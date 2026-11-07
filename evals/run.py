#!/usr/bin/env python3
"""Run genprompt's eval cases, then apply the deterministic graders `claude plugin eval` cannot.

    python evals/run.py --case slice            # one case, one run (the smoke run)
    python evals/run.py                         # every baseline case
    python evals/run.py --controls              # the negative control: every grader must FAIL
    python evals/run.py --validate              # load and check the suite, no model spend
    python evals/run.py --print-shas            # the fixture's deterministic commit SHAs

Results go to evals/results/<timestamp>/ (gitignored): aggregate.json from the eval CLI, and
structural.json + summary.txt from this script (not .md: doctor scans every .md in the repo, and a run quotes temp paths), plus each run's trace and final message. The eval's
temp dirs are kept only long enough to read them, then removed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EVALS = Path(__file__).resolve().parent
ROOT = EVALS.parent
sys.path.insert(0, str(EVALS))
sys.path.insert(0, str(EVALS / "lint"))

import build_cases  # noqa: E402
import structural  # noqa: E402


def claude() -> str:
    exe = shutil.which("claude")
    if not exe:
        sys.exit("claude CLI not found on PATH")
    return exe


def eval_cmd(args, out: Path, tag: str) -> list[str]:
    cmd = [claude(), "plugin", "eval", str(ROOT), "--tag", tag, "--ablation", "none",
           "--scaffold", "--no-publish", "--trust-plugin", "--runs", str(args.runs),
           "--threshold", "0", "--json", str(out / "aggregate.json"), "--output-dir", str(out)]
    if not args.validate:
        cmd.append("--keep-temp")
    if args.case:
        cmd += ["--case", args.case]
    if args.model:
        cmd += ["--model", args.model]
    if args.max_cost_usd is not None:
        cmd += ["--max-cost-usd", str(args.max_cost_usd)]
    if tag == "control":
        cmd += ["--allow-tools", "Write"]  # so the control's write attempt shows no-write failing
    return cmd


def read_trace(path: Path) -> dict:
    final, tools, model, result = "", [], None, {}
    last_text: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            model = ev.get("model")
        if ev.get("type") == "assistant":
            texts = []
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tools.append(block.get("name"))
                elif block.get("type") == "text":
                    texts.append(block.get("text", ""))
            if texts:
                last_text = texts
        if "total_cost_usd" in ev or ev.get("type") == "result":
            result = ev
    final = result.get("result") if isinstance(result.get("result"), str) else "\n".join(last_text)
    usage = result.get("usage", {})
    return {"final": final, "tools": tools, "model": model,
            "cost_usd": result.get("total_cost_usd"), "turns": result.get("num_turns"),
            "usage": {k: usage.get(k) for k in ("input_tokens", "cache_creation_input_tokens",
                                                "cache_read_input_tokens", "output_tokens")},
            "model_usage": result.get("modelUsage")}


def workspace_files(ws: Path) -> dict[str, int]:
    files = {}
    for p in ws.rglob("*"):
        if p.is_file() and ".git" not in p.relative_to(ws).parts:
            try:
                files[p.relative_to(ws).as_posix()] = len(
                    p.read_text(encoding="utf-8").splitlines())
            except (UnicodeDecodeError, OSError):
                files[p.relative_to(ws).as_posix()] = 0
    return files


def post_grade(agg: dict, out: Path, keep: bool) -> list[dict]:
    rows = []
    for case in agg.get("cases", []):
        name = case["name"]
        spec = build_cases.SPEC.get(name) or build_cases.SPEC["slice"]
        control = name.startswith("control-")
        for i, run in enumerate(case.get("arms", {}).get("with", [])):
            row = {"case": name, "run": i + 1, "control": control,
                   "eval_score": run.get("score"), "eval_cost_usd": run.get("costUsd"),
                   "judge_cost_usd": run.get("judgeCostUsd"), "error": run.get("error"),
                   "eval_graders": [{"name": g["name"], "passed": g["passed"],
                                     "explanation": g.get("explanation")}
                                    for g in run.get("graders", [])]}
            trace = Path(run["tracePath"]) if run.get("tracePath") else None
            if trace and trace.exists():
                tmp = trace.parent.parent
                home, ws = tmp / "home", tmp / "home" / "cwd"
                t = read_trace(trace)
                pkg = ws / "package.json"
                scripts = set(json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})) \
                    if pkg.exists() else None
                res = structural.grade(t["final"], cap=spec["cap"], cap_multi=spec.get("cap_multi"),
                                       scripts=scripts, files=workspace_files(ws),
                                       tool_uses=t["tools"], home=home)
                row.update({k: t[k] for k in ("model", "cost_usd", "turns", "usage",
                                              "model_usage")})
                row["structural"] = [r.as_dict() for r in res]
                dest = out / name / f"run{i + 1}"
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(trace, dest / "trace.jsonl")
                (dest / "final.txt").write_text(t["final"], encoding="utf-8")
                if not keep:
                    shutil.rmtree(tmp, ignore_errors=True)
            else:
                row["structural"] = [structural.Result(
                    "all", structural.SKIPPED, "no trace (run errored or temp not kept)").as_dict()]
            rows.append(row)
    return rows


def summary(rows: list[dict], agg: dict) -> str:
    out = [f"claude {agg.get('claudeVersion')} · eval cost ${agg.get('costUsd', 0):.4f} · "
           f"{agg.get('durationSeconds')}s", ""]
    for r in rows:
        tag = " (negative control: every grader should FAIL)" if r["control"] else ""
        out.append(f"## {r['case']} run {r['run']}{tag}")
        out.append(f"model {r.get('model')} · eval score {r['eval_score']} · cost "
                   f"${(r.get('eval_cost_usd') or 0):.4f} (judge ${(r.get('judge_cost_usd') or 0):.4f})"
                   f" · turns {r.get('turns')} · usage {r.get('usage')}")
        if r.get("error"):
            out.append(f"ERROR: {r['error']}")
        out.append("| grader | kind | result | detail |\n|---|---|---|---|")
        for g in r["eval_graders"]:
            out.append(f"| {g['name']} | eval | {'PASS' if g['passed'] else 'FAIL'} | "
                       f"{(g.get('explanation') or '').replace('|', '/')[:140]} |")
        for g in r["structural"]:
            out.append(f"| {g['name']} | structural | {g['status']} | "
                       f"{g['detail'].replace('|', '/')[:140]} |")
        if r["control"]:
            passed = [g["name"] for g in r["eval_graders"] if g["passed"]] + \
                     [g["name"] for g in r["structural"] if g["status"] == structural.PASS]
            out.append(f"\nCONTROL {'OK: every grader failed' if not passed else 'BROKEN: these passed on a bad emission: ' + ', '.join(passed)}")
        out.append("")
    return "\n".join(out)


def find_bash() -> str:
    """Git's bash on Windows (plain `bash` there may be WSL's, which cannot see this path)."""
    git = shutil.which("git")
    if os.name == "nt" and git:
        for cand in (Path(git).parent.parent / "bin" / "bash.exe",
                     Path(git).parent.parent.parent / "bin" / "bash.exe"):
            if cand.exists():
                return str(cand)
    return shutil.which("bash") or "bash"


def print_shas() -> int:
    for variant, calls in build_cases.VARIANT_CALLS.items():
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            script = f'source "{(EVALS / "fixtures" / "scaffold-lib.sh").as_posix()}"; ' + "; ".join(calls)
            subprocess.run([find_bash(), "-c", script], cwd=d, check=True,
                           env={**os.environ, "HOME": d})
            log = subprocess.run(["git", "log", "--oneline", "--all"], cwd=d, check=True,
                                 capture_output=True, text=True).stdout
            print(f"[{variant}]\n{log}")
    return 0


def regrade(results: Path) -> int:
    """Re-apply lint/structural.py to a finished run's saved final.md and trace. The workspace is
    gone by then, so the file list comes from the spec (the scaffold is deterministic) and the
    temp-home archive check is not repeated (the trace's tool calls still are)."""
    agg = json.loads((results / "aggregate.json").read_text(encoding="utf-8"))
    rows = json.loads((results / "structural.json").read_text(encoding="utf-8"))
    for row in rows:
        spec = build_cases.SPEC.get(row["case"]) or build_cases.SPEC["slice"]
        d = results / row["case"] / f"run{row['run']}"
        if not (d / "final.txt").exists():
            continue
        t = read_trace(d / "trace.jsonl")
        scripts = set(json.loads((build_cases.FIXTURE / "package.json").read_text(
            encoding="utf-8"))["scripts"])
        res = structural.grade((d / "final.txt").read_text(encoding="utf-8"), cap=spec["cap"],
                               cap_multi=spec.get("cap_multi"), scripts=scripts,
                               files=build_cases.fixture_files(spec["variant"]),
                               tool_uses=t["tools"], home=None)
        row["structural"] = [r.as_dict() for r in res]
    (results / "structural.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    text = summary(rows, agg)
    (results / "summary.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case", help="case name glob, e.g. slice")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--model", help="model under test (default: the eval child's default)")
    ap.add_argument("--max-cost-usd", type=float)
    ap.add_argument("--controls", action="store_true", help="run the negative control instead")
    ap.add_argument("--validate", action="store_true", help="load the suite, run nothing")
    ap.add_argument("--keep", action="store_true", help="keep the eval temp dirs")
    ap.add_argument("--print-shas", action="store_true")
    ap.add_argument("--regrade", type=Path, help="re-grade a finished results dir")
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    if args.print_shas:
        return print_shas()
    if args.regrade:
        return regrade(args.regrade)
    if subprocess.run([sys.executable, str(EVALS / "build_cases.py"), "--check"]).returncode:
        sys.exit("evals/cases is stale: run python evals/build_cases.py")
    if args.validate:
        args.max_cost_usd = 0
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out = EVALS / "results" / stamp
    out.mkdir(parents=True, exist_ok=True)
    tag = "control" if args.controls else "baseline"
    cmd = eval_cmd(args, out, tag)
    print("$ " + " ".join(cmd[1:]), flush=True)
    if args.validate:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        text = proc.stdout + proc.stderr
        print(text)
        shutil.rmtree(out, ignore_errors=True)
        bad = "failed to load" in text or proc.returncode not in (0, 2)
        print(f"validate: eval CLI exit {proc.returncode}; "
              + ("FAIL: a case did not load" if bad else "OK: every case loaded, no run started"))
        return 1 if bad else 0
    code = subprocess.run(cmd).returncode
    agg_path = out / "aggregate.json"
    if not agg_path.exists():
        print(f"no aggregate.json (eval exit {code})")
        return 1
    agg = json.loads(agg_path.read_text(encoding="utf-8"))
    rows = post_grade(agg, out, args.keep)
    (out / "structural.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    text = summary(rows, agg)
    (out / "summary.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"results: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
