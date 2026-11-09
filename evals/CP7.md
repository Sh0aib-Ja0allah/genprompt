# CP7 (1.3.1 under J-method option D): INCOMPLETE, card-less load stopped by its spend guard

| | |
|---|---|
| Eval code | frozen at `a977724` (X1); unchanged through 01104e0 |
| Spend | **$5.1858 of $13** (re-baselines $4.6481 + CP7 card-less, interrupted, $0.5377; $7.8142 left) |
| Status | Re-baselines complete under Shoaib's X6 ruling. Every case PASSES all four gated graders 3/3 on its first run, so none escalated: 0 flips either way on both sides (X2). CP7 (candidate 2fad0fa) waits for the PE's GO |

## CP7 on 2fad0fa (GO given): card-less load INCOMPLETE (spend guard)

- `compare --cand 2fad0fa --cases slice fix redesign plan investigate --home empty --budget 0.08
  --runs 3 --max-total 0.60`.
- The guard stopped it after 13 of 15 runs at $0.5377: investigate r2 and r3 never ran.
- Cause: 1.3.1's card-less runs cost about $0.041 each against the about $0.025–0.03 the 0.60
  total assumed. With 1.3.1's card-first Step 0, a card-less run is told `card … (absent)` and
  does more work (plan $0.044–0.058, slice $0.041–0.060). My guard pair was too tight again.
- **Not graded** (a partial set is never a pass). Card-fresh and quality were not run.
- Traces: `C:/genprompt-probe/genprompt-probe-20261109-180449/` (13 jsonl, no report).
- Proposed: re-run card-less 5×3 whole with `--max-total 0.80`, about $0.62 expected, and run
  card-fresh with `--max-total 0.80` as well.

## Re-baselines (opus generator, opus judge, judge-inclusive caps)

| Side | Case | first-run cap | cost (judge) | scope | grounding | skepticism | cites-real | gates-exist | escalated | flips F→P / P→F | results |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v1.3.0 `502a723` | fix | $0.70* | $0.6613 ($0.2300) | PPP | PPP | PPP | PASS (23) | PASS (lint, start, test) | no | 0 / 0 | `2026-11-09T15-48-25Z` |
| v1.3.0 | plan | $1.00 | $1.0107 ($0.2737) | PPP | PPP | PPP | PASS (22) | PASS (lint, test) | no | 0 / 0 | `…15-52-05Z` |
| v1.3.0 | redesign | $1.10 | $0.6366 ($0.2123) | PPP | PPP | PPP | PASS (15) | PASS (lint, start, test) | no | 0 / 0 | `…15-55-11Z` |
| v1.3.0 | slice | $1.40 | $0.8267 ($0.2731) | PPP | PPP | PPP | PASS (39) | PASS (lint, test) | no | 0 / 0 | `…15-56-54Z` |
| v1.3.0 | investigate | $0.95 | $0.6868 ($0.2286) | PPP | PPP | PPP | PASS (16) | PASS (lint, start, test) | no | 0 / 0 | `…15-59-28Z` |
| v1.2.0 `d584108` | redesign | $1.10 | $0.8261 ($0.2587) | PPP | PPP | PPP | PASS (24) | PASS (lint, test) | no | 0 / 0 | `…16-01-28Z` |

\* fix ran before the X5 re-estimate, at the old $0.70 cap. Its run was complete, so it stands.

- **Every baseline verdict is PASS (3/3).** Under the opus judge, v1.3.0's redesign passes
  scope and grounding PPP. That is the case the haiku judge failed at CP6 run 7 (FFP / FPF), on
  the same release text.
- **Note on plan's cost:** $1.0107 against a $1.00 cap. The harness checks the ceiling *before*
  each run, so one run can overrun it slightly. It finished complete; for CP7, plan's first-run
  cap stays $1.00 and the overrun is noted.
- Sides: the v1.3.0 baseline is all 5 cases; v1.2.0 is redesign only (X6).
- **J5:** the debug logs hold judge request ids only, never text. `--explain` would be needed
  for a FAIL or split; none occurred.
