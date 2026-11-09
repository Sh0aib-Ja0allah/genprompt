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
- the work dir (fixture and plugin copies) lives under a root only this probe uses:
  C:/genprompt-probe on Windows, /var/tmp/genprompt-probe elsewhere (refused if that is under
  the home directory or a shared scratch root)
- Read, Glob and Grep are also denied on the shared roots C:/tmp and C:/Users (/tmp elsewhere),
  so a recursive Glob cannot list other projects (CP5); A5 accepts "does not exist" answers to
  the protocol's ancestor scan
- --setting-sources local, --strict-mcp-config and --no-session-persistence
- --permission-mode dontAsk, with only the work dir added via --add-dir
- deny rules that cover Read, Glob and Grep on the whole home directory and on ~/.genprompt,
  so a home-rooted Glob is denied instead of listing names (the CP4b gap)
- Bash, Write, Edit and the messaging and agent tools disallowed

--home empty|card (CP6a): each run gets a fresh sandbox GENPROMPT_HOME under the work dir (seeded
with a fresh profile card for `card`). Write/Edit are allowed only there, Bash is narrowed to a
read-only git subset plus the candidate's archive.py, and bases never run archive.py. Several
--base refs can be compared in one run; --a4 report keeps A4 out of the verdict.
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
# The protocol's ancestor scan checks CLAUDE.md / AGENTS.md in every parent directory. A
# "does not exist" answer reveals nothing, so A5 accepts it (CP5). A Glob from the drive root
# that times out returns no names either (CP5b), so that is accepted too.
HARMLESS_RE = re.compile(r"denied|not allowed|No such tool available|does not exist|"
                         r"search timed out|blocked by a deny rule", re.I)
# A Bash `python3` that hit the Windows store alias ran nothing (CP6a).
STORE_ALIAS_RE = re.compile(r"Python was not found", re.I)
# An empty Glob/Grep from the drive root returns exactly "No files found" (CP5c). It must be the
# whole result, so a reply that also lists names is still flagged.
EMPTY_RE = re.compile(r"\s*No (?:files|matches) found\s*", re.I)


def harmless(text: str) -> bool:
    """True when an outside call's result reveals nothing (A5)."""
    return bool(HARMLESS_RE.search(text) or EMPTY_RE.fullmatch(text))


# A Glob/Grep from the drive root is judged by the names it returns, not by its path: with the
# drive-root denials in place it lists only files under the probe root (CP6a-2 flagged two such
# calls by path). It is not screened with harmless() first: a listed name containing "denied"
# would then hide the whole result.
DRIVE_ROOT_RE = re.compile(r"(?:[A-Za-z]:|/[A-Za-z])?/?")


def is_drive_root(p: str) -> bool:
    """True for a drive root path: `C:`, `C:/`, `C:\\`, `/c`, `/`."""
    return bool(p) and bool(DRIVE_ROOT_RE.fullmatch(p.replace("\\", "/")))


def result_text(c) -> str:
    """A tool result's text: the string itself, or the text blocks of a content list joined."""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(str(b.get("text", "")) if isinstance(b, dict) else str(b) for b in c)
    return json.dumps(c)


def names_outside(text: str, probe: str) -> list[str]:
    """Lines of a drive-root Glob/Grep result that name something outside the probe root.
    A line that starts with an absolute path (`C:/...`, `/c/...`, `/...`) must start with the
    probe root. Glob and Grep print a name relative only when it is under the run's cwd, which
    is inside the probe root, so any other line passes unless it climbs out with `..`. Messages
    ("No files found", a timeout, a denial, Grep's "Found N files") are such lines."""
    probe = probe.replace("\\", "/").rstrip("/").lower() + "/"
    bad = []
    for ln in text.splitlines():
        s = ln.strip().replace("\\", "/")
        if not s:
            continue
        low = re.sub(r"^/([a-z])/", r"\1:/", s.lower())
        if re.match(r"[a-z]:/|/", low):
            if not low.startswith(probe):
                bad.append(ln.strip())
        elif ".." in low.split("/"):
            bad.append(ln.strip())
    return bad


