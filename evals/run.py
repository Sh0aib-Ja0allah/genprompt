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

# The lint archive-valid calls, pinned to this tree so a run against another branch (CP4) is
# graded by the same doctor. --doctor overrides it; --plugin picks the plugin under test.
DOCTOR = ROOT / "tools" / "doctor.py"
PLUGIN = ROOT


def claude() -> str:
    exe = shutil.which("claude")
    if not exe:
        sys.exit("claude CLI not found on PATH")
    return exe


def eval_cmd(args, out: Path, tag: str) -> list[str]:
    cmd = [claude(), "plugin", "eval", str(PLUGIN), "--tag", tag, "--ablation", "none",
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
    if getattr(args, "judge_model", None):
        cmd += ["--judge-model", args.judge_model]  # J-method (1.3.1): recorded in structural.json
    if not args.validate and not getattr(args, "no_debug", False):
        # J-method: keep the eval's debug log beside the results, in case it holds the judge
        # text. --debug-file is a global claude option, so it goes before `plugin eval`.
        cmd[1:1] = ["--debug-file", str(out / "eval-debug.log")]
        cmd.append("--verbose")
    if tag == "control":
        cmd += ["--allow-tools", "Write"]  # so the control's write attempt shows no-write failing
    return cmd


def read_trace(path: Path) -> dict:
    final, tools, model, result = "", [], None, {}
    last_text: list[str] = []
    events: list[dict] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            continue
        events.append(ev)
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
    return {"final": final, "tools": tools, "model": model, "events": events,
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
        spec = {**build_cases.SPEC, **build_cases.EXTRA}.get(name) or build_cases.SPEC["slice"]
        meta = build_cases.ARCHIVE_META.get(name, ("D", "slice"))
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
                # a monorepo case gates on its in-scope package's scripts
                pkg = ws / spec.get("package", ".") / "package.json"
                scripts = set(json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {})) \
                    if pkg.exists() else None
                res = structural.grade(t["final"], cap=spec["cap"], cap_multi=spec.get("cap_multi"),
                                       scripts=scripts, files=workspace_files(ws),
                                       tool_uses=t["tools"], home=home,
                                       trace_events=t["events"],
                                       letters=meta[0], cmd=meta[1], doctor=DOCTOR,
                                       package=spec.get("package"), sibling=spec.get("sibling"),
                                       untrusted=spec.get("untrusted"))
                row.update({k: t[k] for k in ("model", "cost_usd", "turns", "usage",
                                              "model_usage")})
                row["structural"] = [r.as_dict() for r in res]
                row["grader_version"] = structural.GRADER_VERSION
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
                   f" · turns {r.get('turns')} · usage {r.get('usage')}"
                   + (f" · judge {r['judge_model']}" if r.get("judge_model") else ""))
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
            # The control cannot exercise these; each is shown failing elsewhere.
            unexercised = {"no-edit": "same tool_used check as no-write, which fails here",
                           "length-cap": "the sample is short; lint/test_structural.py "
                                         "test_length_cap_fails_when_over shows it failing",
                           "archive-valid": "doctor --prompt grades this sample's defects as "
                                            "WARN, not FAIL; test_archive_valid_fails_bad_and_stub "
                                            "shows a stub and an unclosed fence failing"}
            broken = [n for n in passed if n not in unexercised]
            notes = "; ".join(f"{n}: {why}" for n, why in unexercised.items() if n in passed)
            out.append(f"\nCONTROL {'OK' if not broken else 'BROKEN'}: "
                       + (f"these passed on a bad emission: {', '.join(broken)}"
                          if broken else "every exercised grader failed")
                       + (f" (not exercised: {notes})" if notes else ""))
        out.append("")
    return "\n".join(out)


# J-method (1.3.1, option D). The gated graders R4/R3 judge; a case that FAILS any of them gets
# 2 more generations, and each gated grader's verdict is then the majority of the 3 runs.
GATED = ("rubric-scope", "rubric-grounding", "cites-real", "gates-exist")
LLM_GATED = ("rubric-scope", "rubric-grounding")
ESCALATE_RUNS = 2


def gated_verdicts(row: dict) -> dict[str, bool]:
    """One run's verdict per gated grader: True = PASS. Eval graders and structural ones."""
    out = {g["name"]: bool(g["passed"]) for g in row.get("eval_graders", [])
           if g["name"] in GATED}
    out.update({g["name"]: g["status"] == structural.PASS for g in row.get("structural", [])
                if g["name"] in GATED})
    return out


def needs_escalation(rows: list[dict]) -> bool:
    """A single run of a case FAILED a gated grader (or a gated grader is missing)."""
    return any(not all(gated_verdicts(r).get(g, False) for g in GATED) for r in rows)


