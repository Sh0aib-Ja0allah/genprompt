#!/usr/bin/env python3
"""Real-use token check: run a genprompt command with `claude -p`, where @-includes DO expand
(`claude plugin eval` does not expand them; see evals/CP4.md). Used for CP4b.

    python evals/realuse/run.py stage <ref> <name> <workdir>   # plugin copy of <ref>, renamed
    python evals/realuse/run.py fixture <workdir>              # scaffold ledgerlite (base)
    python evals/realuse/run.py case <workdir> <name> <slice|fix> <model> [budget]
    python evals/realuse/run.py analyze <workdir> <name> <case> <model>

Isolation (the real HOME is kept, because sign-in needs it; never copy credentials):
--setting-sources local (no user settings, hooks or user plugins), --strict-mcp-config,
--no-session-persistence, --permission-mode dontAsk (reads only in the fixture and the plugin
copy), deny rules for ~/.genprompt, and Bash, Write, Edit and messaging tools disallowed.
Known gap (CP4b): dontAsk does not stop Glob from LISTING names outside the working dirs; Read is
denied. Keep the fixture outside the home directory if names matter.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tarfile
import io
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
ROOT = EVALS.parent
REQUESTS = {
    "slice": "Slice S-02, scope: CSV export as described in docs/ROADMAP.md (a --csv flag, RFC 4180 "
             "quoting, one row per line item plus a TOTAL row) --go --dry-run",
    "fix": "invoice totals are too low: `npm start -- examples/sample.json` prints TOTAL 40.50 EUR, "
           "but 2x12.50 + 40.00 + 5.00 = 70.00 minus 10% is 63.00 EUR --go --dry-run",
}
DENY = ["Bash", "Write", "Edit", "NotebookEdit", "WebFetch", "WebSearch", "SendMessage",
        "ListAgents", "Artifact", "ArtifactComments", "ArtifactData", "Workflow",
        "PushNotification", "RemoteTrigger", "CronCreate", "CronDelete", "ScheduleWakeup",
        "DesignSync", "EnterWorktree", "ExitWorktree", "ReportFindings",
        "Read(~/.genprompt/**)", "Glob(~/.genprompt/**)", "Grep(~/.genprompt/**)"]
RULES = ("PROTOCOL.md", "/archetypes/", "/guide/", "/stacks/", "/examples/", "/utilities/")
INCLUDE_RE = re.compile(r"^@\$\{CLAUDE_PLUGIN_ROOT\}/(\S+)", re.M)


def stage(ref: str, name: str, work: Path) -> None:
    dest = work / name
    data = subprocess.run(["git", "-C", str(ROOT), "archive", ref], check=True,
                          capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        t.extractall(dest, members=[m for m in t.getmembers()
                                    if not m.name.startswith("evals/")], filter="data")
    pj = dest / ".claude-plugin" / "plugin.json"
    pj.write_text(pj.read_text(encoding="utf-8").replace('"name": "genprompt"',
                                                         f'"name": "{name}"'), encoding="utf-8")
    print(f"staged {ref} as /{name}: at {dest}")


def fixture(work: Path) -> None:
    sys.path.insert(0, str(EVALS))
    from run import find_bash  # noqa: E402  (Git Bash on Windows)
    fx = work / "fixture"
    fx.mkdir(parents=True)
    lib = (EVALS / "fixtures" / "scaffold-lib.sh").as_posix()
    subprocess.run([find_bash(), "-c", f'source "{lib}"; base_repo'], cwd=fx, check=True,
                   env={**__import__("os").environ, "HOME": str(work / "fixture-home")})
    print(f"fixture at {fx}")


def case(work: Path, name: str, which: str, model: str, budget: str) -> None:
    plugin = work / name
    out = work / f"{name}-{which}-{model}.jsonl"
    cmd = [shutil.which("claude"), "-p", "--model", model, "--output-format", "stream-json",
           "--verbose", "--plugin-dir", str(plugin), "--add-dir", str(plugin),
           "--setting-sources", "local", "--strict-mcp-config", "--permission-mode", "dontAsk",
           "--no-session-persistence", "--max-budget-usd", budget, "--disallowedTools", *DENY,
           "--", f"/{name}:{which} {REQUESTS[which]}"]
    with out.open("w", encoding="utf-8") as f:
        p = subprocess.run(cmd, cwd=work / "fixture", stdout=f, stderr=subprocess.PIPE, text=True,
                           encoding="utf-8", errors="replace")
    print(f"{out.name}: exit {p.returncode}")


def include_bytes(plugin: Path, which: str) -> int:
    shim = (plugin / "commands" / f"{which}.md").read_text(encoding="utf-8")
    return len(shim.encode()) + sum((plugin / i).stat().st_size for i in INCLUDE_RE.findall(shim))


def analyze(work: Path, name: str, which: str, model: str) -> dict:
    path = work / f"{name}-{which}-{model}.jsonl"
    first, calls, reads, result = None, {}, [], {}
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
            if b.get("type") == "tool_use" and b.get("name") == "Read":
                p = str(b.get("input", {}).get("file_path", "")).replace("\\", "/")
                if any(k in p for k in RULES) and "/fixture/" not in p:
                    calls[b["id"]] = p.split(f"/{name}/")[-1]
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                c = b.get("content")
                reads.append((calls[b["tool_use_id"]],
                              len((c if isinstance(c, str) else json.dumps(c)).encode())))
        if e.get("type") == "result":
            result = e
    inc = include_bytes(work / name, which)
    rb = sum(n for _, n in reads)
    return {"first_turn_ctx": first, "include_bytes": inc, "rule_reads": reads,
            "rule_read_bytes": rb, "rule_bytes": inc + rb, "cost": result.get("total_cost_usd"),
            "turns": result.get("num_turns"), "usage": result.get("usage", {})}


def main() -> int:
    a = sys.argv[1:]
    if a[0] == "stage":
        stage(a[1], a[2], Path(a[3]))
    elif a[0] == "fixture":
        fixture(Path(a[1]))
    elif a[0] == "case":
        case(Path(a[1]), a[2], a[3], a[4], a[5] if len(a) > 5 else "0.40")
    elif a[0] == "analyze":
        print(json.dumps(analyze(Path(a[1]), a[2], a[3], a[4]), indent=1))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