# Shared scratch roots that hold other projects: Read, Glob and Grep are denied there so a
# recursive Glob cannot list another project's files (CP5 A5).
SHARED_ROOTS = [Path("C:/tmp"), Path("C:/Users")] if os.name == "nt" else [Path("/tmp")]


# --home empty|card (CP6a, E-21/E-09e): Step 0 runs `archive.py --where` (Bash) and the generator may
# Write/Edit its home, so each run gets a fresh sandbox home under the work dir via GENPROMPT_HOME,
# and only that is opened: Write/Edit on the sandbox homes, a read-only git subset, `date`, and the
# candidate's archive.py. Every ref gets the same git subset. A base never runs archive.py: older
# refs ignore GENPROMPT_HOME and would touch the real ~/.genprompt.
HOME_TOOLS_OFF = [t for t in TOOLS_OFF if t not in ("Bash", "Write", "Edit")]
BASH_OFF = ["cd", "ls", "head", "tail", "wc", "cat", "git diff", "git grep", "git config",
            # read-only builtins Claude Code allows even under dontAsk (CP6a: `echo $HOME` and
            # `test -f ~/.genprompt/...` showed the home path and that real paths exist)
            "echo", "printf", "test", "[", "pwd", "env", "printenv"]
BASE_BASH_OFF = ["python", "python3", "py"]
SAFE_BASH_RE = re.compile(
    r"\s*(?:git (?:status|log|show|rev-parse|ls-files|rev-list|shortlog|cat-file -p|branch|"
    r"remote|symbolic-ref|stash list|worktree list)\b|date\b|"
    # only the candidate's archive.py, and only --where or a --dry-run (CP6a)
    r"python3? \"?\S*/gp-cand/tools/archive\.py\"? (?:--where\s*$|.*--dry-run\b))")


def safe_bash(cmd: str) -> bool:
    """A5: every part of a command that ran is a safe one. `2>&1` is allowed, and so are parts
    joined by && / || (the `python3 … || python …` fallback); any other shell syntax is not."""
    parts = re.split(r"&&|\|\|", re.sub(r"\s*2>&1", "", cmd))
    return all(SAFE_BASH_RE.match(x) and not re.search(r"[;&|`<>]|\$\(", x) for x in parts)


def posix_rule_path(p: Path) -> str:
    """A permission-rule path: //c/Users/x on Windows, /home/x elsewhere."""
    s = p.resolve().as_posix()
    if re.match(r"^[A-Za-z]:/", s):
        s = "//" + s[0].lower() + s[2:]
    return s


def drive_root_dirs(root: Path) -> list[Path]:
    """Every top-level folder on the probe root's drive except the one holding the probe root.
    A Glob from the drive root filters its results by Read/Glob deny rules, so denying these
    leaves it nothing outside the probe (CP6a: a v1.2.0 plan run's `Glob *.md` from C:/ listed
    100 names under Program Files, Windows and a local web stack)."""
    root = root.resolve()
    anchor = Path(root.anchor)
    if root == anchor:
        return []
    keep = anchor / root.relative_to(anchor).parts[0]
    try:
        return sorted(d for d in anchor.iterdir() if d.is_dir() and d != keep)
    except OSError:
        return []


def deny_rules(work: Path | None = None, base: bool = False,
               root: Path | None = None) -> list[str]:
    """Deny rules. With `work` (home mode) Bash, Write and Edit are narrowed instead of off.
    With `root` (the probe root), every other top-level folder of its drive is denied too."""
    rules = list(HOME_TOOLS_OFF if work else TOOLS_OFF)
    for tool in ("Read", "Glob", "Grep"):
        rules += [f"{tool}(~/**)", f"{tool}({posix_rule_path(HOME)}/**)",
                  f"{tool}(~/.genprompt/**)"]
        rules += [f"{tool}({posix_rule_path(r)}/**)" for r in SHARED_ROOTS]
        # "(" and ")" would end the rule early ("Program Files (x86)"), so they become "?"
        rules += [f"{tool}({re.sub(r'[()]', '?', posix_rule_path(d))}/**)"
                  for d in (drive_root_dirs(root) if root else [])]
    if work:
        rules += [f"Bash({c}:*)" for c in BASH_OFF + (BASE_BASH_OFF if base else [])]
        w = posix_rule_path(work)
        for tool in ("Write", "Edit"):
            rules += [f"{tool}(~/**)", f"{tool}({posix_rule_path(HOME)}/**)",
                      f"{tool}({w}/fixture/**)", f"{tool}({w}/gp-*/**)"]
            rules += [f"{tool}({posix_rule_path(r)}/**)" for r in SHARED_ROOTS]
    return rules