- Spend: v1.3.0 $3.8220 (fix $0.6613 + four cases $3.1607) + v1.2.0 redesign $0.8261 =
  **$4.6481**.

## CP7 next (on GO): candidate `2fad0fa`

| Step | Expected | Caps |
|---|---|---|
| load: card-less 5×3 (X4) + card-fresh 5×3 (R2, X3), haiku | $0.90 | `--budget 0.08`, `--max-total` 0.60 (card-less) and 0.75 (card-fresh, CP6's lesson: about $0.04 a run when the card is found) |
| quality: 5 cases (J1–J2, R4 vs v1.3.0 on all, vs v1.2.0 on redesign; R3 investigate) | about $3.85 at this run's actuals | first / escalation: fix 0.95/1.55, plan 1.00/1.60, redesign 1.10/1.75, slice 1.40/2.30, investigate 0.95/1.55 |
| **CP7 expected** | **about $4.75**, leaving about $3.6 for escalations or `--explain` | |

---

## Earlier: the X5 stop (recorded)

## Re-baseline v1.3.0 (502a723): first case only

| Case | first-run cap | cost (judge) | rubric-scope | rubric-grounding | cites-real | gates-exist | escalated | flips |
|---|---|---|---|---|---|---|---|---|
| fix | $0.70 | $0.6613 ($0.2300) | PASS (PPP) | PASS (PPP) | PASS (23) | PASS (lint, start, test) | no | none either way |

- Results: `evals/results/2026-11-09T15-48-25Z`, which includes escalation.json and eval-debug.log.
- skepticism PPP; eval score 1.
- **J5: the debug log does not hold the judge's reasoning.** For the judge it records only
  `[API REQUEST] /v1/messages … source=plugin_eval_judge`: 9 request ids, no text. So
  `--explain` is the only way to get the reasoning, for gated FAILs and splits.
- The fix run cost $0.66 against its $0.70 cap. The caps in CP7-plan.md didn't include the
  judge, so they're too tight at opus judge prices.

## Re-estimate (X5), judge at about $0.23 per case

| Step | Generation | Judge | Expected |
|---|---|---|---|
| v1.3.0 fix (done) | | | $0.66 |
| v1.3.0 plan, redesign, slice, investigate | $2.20 | $0.92 | $3.12 |
| v1.2.0 (4 cases) | $2.35 | $0.92 | $3.27 |
| CP7 load (card-less + card-fresh, haiku) | $0.90 | — | $0.90 |
| CP7 quality (5 cases) | $2.62 | $1.15 | $3.77 |
| **Total, no escalation** | | | **≈ $11.72** |

- **Each escalation** is 2 generations plus 6 judge calls' worth: about $1.3–2.0. $13 − $11.72
  leaves $1.28, so **no escalation is funded on expected numbers**, and `--explain` (about
  $0.15–0.45 per explained grader) only barely.
- **Caps need the judge added.** First run about 1.4× generation + $0.30; escalation about
  2.3 × (generation + $0.23).

  | Case | first-run cap | escalation cap |
  |---|---|---|
  | fix | 0.95 | 1.55 |
  | plan | 1.00 | 1.60 |
  | redesign | 1.10 | 1.75 |
  | slice | 1.40 | 2.30 |
  | investigate | 0.95 | 1.55 |

**Options for Shoaib (none taken):**
- **(a)** Raise the cap to **about $16**. That funds two escalations plus `--explain` on one side,
  at about $11.72 + $3.5 + $0.5.
- **(b)** Keep $13. On expected numbers it covers the no-escalation path only. Any escalation
  or explain becomes a cap stop for a decision.
- **(c)** Drop the v1.2.0 re-baseline (saves about $3.27). R4 is then against v1.3.0 only, a
  Planner rule change.
- **(d)** Use a cheaper judge (sonnet) for all three sides. That's a J1 rule change before any
  further result. The fix result above would be re-run under it.