def majority(rows: list[dict]) -> dict[str, dict]:
    """Per gated grader: the run verdicts and the majority (strictly more PASS than FAIL)."""
    out = {}
    for g in GATED:
        votes = [gated_verdicts(r).get(g, False) for r in rows]
        out[g] = {"runs": ["PASS" if v else "FAIL" for v in votes],
                  "verdict": "PASS" if sum(votes) * 2 > len(votes) else "FAIL"}
    return out


def explain_targets(agg: dict) -> list[tuple[str, int, str, str]]:
    """(case, run, grader, rubric text) for each gated LLM grader that FAILED or split its
    votes; the only graders `--explain` asks about."""
    out = []
    for case in agg.get("cases", []):
        rubric = {g["name"]: g.get("graderMarkdown", "") for g in case.get("graders", [])}
        for i, run in enumerate(case.get("arms", {}).get("with", [])):
            for g in run.get("graders", []):
                votes = g.get("judgeVotes") or []
                if g["name"] in LLM_GATED and (not g.get("passed") or len(set(votes)) > 1):
                    out.append((case["name"], i + 1, g["name"], rubric.get(g["name"], "")))
    return out


EXPLAIN_TOOLS_OFF = ["Bash", "PowerShell", "Read", "Glob", "Grep", "Write", "Edit",
                     "NotebookEdit", "WebFetch", "WebSearch", "Task", "Agent"]


def explain_prompt(rubric: str, final: str) -> str:
    return ("You are re-checking one LLM grader's verdict on a stored eval output. Apply the "
            "rubric below to the RESPONSE exactly as a grader would. Use no tools. Reply with "
            "one JSON object only: {\"verdict\": \"PASS\" or \"FAIL\", \"reason\": \"<the "
            "specific line(s) of the response and the rubric clause that decide it, at most "
            "120 words>\"}.\n\n=== RUBRIC ===\n" + rubric.strip() +
            "\n\n=== RESPONSE ===\n" + final.strip() + "\n")


def explain_cmd(model: str, budget: float, prompt: str) -> list[str]:
    return [claude(), "-p", "--model", model, "--output-format", "json",
            "--setting-sources", "local", "--strict-mcp-config", "--permission-mode", "dontAsk",
            "--no-session-persistence", "--max-budget-usd", f"{budget:.2f}",
            "--disallowedTools", *EXPLAIN_TOOLS_OFF, "--", prompt]


def explain_notes(results: Path, model: str, budget: float, max_total: float,
                  spent: float = 0.0) -> tuple[list[dict], float]:
    """The core of --explain for one results dir: one call per target while `spent` + the
    per-call cap fits `max_total`. Returns the notes and the new running total."""
    agg = json.loads((results / "aggregate.json").read_text(encoding="utf-8"))
    notes = []
    for case, run, grader, rubric in explain_targets(agg):
        final = results / case / f"run{run}" / "final.txt"
        if not final.exists():
            notes.append({"case": case, "run": run, "grader": grader, "error": "no final.txt"})
            continue
        if spent + budget > max_total:
            notes.append({"case": case, "run": run, "grader": grader,
                          "error": f"skipped: ${spent:.4f} spent, cap ${max_total}"})
            continue
        p = subprocess.run(explain_cmd(model, budget, explain_prompt(
            rubric, final.read_text(encoding="utf-8"))), capture_output=True, text=True,
            encoding="utf-8", errors="replace", cwd=results)
        try:
            res = json.loads(p.stdout)
        except json.JSONDecodeError:
            res = {"result": p.stdout[-500:], "total_cost_usd": 0}
        spent += res.get("total_cost_usd") or 0
        notes.append({"case": case, "run": run, "grader": grader, "model": model,
                      "answer": res.get("result"), "cost_usd": res.get("total_cost_usd")})
    return notes, spent


def explain(results: Path, model: str, budget: float, max_total: float) -> int:
    """J-method: for each gated LLM grader that FAILED or split, ask the judge model once for a
    verdict and its reason, and store them in explain.json. An explanation, never a verdict:
    gates stay on the harness votes."""
    notes, spent = explain_notes(results, model, budget, max_total)
    (results / "explain.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")
    for n in notes:
        print(f"{n['case']} run{n['run']} {n['grader']}: "
              f"{n.get('answer') or n.get('error')}")
    print(f"explain: {len(notes)} grader(s), ${spent:.4f}")
    return 0