def seed_card(home: Path, fx: Path) -> Path:
    """A fresh profile card for the ledgerlite fixture (PROTOCOL Step 2, derive.md §2.9). Stamps
    are the fixture's real `git log -1 --format=%h` for the manifest and the contract."""
    def sha(f: str) -> str:
        return subprocess.run(["git", "-C", str(fx), "log", "-1", "--format=%h", "--", f],
                              check=True, capture_output=True, text=True).stdout.strip()
    key = fx.name.lower().replace("_", "-").replace(" ", "-")
    card = home / "generated-prompts" / "by-repo" / f"{key}.profile.md"
    card.parent.mkdir(parents=True, exist_ok=True)
    card.write_text(f"""---
repo:     {fx.name}
path:     {fx.resolve().as_posix()}
key:      {key}
derived:  {dt.date.today().isoformat()}
stamp:    package.json@{sha('package.json')} ; CLAUDE.md@{sha('CLAUDE.md')}
---
branch:          main
default_branch:  main (inferred: yes, no remote)
scope:       single root
stack:       Node.js >=18 (CommonJS), no framework, no runtime dependencies
role:        senior node engineer
contract:    CLAUDE.md · hard rules: never commit to main (feat/<slug> or fix/<slug>) · Conventional Commits · stage by explicit path, never git add -A/. · never push or open a PR without the maintainer's OK · npm test and npm run lint green before every commit · no build step, no type checker · money is integer cents · no runtime dependencies in src/
ancestors:   none found · user-level: ~/.claude/CLAUDE.md
truth:       CLAUDE.md (binding) > docs/ROADMAP.md (slices S-01..; newest commit wins) > README.md (may lag the roadmap)
docnaming:   docs/<TOPIC>.md in upper-case kebab (CLAUDE.md), next e.g. docs/CSV-EXPORT.md
code_roots:  src/ test/ scripts/
forbidden:   EXCLUDE list, node_modules/
blockers:    none stated
gates:       NOT CACHED: always re-derived at runtime (§2.5); <PROFILE.gates> means the derived list
""", encoding="utf-8")
    return card


def default_workroot() -> Path:
    """A root used only by this probe, so a recursive Glob from the work dir's parent finds
    nothing but probe runs: C:/genprompt-probe on Windows, /var/tmp/genprompt-probe elsewhere.
    It must not sit inside the home directory or a shared scratch root (both are denied)."""
    base = Path("C:/genprompt-probe") if os.name == "nt" else Path("/var/tmp/genprompt-probe")
    for forbidden in [HOME, *SHARED_ROOTS]:
        try:
            base.resolve().relative_to(forbidden.resolve())
            sys.exit(f"{base} is inside {forbidden}, which the probe denies; pass --workroot")
        except ValueError:
            pass
    base.mkdir(parents=True, exist_ok=True)
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


def claude_cmd(work: Path, plugin: Path | None, model: str, budget: str, prompt: str,
               homes: Path | None = None, base: bool = False) -> list[str]:
    """`homes`: home mode; Write/Edit are allowed only under that folder of sandbox homes."""
    cmd = [shutil.which("claude") or "claude", "-p", "--model", model,
           "--output-format", "stream-json", "--verbose", "--add-dir", str(work),
           "--setting-sources", "local", "--strict-mcp-config", "--permission-mode", "dontAsk",
           "--no-session-persistence", "--max-budget-usd", budget]
    if plugin:
        cmd += ["--plugin-dir", str(plugin)]
    if homes:
        h = posix_rule_path(homes)
        cmd += ["--allowedTools", f"Write({h}/**)", f"Edit({h}/**)"]
    return cmd + ["--disallowedTools", *deny_rules(work if homes else None, base, work.parent),
                  "--", prompt]


