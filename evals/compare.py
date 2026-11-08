#!/usr/bin/env python3
"""Compare a candidate eval run with the baseline and apply the CP4 acceptance gates.

    python evals/compare.py --baseline evals/results/<ts> --baseline-ref 758e59e \
                            --candidate <dir>/evals/results/<ts> --candidate-ref <sha> \
                            [--extra-baseline commit-finished=evals/results/<ts>@<sha> ...]

Both result dirs must hold structural.json graded by the same grader version (re-grade the older one
with `run.py --regrade` first) and each run's trace.jsonl. Gates (agreed for CP4):
  G1  no deterministic grader goes PASS -> FAIL in any case (in-eval regex/tool_used graders, minus
      the in-eval protocol-loaded regex, which is expected to break once the double read goes; plus
      every structural grader)
  G2  cites-real and gates-exist hold: no PASS -> FAIL
  G3  rule bytes drop by >= 25% at the median case. Rule bytes = the shim and its @-included files
      at the ref (git show) + the text returned by every Read of a rules file in the trace
  G4  no Read of PROTOCOL.md, guide/03-blocks.md or an archetype file the shim already
      @-includes, in any case (a hybrid reading a second archetype is listed, not failed)
It also prints cache-write / cache-read tokens per case, to show the @-include vs Read trade.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
ROOT = EVALS.parent
sys.path.insert(0, str(EVALS))

import build_cases  # noqa: E402

RULE_DIRS = ("archetypes/", "guide/", "stacks/", "examples/", "utilities/")
EVAL_EXCLUDE = {"protocol-loaded"}  # the in-eval regex keys on the Read E-09b removes
INCLUDE_RE = re.compile(r"^@\$\{CLAUDE_PLUGIN_ROOT\}/(\S+)", re.M)


def git_show(ref: str, path: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:{path}"], check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout


def load_bytes(ref: str, cmd: str) -> int:
    shim = git_show(ref, f"commands/{cmd}.md")
    return len(shim.encode()) + sum(len(git_show(ref, inc).encode())
                                   for inc in INCLUDE_RE.findall(shim))


def rule_path(path: str) -> str | None:
    """The plugin-relative path of a rules file, or None for anything else (e.g. the fixture)."""
    p = path.replace("\\", "/")
    if p.endswith("/PROTOCOL.md") or p == "PROTOCOL.md":
        return "PROTOCOL.md"
    for d in RULE_DIRS:
        i = p.find("/" + d)
        if i >= 0 and "/cwd/" not in p:
            return p[i + 1:]
    return None


def trace_rule_reads(trace: Path) -> tuple[list[str], int]:
    calls: dict[str, str] = {}
    paths, total = [], 0
    for raw in trace.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            continue
        msg = ev.get("message") if isinstance(ev, dict) else None
        content = msg.get("content") if isinstance(msg, dict) else None
        for b in content if isinstance(content, list) else []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and b.get("name") == "Read":
                rp = rule_path(b.get("input", {}).get("file_path", ""))
                if rp:
                    calls[b["id"]] = rp
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                c = b.get("content")
                text = c if isinstance(c, str) else json.dumps(c)
                paths.append(calls[b["tool_use_id"]])
                total += len(text.encode())
    return paths, total


def load(results: Path) -> dict[str, dict]:
    rows = json.loads((results / "structural.json").read_text(encoding="utf-8"))
    return {r["case"]: r for r in rows if not r.get("control")}


def status_map(row: dict) -> dict[str, str]:
    out = {f"eval:{g['name']}": ("PASS" if g["passed"] else "FAIL")
           for g in row["eval_graders"]
           if not g["name"].startswith("rubric") and g["name"] not in EVAL_EXCLUDE}
    out.update({f"structural:{g['name']}": g["status"] for g in row["structural"]})
    return out


def parse_extra(specs: list[str]) -> dict[str, tuple[Path, str]]:
    """--extra-baseline CASE=RESULTS_DIR@REF → {case: (dir, ref)}. For a case with no row in the
    main baseline (commit-finished: compared against its CP4 run at 4fb361a)."""
    out: dict[str, tuple[Path, str]] = {}
    for spec in specs:
        m = re.match(r"^([\w-]+)=(.+)@([0-9A-Za-z._/-]+)$", spec)
        if not m:
            raise SystemExit(f"--extra-baseline wants CASE=RESULTS_DIR@REF, got {spec!r}")
        out[m.group(1)] = (Path(m.group(2)), m.group(3))
    return out


def compare(base_dir: Path, base_ref: str, cand_dir: Path, cand_ref: str,
            extra: dict[str, tuple[Path, str]] | None = None) -> tuple[list[str], list[str], list]:
    """Returns (table lines, notes, gates). Cases in --extra-baseline are compared with their own
    baseline run for G1/G2/G4; they stay out of G3's median, which measures the change against the
    main baseline. Candidate cases tagged extra in build_cases (e.g. slice-monorepo) have no
    baseline: they are reported, not gated."""
    extra = extra or {}
    base, cand = load(base_dir), load(cand_dir)
    sources: dict[str, tuple[dict, Path, str]] = {c: (r, base_dir, base_ref) for c, r in base.items()}
    for case, (d, ref) in extra.items():
        rows = load(d)
        if case not in rows:
            raise SystemExit(f"--extra-baseline {case}: no such case in {d}")
        sources[case] = (rows[case], d, ref)
    gv = {r.get("grader_version") for r in [*(s[0] for s in sources.values()), *cand.values()]}
    if len(gv) != 1:
        raise SystemExit(f"grader versions differ {gv}: re-grade with run.py --regrade first")

    regress, hold_fail, forbidden, drops, notes = [], [], [], [], []
    lines = ["| Case | baseline | rule bytes base → cand (Δ) | rule Reads (cand) | "
             "cache write base → cand | cache read base → cand | output base → cand | "
             "$ base → cand |", "|---|---|---|---|---|---|---|---|"]
    for case in [c for c in build_cases.SPEC if c in sources and c in cand]:
        b, bdir, bref = sources[case]
        c = cand[case]
        bs, cs = status_map(b), status_map(c)
        exempt: set[str] = set()
        if case == "commit":
            # Planner ruling: the fixture's work is unfinished, so the correct output is a refusal
            # with no prompt block. archive-valid never gates commit, and a grader that failed
            # only because there is no block is not a regression.
            exempt.add("structural:archive-valid")
            exempt |= {f"structural:{g['name']}" for g in c["structural"]
                       if "no prompt block" in g["detail"] or "no fenced prompt" in g["detail"]
                       or (g["name"] == "self-check" and "no self-check" in g["detail"])}
            if exempt:
                notes.append(f"commit: exempt from G1 ({', '.join(sorted(exempt))})")
        for name, st in bs.items():
            if name in exempt:
                continue
            if st == "PASS" and cs.get(name) == "FAIL":
                regress.append(f"{case}: {name}")
                if name in ("structural:cites-real", "structural:gates-exist"):
                    hold_fail.append(f"{case}: {name}")
        cmd = build_cases.ARCHIVE_META[case][1].split("+")[0]
        bt = load_bytes(bref, cmd) + trace_rule_reads(bdir / case / "run1" / "trace.jsonl")[1]
        cpaths, cread = trace_rule_reads(cand_dir / case / "run1" / "trace.jsonl")
        ct = load_bytes(cand_ref, cmd) + cread
        # Forbidden: PROTOCOL, 03-blocks and the files this shim already @-includes. Another
        # archetype a hybrid needs (next-hybrid reading D-slice.md) is reported, not failed.
        included = set(INCLUDE_RE.findall(git_show(cand_ref, f"commands/{cmd}.md")))
        forbidden += [f"{case}: {p}" for p in cpaths
                      if p in included or p in ("PROTOCOL.md", "guide/03-blocks.md")]
        if case in extra:
            notes.append(f"{case}: compared against its own baseline {bdir.name} @ {bref} "
                         f"(--extra-baseline); not in G3's median")
        else:
            drops.append((bt - ct) / bt)
        bu, cu = b.get("usage") or {}, c.get("usage") or {}
        lines.append(
            f"| {case} | {bref} | {bt:,} → {ct:,} ({(ct - bt) / bt:+.0%}) | "
            f"{', '.join(cpaths) or 'none'} | "
            f"{bu.get('cache_creation_input_tokens', 0):,} → {cu.get('cache_creation_input_tokens', 0):,} | "
            f"{bu.get('cache_read_input_tokens', 0):,} → {cu.get('cache_read_input_tokens', 0):,} | "
            f"{bu.get('output_tokens', 0):,} → {cu.get('output_tokens', 0):,} | "
            f"{b.get('eval_cost_usd') or 0:.3f} → {c.get('eval_cost_usd') or 0:.3f} |")
    for case in [c for c in cand if c not in sources]:
        st = [g for g in cand[case]["structural"] if g["status"] != "SKIPPED"]
        notes.append(f"{case}: no baseline, reported not gated: eval score "
                     f"{cand[case].get('eval_score')}, structural "
                     f"{sum(g['status'] == 'PASS' for g in st)}/{len(st)}")
    med = statistics.median(drops) if drops else 0.0
    gates = [
        ("G1 no deterministic grader PASS→FAIL", not regress, "; ".join(regress) or "none"),
        ("G2 cites-real + gates-exist hold", not hold_fail, "; ".join(hold_fail) or "held"),
        ("G3 rule bytes drop ≥25% at the median", med >= 0.25, f"median drop {med:.1%}"),
        ("G4 no Read of PROTOCOL/archetype/03-blocks", not forbidden,
         "; ".join(forbidden) or "none"),
    ]
    return lines, notes, gates


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--baseline-ref", required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--candidate-ref", required=True)
    ap.add_argument("--extra-baseline", action="append", default=[], metavar="CASE=DIR@REF",
                    help="compare CASE against another run, e.g. "
                         "commit-finished=evals/results/2026-11-08T17-32-10Z@4fb361a")
    args = ap.parse_args()
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    lines, notes, gates = compare(args.baseline, args.baseline_ref, args.candidate,
                                  args.candidate_ref, parse_extra(args.extra_baseline))
    print("\n".join(lines))
    print()
    for n in notes:
        print(f"note  {n}")
    for name, ok, detail in gates:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    verdict = all(ok for _, ok, _ in gates)
    print(f"\nacceptance: {'PASS' if verdict else 'FAIL'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