def auto_explain(out: Path, model: str, budget: float, max_total: float) -> dict:
    """1.4.0 item 5, recommendation (5): after a real run (and its escalation, if any), explain
    every gated LLM grader that FAILED or split, in the run's dir and each escalation-<case>/
    dir, under ONE running total (`max_total`) and the per-call cap (`budget`). Never touches a
    verdict: aggregate.json, structural.json and escalation.json's verdicts are read, not written.
    Writes <dir>/explain.json per dir with targets, adds `explain_cost_usd` to escalation.json
    (so a driver that sums escalation.json costs sees the spend), and returns a summary."""
    dirs = [d for d in [out, *sorted(out.glob("escalation-*"))]
            if (d / "aggregate.json").exists()]
    targets = {d: explain_targets(json.loads((d / "aggregate.json").read_text(encoding="utf-8")))
               for d in dirs}
    summary = {"model": model, "targets": sum(len(t) for t in targets.values()),
               "explained": 0, "skipped": 0, "cost_usd": 0.0}
    if not summary["targets"]:
        print("auto-explain: no gated FAIL or split vote, nothing to explain ($0)")
        return summary
    spent = 0.0
    for d in dirs:
        if not targets[d]:
            continue
        notes, spent = explain_notes(d, model, budget, max_total, spent)
        (d / "explain.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")
        for n in notes:
            summary["skipped" if n.get("error") else "explained"] += 1
            print(f"auto-explain {d.name} {n['case']} run{n['run']} {n['grader']}: "
                  f"{n.get('answer') or n.get('error')}")
    summary["cost_usd"] = spent
    esc = out / "escalation.json"
    if esc.exists():
        rep = json.loads(esc.read_text(encoding="utf-8"))
        rep["explain_cost_usd"] = spent
        esc.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(f"auto-explain: {summary['explained']} explained, {summary['skipped']} skipped "
          f"(cap ${max_total}), ${spent:.4f}")
    return summary


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
        spec = {**build_cases.SPEC, **build_cases.EXTRA}.get(row["case"]) or build_cases.SPEC["slice"]
        meta = build_cases.ARCHIVE_META.get(row["case"], ("D", "slice"))
        d = results / row["case"] / f"run{row['run']}"
        if not (d / "final.txt").exists():
            continue
        t = read_trace(d / "trace.jsonl")
        root = build_cases.VARIANT_ROOT.get(spec["variant"], build_cases.FIXTURE)
        scripts = set(json.loads((root / spec.get("package", ".") / "package.json").read_text(
            encoding="utf-8"))["scripts"])
        res = structural.grade((d / "final.txt").read_text(encoding="utf-8"), cap=spec["cap"],
                               cap_multi=spec.get("cap_multi"), scripts=scripts,
                               files=build_cases.fixture_files(spec["variant"]),
                               tool_uses=t["tools"], home=None, trace_events=t["events"],
                               letters=meta[0], cmd=meta[1], doctor=DOCTOR,
                                       package=spec.get("package"), sibling=spec.get("sibling"),
                                       untrusted=spec.get("untrusted"))
        row["structural"] = [r.as_dict() for r in res]
        row["grader_version"] = structural.GRADER_VERSION
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
    ap.add_argument("--tag", default="baseline", help="case tag to run: baseline | extra")
    ap.add_argument("--plugin", type=Path, default=ROOT,
                    help="plugin root under test (default: this tree; CP4 points elsewhere)")
    ap.add_argument("--doctor", type=Path, help="doctor.py for archive-valid (default: this tree)")
    # J-method (1.3.1)
    ap.add_argument("--judge-model", help="LLM-grader model passed to the eval CLI (default: "
                                          "its own, haiku); recorded per row in structural.json")
    ap.add_argument("--no-debug", action="store_true",
                    help="skip --verbose --debug-file (on by default for real runs)")
    ap.add_argument("--escalate", action="store_true",
                    help="option D: a gated FAIL gets 2 more generations; majority of 3")
    ap.add_argument("--escalate-max-cost-usd", type=float,
                    help="cost cap for the 2 extra generations of one case")
    ap.add_argument("--explain", type=Path,
                    help="results dir: ask the judge model why each gated LLM FAIL/split went "
                         "that way; writes explain.json (no verdict changes)")
    ap.add_argument("--explain-budget", type=float, default=0.30,
                    help="$ cap per explain call (--explain and the automatic step)")
    ap.add_argument("--explain-max-total", type=float, default=1.00,
                    help="$ cap for all explain calls of one invocation, escalation dirs included")
    ap.add_argument("--no-auto-explain", action="store_true",
                    help="skip the automatic explain step after a run (it runs by default, only "
                         "for gated LLM FAILs or split votes, and never changes a verdict)")
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    global DOCTOR, PLUGIN
    if args.doctor:
        DOCTOR = args.doctor.resolve()
    PLUGIN = args.plugin.resolve()
    if args.explain:
        if not args.judge_model:
            ap.error("--explain needs --judge-model (the model whose reasoning is wanted)")
        return explain(args.explain, args.judge_model, args.explain_budget,
                       args.explain_max_total)
    if args.escalate and (not args.case or "*" in args.case or args.runs != 1):
        ap.error("--escalate needs one --case and --runs 1 (escalation is per case)")
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
    tag = "control" if args.controls else args.tag
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
    rows, agg = run_once(cmd, out, args)
    if rows is None:
        return 1
    if args.escalate:
        rows = escalate(args, out, tag, rows, agg)
    if not args.no_auto_explain and not args.controls:
        # Recommendation (5): reasons for every gated FAIL or split, verdicts unchanged.
        auto_explain(out, args.judge_model or "haiku", args.explain_budget,
                     args.explain_max_total)
    print(f"results: {out}")
    return 0