def run_claude(cmd: list[str], cwd: Path, out: Path, env: dict | None = None) -> int:
    with out.open("w", encoding="utf-8") as f:
        p = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.PIPE, text=True,
                           encoding="utf-8", errors="replace",
                           env={**os.environ, **env} if env else None)
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
    bash, writes = [], []
    # "Inside" is the probe's own root (every run dir under it is ours), so the ancestor scan
    # listing a sibling run's fixture CLAUDE.md is not a leak (CP5b).
    work_s, plugin_name = work.resolve().parent.as_posix().lower(), plugin.name
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
                if b.get("name") == "Bash":
                    p = str(inp.get("command") or "")
                calls[b["id"]] = (b.get("name"), p)
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                name, p = calls[b["tool_use_id"]]
                c = b.get("content")
                text = c if isinstance(c, str) else json.dumps(c)
                if name == "Bash":
                    # A5: a Bash call that ran must be a read-only git subset command, `date` or
                    # the candidate's `archive.py --where`, with nothing chained on.
                    ran = not (harmless(text) or STORE_ALIAS_RE.search(text))
                    ok = not ran or safe_bash(p)
                    bash.append((p, text[:80].replace("\n", " / "), bool(ok)))
                    if not ok:
                        outside.append((name, p, "RETURNED: " + text[:80].replace("\n", " / ")))
                    continue
                if name in ("Write", "Edit"):
                    # A write that went through must land in a sandbox home (work/homes/...).
                    landed = not harmless(text)
                    in_home = p.lower().startswith(work.resolve().as_posix().lower() + "/homes/")
                    writes.append((name, p, text[:60].replace("\n", " / ")))
                    if landed and not in_home:
                        outside.append((name, p, "WROTE: " + text[:80].replace("\n", " / ")))
                        continue
                if name in ("Glob", "Grep") and is_drive_root(p):
                    # Judged by the names returned (CP6a-2 false alarm), not by the path.
                    bad = names_outside(result_text(c), work_s)
                    if bad:
                        outside.append((name, p, "RETURNED: " + " / ".join(bad[:3])[:80]))
                    continue
                if p and not p.lower().startswith(work_s):
                    outside.append((name, p, "denied" if harmless(text)
                                    else "RETURNED: " + text[:80].replace("\n", " / ")))
                if name == "Read" and f"/{plugin_name}/" in p and any(h in p for h in RULE_HINTS):
                    reads.append((p.split(f"/{plugin_name}/")[-1], len(text.encode())))
        if e.get("type") == "result":
            result = e
    return {"first": first, "reads": reads, "outside": outside, "result": result,
            "bash": bash, "writes": writes}


