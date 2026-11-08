#!/usr/bin/env python3
"""Real-use load probe: measure what a genprompt change does to the rules a generator loads,
with `claude -p`, where @-includes DO expand (`claude plugin eval` does not; see evals/CP4.md).

    python evals/realuse/run.py compare --base <ref> --cand <ref> [--cases slice fix]
                                        [--model haiku] [--budget 0.40] [--min-drop 0.25]
    python evals/realuse/run.py isolation       # tiny probe (< $0.01): proves the home is sealed
    python evals/realuse/run.py report <workdir> --base-name ... (re-analyze a finished compare)

`compare` stages renamed plugin copies of both refs (gp-base, gp-cand), scaffolds the ledgerlite
fixture, runs each case on each copy, and prints the CP4b table plus an acceptance verdict:
  A1 the candidate Reads none of the files its shim @-includes, nor PROTOCOL.md or 03-blocks
  A2 the candidate's first-turn context is larger than the baseline's (the @-includes landed)
  A3 rule bytes (@-included bytes + rule-file Read bytes) are lower in every case
  A4 the median rule-byte drop is at least --min-drop (default 25%)
  A5 isolation: no tool call outside the work dir returned anything but a denial

Isolation. Sign-in needs the real HOME, and credentials are never copied, so the run is sealed by
flags instead:
- the work dir (fixture and plugin copies) lives OUTSIDE the home directory: C:/tmp on Windows,
  the system temp dir elsewhere (refused if that is under the home directory)
- --setting-sources local, --strict-mcp-config and --no-session-persistence
- --permission-mode dontAsk, with only the work dir added via --add-dir
- deny rules that cover Read, Glob and Grep on the whole home directory and on ~/.genprompt,
  so a home-rooted Glob is denied instead of listing names (the CP4b gap)
- Bash, Write, Edit and the messaging and agent tools disallowed
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
ROOT = EVALS.parent
HOME = Path.home()
REQUESTS = {
    "slice": "Slice S-02, scope: CSV export as described in docs/ROADMAP.md (a --csv flag, RFC 4180 "
             "quoting, one row per line item plus a TOTAL row) --go --dry-run",
    "fix": "invoice totals are too low: `npm start -- examples/sample.json` prints TOTAL 40.50 EUR, "
           "but 2x12.50 + 40.00 + 5.00 = 70.00 minus 10% is 63.00 EUR --go --dry-run",
    "redesign": "src/cli.js: split argument parsing, validation and printing into small "
                "functions; keep the CLI's output and exit codes identical --go --dry-run",
    "plan": "S-03 tax lines from docs/ROADMAP.md: a per-line VAT rate and a tax subtotal, totals "
            "still in integer cents --go --dry-run",
}
TOOLS_OFF = ["Bash", "PowerShell", "Write", "Edit", "NotebookEdit", "WebFetch", "WebSearch",
             "SendMessage", "ListAgents", "Artifact", "ArtifactComments", "ArtifactData",
             "Workflow", "PushNotification", "RemoteTrigger", "CronCreate", "CronDelete",
             "ScheduleWakeup", "DesignSync", "EnterWorktree", "ExitWorktree", "ReportFindings",
             "Task", "Agent"]
RULE_HINTS = ("PROTOCOL.md", "/archetypes/", "/guide/", "/stacks/", "/examples/", "/utilities/")
INCLUDE_RE = re.compile(r"^@\$\{CLAUDE_PLUGIN_ROOT\}/(\S+)", re.M)
DENIED_RE = re.compile(r"denied|not allowed|No such tool available", re.I)


def posix_rule_path(p: Path) -> str:
    """A permission-rule path: //c/Users/x on Windows, /home/x elsewhere."""
    s = p.resolve().as_posix()
    if re.match(r"^[A-Za-z]:/", s):
        s = "//" + s[0].lower() + s[2:]
    return s


