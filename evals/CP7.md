# CP7 (1.3.1 under J-method option D): STOPPED at X5 during the v1.3.0 re-baseline

| | |
|---|---|
| Eval code | frozen at `a977724` (X1) |
| Spend | **$0.6613 of $13** |
| Status | **X5 stop: the opus judge cost $0.2300 on the first case, 4.6× the assumed $0.05.** Re-estimate below; nothing else run |

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
