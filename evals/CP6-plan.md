# CP6 plan: rule set and cost estimate (nothing run)

| | |
|---|---|
| Status | **Rules fixed by the Planner's rulings R1–R5 (PLAN.md step 9). Cost not yet approved:** the estimate goes to Shoaib with a fresh number once the final candidate exists |
| Candidate | the final 1.3.0 candidate, after E-12, E-13, E-15 and E-20 merge. CP6 records its SHA as **frozen** (R5) |
| Baselines | load: v1.1.0 `fb4db7b` and v1.2.0 `d584108` medians stored in CP6a (no new baseline runs). Quality: CP5 `evals/results/2026-11-08T19-07-58Z` |
| Estimate | **about $4.86 expected; cap request $5.75** (breakdown below; to be refreshed on the final candidate) |

## Prerequisites (offline, no spend)

1. **E-14 merged** (done: 9484139).
2. **The probe request for `investigate`** in `evals/realuse/run.py` (`REQUESTS`; done). The
   request gives a symptom only: `npm start -- examples/sample.json --lines` prints the right
   per-line amounts (25.00, 40.00 and 5.00 EUR) but TOTAL 40.50 EUR instead of 63.00 EUR. The
   cause, src/invoice.js:14, is for the generator to ground. A test checks the symptom against
   the fixture.
3. **The eval case `evals/cases/investigate`** (done; generated from `evals/build_cases.py`). It
   is tagged `extra`, like slice-monorepo, because it has no CP5 baseline. So CP6 runs it with
   `evals/run.py --tag extra --case investigate`. `--validate --tag extra` loads it with no
   spend.
4. **A5 drive-root fix** (done): a drive-root Glob/Grep is judged by the names it returns.
5. **Card-fresh gates in `realuse/run.py`** (done): `--home card` records the seeded card's
   bytes per run and adds gates C1 and C2 (R2). It refuses to start without `--cardless` medians
   for every case.
6. **The isolation check** passes on the candidate before anything else (about $0.004).

## Rules (fixed before results)

Stop at the first gate failure. No re-runs, no remedies without Shoaib. An incomplete run is
reported as incomplete, and a partial set is never a pass.

### Load (haiku, 3 runs per cell, fresh sandbox home per run)

| Probe | Cases | Gate |
|---|---|---|
| card-less (`--home empty`) | slice, fix, redesign, plan | per-case median ≤ v1.1.0 **and** ≤ v1.2.0 stored medians (as CP6a-2) |
| card-less | investigate | **R1: reported, not gated.** Soft line 40,000 B. Going over it doesn't block, but it must be named in the 1.3.0 CHANGELOG |
| card-fresh (`--home card`) | all 5 | **R2, gated:** C1 no card-fresh run Reads `guide/blocks/derive.md`, `guide/01-target-profile.md` or `stacks/stack-matrix.md`. C2 each case's card-fresh median ≤ its card-less median (from this CP6's card-less probe) + the seeded card's bytes. The card size is recorded per run. No comparison with v1.1.0 or v1.2.0 |
| all | all 5 | A1 (no Read of an @-included file, PROTOCOL.md or 03-blocks) and A5 (isolation) gate, investigate included (R1) |

The card-fresh probe runs after the card-less one and takes its medians, e.g.
`--home card --cardless slice=<m> fix=<m> redesign=<m> plan=<m> investigate=<m>`.

### Quality (opus-5-5, 1 run per case, plugin eval at the candidate)

| Cases | Gate |
|---|---|
| slice, fix, redesign, plan | **R4:** no regression vs CP5 on rubric-scope, rubric-grounding, cites-real and gates-exist. Rubrics compare **majority verdicts** (≥ 2 of 3 votes), not vote counts. The counts are reported too |
| investigate | **R3, absolute:** all four gated graders PASS, rubrics by majority (≥ 2 of 3). One run; a fail stops CP6 and goes to Shoaib |

Other graders (line-length, no-placeholders, self-check, archive-valid) are reported, not gated.

### Frozen candidate (R5)

CP6 records the candidate SHA it ran on. If PROTOCOL, guide/ or archetypes/ change after that,
the card-less load re-runs, and so does quality for every case the edit touches. This is not
in the estimate below; see the contingency line.

## Cost estimate

| Item | Basis | Expected |
|---|---|---|
| isolation check | CP6a-2: $0.0033 + $0.0041 | $0.01 |
| card-less load, 5 × 3 runs | CP6a-2 mean $0.023 per run (range $0.013–0.056); $0.03 used | $0.45 |
| card-fresh load, 5 × 3 runs | no data yet; the same $0.03 per run assumed | $0.45 |
| quality slice | CP5 $0.7733; CP6a-2 cases ran +0% to +44% over CP5 | $0.95 |
| quality fix | CP5 $0.5267, CP6a-2 $0.5270 | $0.55 |
| quality redesign | CP6a-2 $0.8258 | $0.85 |
| quality plan | CP6a-2 $0.7100 | $0.75 |
| quality investigate | no data; assumed like redesign | $0.85 |
| **Total** | | **≈ $4.86** |

- **Cap request: $5.75**, about 18% headroom, mostly for card-fresh and investigate, which
  have no data yet. The rulings add no runs, so the number is unchanged from the draft.
- **R5 contingency (not in the cap):** a re-run after a late rules edit costs $0.45 for the
  card-less load plus $0.55–0.95 per touched case's quality run. All five cases would be about
  $4.40.
- **Spend-guard parameters** (the CP6a-2 lesson): `--max-total` refuses a run when spent plus
  the per-run cap could exceed it, so each load probe's total must be its expected spend plus one
  per-run cap. Card-less and card-fresh: `--budget 0.08 --max-total 0.55` each. Quality: each
  case gets `--max-cost-usd` at about 1.4× its expected cost, within the remainder of the cap.
- **Order**, so an early failure spends least: isolation → card-less load → card-fresh load
  (needs the card-less medians) → quality (fix, plan, redesign, slice, investigate).

## Notes carried into CP6 (not gates)

- **no-placeholders false alarm (CP6a-2 plan).** The grader matched `<WS letter>` and
  `<two digits>` in "Stable ids (`<WS letter>-<two digits>`), never renumbered once written." That
  line describes the id format; it is not an unfilled slot, and doctor rated it a WARN. Two
  options: the grader skips a placeholder that sits inside a format description, or the
  generator writes a concrete example (`WS-01`) instead. If it recurs in CP6 it is reported
  with this explanation, not counted as a regression.
- **fix's rubric-grounding passed on 2 of 3 votes in CP6a-2** (3 of 3 at CP5). Under R4 that is
  still a PASS (the majority verdict); the counts are reported.
- **Windows and `archive.py --where`.** `python3 … --where` often hits the store alias or is
  denied. Card-fresh runs depend on the home path, so their Bash results are listed in the report.