def deny_rules() -> list[str]:
    rules = list(TOOLS_OFF)
    for tool in ("Read", "Glob", "Grep"):
        rules += [f"{tool}(~/**)", f"{tool}({posix_rule_path(HOME)}/**)",
                  f"{tool}(~/.genprompt/**)"]
    return rules


def default_workroot() -> Path:
    base = Path("C:/tmp") if os.name == "nt" else Path(tempfile.gettempdir())
    try:
        base.resolve().relative_to(HOME.resolve())
        sys.exit(f"{base} is inside the home directory; pass --workroot outside it")
    except ValueError:
        pass
    if not base.exists():
        sys.exit(f"{base} does not exist; create it or pass --workroot")
    return base


def find_bash() -> str:
    git = shutil.which("git")
    if os.name == "nt" and git:
        for cand in (Path(git).parent.parent / "bin" / "bash.exe",
                     Path(git).parent.parent.parent / "bin" / "bash.exe"):
            if cand.exists():
                return str(cand)
    return shutil.which("bash") or "bash"


def stage(ref: str, name: str, work: Path) -> Path:
    dest = work / name
    data = subprocess.run(["git", "-C", str(ROOT), "archive", ref], check=True,
                          capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        t.extractall(dest, members=[m for m in t.getmembers()
                                    if not m.name.startswith("evals/")], filter="data")
    pj = dest / ".claude-plugin" / "plugin.json"
    pj.write_text(re.sub(r'"name":\s*"genprompt"', f'"name": "{name}"',
                         pj.read_text(encoding="utf-8"), count=1), encoding="utf-8")
    return dest


def fixture(work: Path) -> Path:
    fx = work / "fixture"
    fx.mkdir(parents=True)
    lib = (EVALS / "fixtures" / "scaffold-lib.sh").as_posix()
    subprocess.run([find_bash(), "-c", f'source "{lib}"; base_repo'], cwd=fx, check=True,
                   env={**os.environ, "HOME": str(work / "fixture-home")},
                   capture_output=True)
    return fx


def claude_cmd(work: Path, plugin: Path | None, model: str, budget: str, prompt: str) -> list[str]:
    cmd = [shutil.which("claude") or "claude", "-p", "--model", model,
           "--output-format", "stream-json", "--verbose", "--add-dir", str(work),
           "--setting-sources", "local", "--strict-mcp-config", "--permission-mode", "dontAsk",
           "--no-session-persistence", "--max-budget-usd", budget]
    if plugin:
        cmd += ["--plugin-dir", str(plugin)]
    return cmd + ["--disallowedTools", *deny_rules(), "--", prompt]


def run_claude(cmd: list[str], cwd: Path, out: Path) -> int:
    with out.open("w", encoding="utf-8") as f:
        p = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.PIPE, text=True,
                           encoding="utf-8", errors="replace")
    if p.returncode:
        print(f"  {out.name}: exit {p.returncode}: {p.stderr[-300:]}")
    return p.returncode


def includes(plugin: Path, case: str) -> list[str]:
    return INCLUDE_RE.findall((plugin / "commands" / f"{case}.md").read_text(encoding="utf-8"))


def include_bytes(plugin: Path, case: str) -> int:
    shim = plugin / "commands" / f"{case}.md"
    return shim.stat().st_size + sum((plugin / i).stat().st_size for i in includes(plugin, case))


def analyze(path: Path, plugin: Path, work: Path) -> dict:
    first, calls, reads, outside, result = None, {}, [], [], {}
    work_s, plugin_name = work.resolve().as_posix().lower(), plugin.name
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(raw)
        except json.JSONDecodeError:
            continue
        m = e.get("message") if isinstance(e.get("message"), dict) else {}
        if e.get("type") == "assistant" and first is None:
            u = m.get("usage", {})
            first = sum(u.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                              "cache_read_input_tokens"))
        for b in m.get("content", []) if isinstance(m.get("content"), list) else []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                inp = b.get("input", {}) or {}
                p = str(inp.get("file_path") or inp.get("path") or "").replace("\\", "/")
                calls[b["id"]] = (b.get("name"), p)
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                name, p = calls[b["tool_use_id"]]
                c = b.get("content")
                text = c if isinstance(c, str) else json.dumps(c)
                if p and not p.lower().startswith(work_s):
                    outside.append((name, p, "denied" if DENIED_RE.search(text)
                                    else "RETURNED: " + text[:80].replace("\n", " / ")))
                if name == "Read" and f"/{plugin_name}/" in p and any(h in p for h in RULE_HINTS):
                    reads.append((p.split(f"/{plugin_name}/")[-1], len(text.encode())))
        if e.get("type") == "result":
            result = e
    return {"first": first, "reads": reads, "outside": outside, "result": result}


