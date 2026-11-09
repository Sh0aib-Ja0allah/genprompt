# CP6 plan: rule set and cost estimate (draft, nothing run)

| | |
|---|---|
| Status | **Draft for the PE and the Planner.** Shoaib approves the cost before any spend |
| Candidate | the 1.3.0 release candidate SHA, with E-14 (archetype X, `:investigate`) merged. Not yet fixed |
| Baselines | v1.1.0 `fb4db7b` and v1.2.0 `d584108` load medians stored in CP6a (no new baseline runs); quality vs CP5 `evals/results/2026-11-08T19-07-58Z` |
| Estimate | **about $4.90 expected; cap request $5.75** (breakdown below) |

## Prerequisites (offline, no spend)

1. **E-14 merged** into the candidate. Until then `investigate` can't be probed or evaluated.
2. **A probe request for `investigate`** in `evals/realuse/run.py` (`REQUESTS`): a bug symptom in
   the ledgerlite fixture with no known cause. It is added only once E-14 is on the candidate,
   because `--cases` is checked against `REQUESTS` and older refs have no `:investigate`.
3. **An eval case `evals/cases/investigate`** (case.yaml, prompt.md, scaffold.sh, graders), made
   up like the others, with the symptom planted in the scaffold. It needs an archetype-label
   grader for X and the same rubric graders as the other cases.
4. **The A5 drive-root fix** (done on this branch): a drive-root Glob/Grep is judged by the names
   it returns. Re-analysing the CP6a-2 traces gives 0 flags (was 2). The CP6a leak (a v1.2.0 run
   listing system file names) is still flagged.
5. **The isolation check** passes on the candidate before anything else (about $0.004).

## Rules (fixed before results)

Stop at the first failure. No re-runs, no remedies without Shoaib. An incomplete run is reported
as incomplete, and a partial set is never a pass.

### Load (haiku, 3 runs per cell, fresh sandbox home per run)

| Probe | Cases | Gate |
|---|---|---|
| card-less (`--home empty`) | slice, fix, redesign, plan | per-case median ≤ v1.1.0 **and** ≤ v1.2.0 stored medians (as CP6a-2) |
| card-less | investigate | **reported, not gated**: no earlier version has X. Proposed soft check: median ≤ 35,000 B (an E-09f floor of about 30 KB plus one `derive.md` read) |
| card-fresh (`--home card`) | all 5 | **reported, not gated** against old versions (see below). Proposed self-gate: each case's card-fresh median ≤ its card-less median |
| all | all | A1 (no Read of an @-included file, PROTOCOL.md or 03-blocks) and A5 (isolation) are gates |

Why card-fresh can't be gated against v1.1.0/v1.2.0: older refs ignore `GENPROMPT_HOME`, so a
base run can't see the sandbox card, and the real `~/.genprompt` stays denied. A fresh card
replaces the derivation, so the candidate's card-fresh run should never load more than its
card-less run. That is the self-gate proposed above, and the Planner decides whether it gates.

### Quality (opus-5-5, 1 run per case, plugin eval at the candidate)

| Cases | Gate |
|---|---|
| slice, fix, redesign, plan | no regression vs CP5 on rubric-scope, rubric-grounding, cites-real, gates-exist (as CP6a-2) |
| investigate | no CP5 result exists, so the gate is absolute: all four gated graders PASS |

Other graders (line-length, no-placeholders, self-check, archive-valid) are reported, not gated.

## Cost estimate

| Item | Basis | Expected |
|---|---|---|
| isolation check | CP6a-2: $0.0033 + $0.0041 | $0.01 |
| card-less load, 5 × 3 runs | CP6a-2 mean $0.023 per run (range $0.013–0.056); $0.03 used | $0.45 |
| card-fresh load, 5 × 3 runs | no data yet; same $0.03 per run assumed | $0.45 |
| quality slice | CP5 $0.7733; CP6a-2 cases ran +0% to +44% over CP5 | $0.95 |
| quality fix | CP5 $0.5267, CP6a-2 $0.5270 | $0.55 |
| quality redesign | CP6a-2 $0.8258 | $0.85 |
| quality plan | CP6a-2 $0.7100 | $0.75 |
| quality investigate | no data; assumed like redesign | $0.85 |
| **Total** | | **≈ $4.86** |

- **Cap request: $5.75**, about 18% headroom, mostly for the two cases with no data.
- **Spend-guard parameters** (the CP6a-2 lesson): `--max-total` refuses a run when spent plus
  the per-run cap could exceed it, so each load probe's total must be its expected spend plus one
  per-run cap. Card-less and card-fresh: `--budget 0.08 --max-total 0.55` each. Quality: each
  case gets `--max-cost-usd` at about 1.4× its expected cost, within the remainder of the cap.
- **Order**, so an early failure spends least: isolation → card-less load → card-fresh load →
  quality (fix, plan, redesign, slice, investigate).

## Notes carried into CP6 (not gates)

- **no-placeholders false alarm (CP6a-2 plan).** The grader matched `<WS letter>` and
  `<two digits>` in "Stable ids (<WS letter>-<two digits>), never renumbered once written." That
  line describes the id format; it is not an unfilled slot, and doctor rated it a WARN. Two
  options: the grader skips a placeholder that sits inside a format description, or the
  generator writes a concrete example (`WS-01`) instead. If it recurs in CP6 it is reported
  with this explanation, not counted as a regression.
- **fix's rubric-grounding passed on 2 of 3 votes in CP6a-2** (3 of 3 at CP5). Watch it in CP6.
  The harness doesn't show the judge's reasoning.
- **Windows and `archive.py --where`.** `python3 … --where` often hits the store alias or is
  denied; card-fresh runs depend on the home path, so Bash results are listed in the report.