def compare(args) -> int:
    work = (Path(args.workroot) if args.workroot else default_workroot()) / \
        f"genprompt-probe-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    work.mkdir(parents=True)
    names = ["gp-base"] if len(args.base) == 1 else [f"gp-b-{r[:7]}" for r in args.base]
    bases = [stage(r, n, work) for r, n in zip(args.base, names)]
    ref_of = {n: r for n, r in zip(names, args.base)} | {"gp-cand": args.cand}
    cand = stage(args.cand, "gp-cand", work)
    fx = fixture(work)
    homes = work / "homes" if args.home != "none" else None
    print(f"work dir {work}\n" + "".join(f"base {r} -> /{n}:, " for n, r in zip(names, args.base))
          + f"cand {args.cand} -> /gp-cand: · {args.runs} run(s) per cell · home {args.home}")
    # runs[case][plugin] = list of analyses, one per run (each run is a fresh claude -p session)
    runs: dict[str, dict[str, list[dict]]] = {}
    verdict_reads, outside_bad, bash_log, write_log = [], [], [], []
    for case in args.cases:
        runs[case] = {}
        for plugin in (*bases, cand):
            runs[case][plugin.name] = []
            for i in range(1, args.runs + 1):
                # Spend guard: never start a run that could push the total past --max-total.
                spent = sum(a["result"].get("total_cost_usd") or 0
                            for cr in runs.values() for rs in cr.values() for a in rs)
                if args.max_total is not None and spent + float(args.budget) > args.max_total:
                    sys.exit(f"STOP: ${spent:.4f} spent; another run (cap ${args.budget}) could pass "
                             f"--max-total ${args.max_total}. Partial traces are in {work}")
                suffix = "" if args.runs == 1 else f"-r{i}"
                out = work / f"{plugin.name}-{case}-{args.model}{suffix}.jsonl"
                env = None
                if homes:
                    # A fresh sandbox home per run, so one run's writes never reach the next.
                    home = homes / f"{plugin.name}-{case}-r{i}"
                    home.mkdir(parents=True)
                    if args.home == "card":
                        seed_card(home, fx)
                    env = {"GENPROMPT_HOME": home.resolve().as_posix()}
                run_claude(claude_cmd(work, plugin, args.model, args.budget,
                                      f"/{plugin.name}:{case} {REQUESTS[case]}", homes,
                                      plugin is not cand), fx, out, env)
                a = analyze(out, plugin, work)
                inc = include_bytes(plugin, case)
                a["inc"], a["rule"] = inc, inc + sum(n for _, n in a["reads"])
                runs[case][plugin.name].append(a)
                tag = f"{plugin.name}/{case}/r{i}"
                outside_bad += [f"{tag}: {t} {p} {r}" for t, p, r in a["outside"]
                                if not r.startswith("denied")]
                bash_log += [f"{tag}: {'ok' if ok else 'FLAG'} `{c[:90]}` → {t[:60]}"
                             for c, t, ok in a["bash"]]
                write_log += [f"{tag}: {n} {p} → {t}" for n, p, t in a["writes"]]
        forbidden = set(includes(cand, case)) | {"PROTOCOL.md", "guide/03-blocks.md"}
        verdict_reads += [f"{case}: {p}" for a in runs[case]["gp-cand"]
                          for p, _ in a["reads"] if p in forbidden]

    med = statistics.median
    cost = lambda rs: sum(a["result"].get("total_cost_usd") or 0 for a in rs)  # noqa: E731
    u = lambda rs, k: med([a["result"].get("usage", {}).get(k, 0) or 0 for a in rs])  # noqa: E731

    def files(rs):
        seen: dict[str, int] = {}
        for a in rs:
            for p in {Path(p).name for p, _ in a["reads"]}:
                seen[p] = seen.get(p, 0) + 1
        return ", ".join(f"{p}×{n}" for p, n in sorted(seen.items())) or "none"

    def per_run(rs):
        return " ".join(f"{a['rule']:,}" for a in rs)

    sections, checks = [], []
    c_med = {case: med([a["rule"] for a in runs[case]["gp-cand"]]) for case in args.cases}
    sections.append("Candidate gp-cand (" + args.cand + f", home {args.home})\n\n"
                    "| Case | first-turn ctx (median) | @-included bytes | rule Reads (files × runs) | "
                    "rule bytes (median) | per-run rule bytes | $ (sum) |\n|---|---|---|---|---|---|---|\n"
                    + "\n".join(
                        f"| {case} | {med([a['first'] or 0 for a in rs]):,.0f} | {rs[0]['inc']:,} | "
                        f"{files(rs)} | {c_med[case]:,.0f} | {per_run(rs)} | {cost(rs):.4f} |"
                        for case in args.cases for rs in [runs[case]["gp-cand"]]))
    a2_ok, a3_ok, a3_det, a4_ok, a4_det = True, True, [], True, []
    for b in bases:
        lines = [f"Base {b.name} ({ref_of[b.name]}) → candidate", "",
                 "| Case | first-turn ctx base → cand (median) | @-included bytes | rule Reads base → "
                 "cand (files × runs) | rule bytes base → cand (median, Δ) | per-run rule bytes base / "
                 "cand | cache write (median) | cache read (median) | $ (sum) |",
                 "|---|---|---|---|---|---|---|---|---|"]
        case_drops, run_drops = [], []
        for case in args.cases:
            b_runs, c_runs = runs[case][b.name], runs[case]["gp-cand"]
            bm, cm = med([a["rule"] for a in b_runs]), c_med[case]
            drop = (bm - cm) / bm if bm else 0.0
            case_drops.append(drop)
            run_drops += [(x["rule"] - y["rule"]) / x["rule"] for x in b_runs for y in c_runs
                          if x["rule"]]
            bf, cf = med([a["first"] or 0 for a in b_runs]), med([a["first"] or 0 for a in c_runs])
            a2_ok &= cf > bf
            a3_ok &= cm <= bm
            lines.append(
                f"| {case} | {bf:,.0f} → {cf:,.0f} | {b_runs[0]['inc']:,} → {c_runs[0]['inc']:,} | "
                f"{files(b_runs)} → {files(c_runs)} | {bm:,.0f} → {cm:,.0f} ({-drop:+.1%}) | "
                f"{per_run(b_runs)} / {per_run(c_runs)} | "
                f"{u(b_runs, 'cache_creation_input_tokens'):,.0f} → {u(c_runs, 'cache_creation_input_tokens'):,.0f} | "
                f"{u(b_runs, 'cache_read_input_tokens'):,.0f} → {u(c_runs, 'cache_read_input_tokens'):,.0f} | "
                f"{cost(b_runs):.4f} → {cost(c_runs):.4f} |")
        sections.append("\n".join(lines))
        all_med = med(run_drops) if run_drops else 0.0
        a3_det.append(f"vs {ref_of[b.name]}: " + ", ".join(
            f"{c} {-d:+.1%}" for c, d in zip(args.cases, case_drops)))
        a4_ok &= all_med >= args.min_drop
        a4_det.append(f"vs {ref_of[b.name]}: all-runs median drop {all_med:.1%} over "
                      f"{len(run_drops)} pairs; median of per-case medians {med(case_drops):.1%}")
    checks.append(("A1 no Read of an @-included file, PROTOCOL.md or 03-blocks", not verdict_reads,
                   "; ".join(verdict_reads) or "none"))
    if bases:
        checks += [
            ("A2 first-turn context larger in the candidate (median per case, every base)", a2_ok,
             "per case"),
            ("A3 candidate median rule bytes ≤ every base's, in every case", a3_ok,
             " · ".join(a3_det)),
        ]
        if args.a4 == "gate":
            checks.append((f"A4 median rule-byte drop across all runs ≥ {args.min_drop:.0%}", a4_ok,
                           " · ".join(a4_det)))
        else:
            sections.append("A4 (reported, not gated): " + " · ".join(a4_det))
    checks.append(("A5 isolation: nothing outside the probe root returned content, no unsafe "
                   "Bash ran, no write outside the sandbox homes", not outside_bad,
                   "; ".join(outside_bad[:6]) or "every outside call was denied or harmless"))
    if homes:
        sections.append("Bash calls:\n" + ("\n".join(f"- {x}" for x in bash_log) or "- none"))
        sections.append("Write/Edit calls:\n" + ("\n".join(f"- {x}" for x in write_log) or "- none"))
    total = sum(a["result"].get("total_cost_usd") or 0
                for case in runs.values() for rs in case.values() for a in rs)
    report = "\n\n".join(sections) + "\n\n" + "\n".join(
        f"{'PASS' if ok else 'FAIL'}  {n}: {d}" for n, ok, d in checks)
    report += f"\n\nverdict: {'PASS' if all(ok for _, ok, _ in checks) else 'FAIL'} · " \
              f"model {args.model} · {args.runs} run(s) per cell · home {args.home} · " \
              f"total ${total:.4f}"
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
    home, shared = HOME.as_posix(), SHARED_ROOTS[0].as_posix()
    drive = Path(work.resolve().anchor).as_posix()
    prompt = (f"Make exactly these seven tool calls, one at a time, then reply DONE: "
              f"(1) Glob with path \"{home}\" and pattern \"**/genprompt-isolation-sentinel-*\". "
              f"(2) Glob with path \"{home}/.genprompt\" and pattern \"*\". "
              f"(3) Grep with path \"{home}\" and pattern \"genprompt-isolation-sentinel\". "
              f"(4) Glob with path \"{shared}\" and pattern \"**/genprompt-isolation-sentinel-*\". "
              f"(5) Grep with path \"{shared}\" and pattern \"genprompt-isolation-sentinel\". "
              f"(6) Read the file \"{(work / 'inside.txt').as_posix()}\". "
              f"(7) Glob with path \"{drive}\" and pattern \"**/*.md\".")
    out = work / "isolation.jsonl"
    cmd = claude_cmd(work, None, "haiku", "0.02", prompt)
    # Grant Read/Glob/Grep everywhere, as every genprompt shim's allowed-tools does, so only the
    # deny rules seal the run. Without this, dontAsk refuses any path outside the work dir and
    # the check proves nothing (CP6a-2: the first drive-root check passed only for that reason).
    k = cmd.index("--disallowedTools")
    cmd[k:k] = ["--allowedTools", "Read", "Glob", "Grep"]
    run_claude(cmd, work, out)
    calls, rows, root_txt, ok_home = {}, [], [], []
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
                inp = b.get("input") or {}
                at_root = str(inp.get("path") or "").replace("\\", "/").rstrip("/") == \
                    drive.rstrip("/")
                calls[b["id"]] = (b.get("name"), json.dumps(inp)[:120], at_root)
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                c = b.get("content")
                full = c if isinstance(c, str) else json.dumps(c)
                name, desc, at_root = calls[b["tool_use_id"]]
                rows.append((name, desc, full[:100]))
                if at_root:
                    root_txt.append(full)
                elif name in ("Glob", "Grep"):
                    ok_home.append(rows[-1])
        if e.get("type") == "result":
            rows.append(("result", "", f"cost ${e.get('total_cost_usd')}"))
    ok_inside = [r for r in rows if r[0] == "Read"]
    # All three home calls must have been made (a skipped Grep proves nothing) and denied.
    made = {r[0] for r in ok_home}
    sealed = len(ok_home) >= 5 and made == {"Glob", "Grep"} and \
        all(DENIED_RE.search(r[2]) for r in ok_home)
    inside = bool(ok_inside) and "inside the work dir" in ok_inside[0][2]
    # (7) A drive-root Glob may only return names under the probe root (CP6a).
    probe = work.resolve().parent.as_posix().lower()
    leaked = [ln for t in root_txt for ln in names_outside(t, probe)]
    root_ok = bool(root_txt) and not leaked
    for r in rows:
        print(" | ".join(x.replace("\n", " / ") for x in r))
    print(f"\nhome and shared roots sealed (all 5 Glob/Grep denied): {'PASS' if sealed else 'FAIL'}")
    print(f"work dir readable: {'PASS' if inside else 'FAIL'}")
    print(f"drive-root Glob returns nothing outside the probe root: "
          f"{'PASS' if root_ok else 'FAIL'} ({len(leaked)} outside name(s))")
    return 0 if sealed and inside and root_ok else 1


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--base", nargs="*", default=[], help="one or more baseline refs; none = report the candidate only")
    c.add_argument("--cand", required=True)
    c.add_argument("--cases", nargs="+", default=["slice", "fix"], choices=sorted(REQUESTS))
    c.add_argument("--model", default="haiku")
    c.add_argument("--budget", default="0.40", help="max $ per claude -p run")
    c.add_argument("--min-drop", type=float, default=0.25)
    c.add_argument("--runs", type=int, default=1, help="fresh runs per case per ref (gate on the median)")
    c.add_argument("--home", choices=["none", "empty", "card"], default="none",
                   help="GENPROMPT_HOME per run: none (unset, Bash off), empty sandbox home, or a sandbox home seeded with a fresh profile card")
    c.add_argument("--a4", choices=["gate", "report"], default="gate")
    c.add_argument("--max-total", type=float, help="stop before a run could push total $ past this")
    c.add_argument("--workroot")
    i = sub.add_parser("isolation")
    i.add_argument("--workroot")
    args = ap.parse_args()
    return compare(args) if args.cmd == "compare" else isolation(args)


if __name__ == "__main__":
    sys.exit(main())