def compare(args) -> int:
    work = (Path(args.workroot) if args.workroot else default_workroot()) / \
        f"genprompt-probe-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    work.mkdir(parents=True)
    base, cand = stage(args.base, "gp-base", work), stage(args.cand, "gp-cand", work)
    fx = fixture(work)
    print(f"work dir {work}\nbase {args.base} -> /gp-base:, cand {args.cand} -> /gp-cand:")
    rows, verdict_reads, outside_bad = [], [], []
    for case in args.cases:
        res = {}
        for plugin in (base, cand):
            out = work / f"{plugin.name}-{case}-{args.model}.jsonl"
            run_claude(claude_cmd(work, plugin, args.model, args.budget,
                                  f"/{plugin.name}:{case} {REQUESTS[case]}"), fx, out)
            a = analyze(out, plugin, work)
            inc = include_bytes(plugin, case)
            a["inc"], a["rule"] = inc, inc + sum(n for _, n in a["reads"])
            res[plugin.name] = a
            outside_bad += [f"{plugin.name}/{case}: {t} {p} {r}" for t, p, r in a["outside"]
                            if not r.startswith("denied")]
        b, c = res["gp-base"], res["gp-cand"]
        forbidden = set(includes(cand, case)) | {"PROTOCOL.md", "guide/03-blocks.md"}
        verdict_reads += [f"{case}: {p}" for p, _ in c["reads"] if p in forbidden]
        rows.append((case, b, c))
    lines = ["| Case | first-turn ctx base → cand | @-included bytes | rule Reads base → cand | "
             "rule bytes base → cand (Δ) | cache write | cache read | output | $ |",
             "|---|---|---|---|---|---|---|---|---|"]
    drops = []
    for case, b, c in rows:
        bu, cu = b["result"].get("usage", {}), c["result"].get("usage", {})
        drop = (b["rule"] - c["rule"]) / b["rule"] if b["rule"] else 0.0
        drops.append(drop)
        names = lambda a: ", ".join(Path(p).name for p, _ in a["reads"]) or "none"  # noqa: E731
        lines.append(
            f"| {case} | {b['first']:,} → {c['first']:,} | {b['inc']:,} → {c['inc']:,} | "
            f"{names(b)} → {names(c)} | {b['rule']:,} → {c['rule']:,} ({-drop:+.1%}) | "
            f"{bu.get('cache_creation_input_tokens', 0):,} → {cu.get('cache_creation_input_tokens', 0):,} | "
            f"{bu.get('cache_read_input_tokens', 0):,} → {cu.get('cache_read_input_tokens', 0):,} | "
            f"{bu.get('output_tokens', 0):,} → {cu.get('output_tokens', 0):,} | "
            f"{b['result'].get('total_cost_usd') or 0:.4f} → {c['result'].get('total_cost_usd') or 0:.4f} |")
    med = statistics.median(drops) if drops else 0.0
    checks = [
        ("A1 no Read of an @-included file, PROTOCOL.md or 03-blocks", not verdict_reads,
         "; ".join(verdict_reads) or "none"),
        ("A2 first-turn context larger in the candidate",
         all(c["first"] > b["first"] for _, b, c in rows), "per case"),
        ("A3 rule bytes lower in every case", all(d > 0 for d in drops),
         ", ".join(f"{-d:+.1%}" for d in drops)),
        (f"A4 median rule-byte drop ≥ {args.min_drop:.0%}", med >= args.min_drop,
         f"median {med:.1%}"),
        ("A5 isolation: nothing outside the work dir returned content", not outside_bad,
         "; ".join(outside_bad) or "every outside call was denied"),
    ]
    cost = sum((a["result"].get("total_cost_usd") or 0) for _, b, c in rows for a in (b, c))
    report = "\n".join(lines) + "\n\n" + "\n".join(
        f"{'PASS' if ok else 'FAIL'}  {n}: {d}" for n, ok, d in checks)
    report += f"\n\nverdict: {'PASS' if all(ok for _, ok, _ in checks) else 'FAIL'} · " \
              f"model {args.model} · total ${cost:.4f}"
    (work / "report.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0 if all(ok for _, ok, _ in checks) else 1


def isolation(args) -> int:
    """Ask a model to Glob from the home root and Read outside the work dir. Each must be denied.
    The sentinel pattern matches nothing real, so even a failure would list no real names."""
    work = (Path(args.workroot) if args.workroot else default_workroot()) / \
        f"genprompt-isolation-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    work.mkdir(parents=True)
    (work / "inside.txt").write_text("inside the work dir\n", encoding="utf-8")
    home = HOME.as_posix()
    prompt = (f"Make exactly these four tool calls, one at a time, then reply DONE: "
              f"(1) Glob with path \"{home}\" and pattern \"**/genprompt-isolation-sentinel-*\". "
              f"(2) Glob with path \"{home}/.genprompt\" and pattern \"*\". "
              f"(3) Grep with path \"{home}\" and pattern \"genprompt-isolation-sentinel\". "
              f"(4) Read the file \"{(work / 'inside.txt').as_posix()}\".")
    out = work / "isolation.jsonl"
    run_claude(claude_cmd(work, None, "haiku", "0.02", prompt), work, out)
    calls, rows = {}, []
    for raw in out.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(raw)
        except json.JSONDecodeError:
            continue
        m = e.get("message") if isinstance(e.get("message"), dict) else {}
        for b in m.get("content", []) if isinstance(m.get("content"), list) else []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                calls[b["id"]] = (b.get("name"), json.dumps(b.get("input"))[:120])
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                c = b.get("content")
                rows.append((*calls[b["tool_use_id"]],
                             (c if isinstance(c, str) else json.dumps(c))[:100]))
        if e.get("type") == "result":
            rows.append(("result", "", f"cost ${e.get('total_cost_usd')}"))
    ok_home = [r for r in rows if r[0] in ("Glob", "Grep")]
    ok_inside = [r for r in rows if r[0] == "Read"]
    # All three home calls must have been made (a skipped Grep proves nothing) and denied.
    made = {r[0] for r in ok_home}
    sealed = len(ok_home) >= 3 and made == {"Glob", "Grep"} and \
        all(DENIED_RE.search(r[2]) for r in ok_home)
    inside = bool(ok_inside) and "inside the work dir" in ok_inside[0][2]
    for r in rows:
        print(" | ".join(x.replace("\n", " / ") for x in r))
    print(f"\nhome sealed (every home Glob/Grep denied): {'PASS' if sealed else 'FAIL'}")
    print(f"work dir readable: {'PASS' if inside else 'FAIL'}")
    return 0 if sealed and inside else 1


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--base", required=True)
    c.add_argument("--cand", required=True)
    c.add_argument("--cases", nargs="+", default=["slice", "fix"], choices=sorted(REQUESTS))
    c.add_argument("--model", default="haiku")
    c.add_argument("--budget", default="0.40", help="max $ per claude -p run")
    c.add_argument("--min-drop", type=float, default=0.25)
    c.add_argument("--workroot")
    i = sub.add_parser("isolation")
    i.add_argument("--workroot")
    args = ap.parse_args()
    return compare(args) if args.cmd == "compare" else isolation(args)


if __name__ == "__main__":
    sys.exit(main())