def run_once(cmd: list[str], out: Path, args) -> tuple[list[dict] | None, dict]:
    code = subprocess.run(cmd).returncode
    agg_path = out / "aggregate.json"
    if not agg_path.exists():
        print(f"no aggregate.json (eval exit {code})")
        return None, {}
    agg = json.loads(agg_path.read_text(encoding="utf-8"))
    rows = post_grade(agg, out, args.keep)
    for r in rows:
        r["judge_model"] = args.judge_model or "eval CLI default (haiku)"
    (out / "structural.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    text = summary(rows, agg)
    (out / "summary.txt").write_text(text, encoding="utf-8")
    print(text)
    return rows, agg


def escalate(args, out: Path, tag: str, rows: list[dict], agg: dict) -> list[dict]:
    """J-method option D: a case whose single run FAILED a gated grader gets ESCALATE_RUNS more
    generations (one eval call, its own results dir, its own cost cap); each gated grader's
    verdict is then the majority of the 3 runs. escalation.json records the per-run verdicts,
    the majority, and which gated graders the re-sample flipped from FAIL to PASS (O1)."""
    report = {"judge_model": args.judge_model, "cases": {}}
    first_cost = sum(r.get("eval_cost_usd") or 0 for r in rows)
    for case in sorted({r["case"] for r in rows}):
        case_rows = [r for r in rows if r["case"] == case]
        entry = {"first": {g: v["runs"][0] for g, v in majority(case_rows).items()},
                 "escalated": False}
        if needs_escalation(case_rows):
            budget = args.escalate_max_cost_usd
            if budget is None or budget <= 0:
                entry["error"] = "escalation needed but no --escalate-max-cost-usd left"
            else:
                sub = out / f"escalation-{case}"
                sub.mkdir(parents=True, exist_ok=True)
                sargs = argparse.Namespace(**{**vars(args), "case": case,
                                              "runs": ESCALATE_RUNS, "max_cost_usd": budget})
                more, _ = run_once(eval_cmd(sargs, sub, tag), sub, sargs)
                if more is None or len(more) < ESCALATE_RUNS:
                    entry["error"] = "escalation incomplete (an incomplete case is a stop)"
                    more = more or []
                for i, r in enumerate(more):
                    r["run"] = len(case_rows) + i + 1
                case_rows = case_rows + more
                entry["escalated"] = True
                entry["escalation_cost_usd"] = sum(r.get("eval_cost_usd") or 0 for r in more)
        m = majority(case_rows)
        entry["runs"] = {g: v["runs"] for g, v in m.items()}
        entry["final"] = {g: v["verdict"] for g, v in m.items()}
        entry["flipped_to_pass"] = [g for g in GATED
                                    if entry["first"][g] == "FAIL" and entry["final"][g] == "PASS"]
        # X2: both directions (a grader that passed run 1 can lose the 3-run majority)
        entry["flipped_to_fail"] = [g for g in GATED
                                    if entry["first"][g] == "PASS" and entry["final"][g] == "FAIL"]
        report["cases"][case] = entry
    report["first_pass_cost_usd"] = first_cost
    report["escalation_cost_usd"] = sum(e.get("escalation_cost_usd", 0)
                                        for e in report["cases"].values())
    (out / "escalation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for case, e in report["cases"].items():
        print(f"{case}: final {e['final']} · escalated {e['escalated']} · FAIL->PASS "
              f"{e['flipped_to_pass'] or 'none'} · PASS->FAIL {e['flipped_to_fail'] or 'none'}"
              + (f" · {e['error']}" if e.get("error") else ""))
    return rows


if __name__ == "__main__":
    sys.exit(main())
