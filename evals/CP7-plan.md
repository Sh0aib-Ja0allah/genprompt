# CP7 plan: 1.3.1 under J-method option D (rules fixed before results; nothing run)

| | |
|---|---|
| Status | **For PE and Planner review before any spend** |
| Budget | **$13 cap** (Shoaib raised it from $11) for the re-baselines of v1.3.0 and v1.2.0 plus CP7. Running total starts at $0 |
| Eval code | **frozen (X1)** at the commit that adds X1–X5, named in the report. It is the same for all three sides |
| CP7 candidate | **`2fad0fa`**, frozen (R5): A's 1.3.1 (card-first Step 0, bare tool names, `{…}` slots, F headroom; plan floor 29,794) |
| Code | evals/run.py at 5dc4c71 (`--judge-model`, debug log, `--escalate`, `--explain`; 17 tests, no spend) |
| Baselines | v1.3.0 = `502a723`; v1.2.0 = `d584108` |
| Candidate | A's 1.3.1 candidate, frozen when GO is given (R5) |

## 1. Rules

### Carried over from CP6 (evals/CP6-plan.md)

- **R1** investigate's card-less load is reported against its 40,000 B soft line, not gated.
  A1 and A5 still gate it.
- **R2** card-fresh gates C1 and C2, plus the validity rule (V1–V3: ≥ 12 of 15 runs and ≥ 2 of 3
  per case saw the card, else INVALID).
- **R3** investigate quality is absolute: all four gated graders PASS.
- **R4** quality must show no regression on the four gated graders: rubric-scope,
  rubric-grounding, cites-real, gates-exist.
- **R5** the candidate SHA is frozen; a change to PROTOCOL, guide/ or archetypes/ re-runs what it
  touches.
- **A5** stays frozen at the general rule (5a2504b).
- Stop at the first failure, INVALID or incomplete case; no remedy without Shoaib.

### New (J-method option D)

- **J1. Judge.** Every quality run passes `--judge-model claude-opus-5-5`, recorded per row in
  structural.json. 3 votes per LLM rubric, majority.
- **J2. Escalation.** One generation per case. If that run FAILS any gated grader, the case gets
  2 more generations (`--escalate`, one eval call under its own cap). Each gated grader's final
  verdict is the majority of the 3 runs' verdicts. A case that passes everything isn't re-run.
- **J3. Same procedure on every side (O1).**
  - The v1.3.0 and v1.2.0 re-baselines use exactly J1 and J2: the same judge, flags, caps policy
    and escalation trigger.
  - The flips (gated graders whose first run FAILED but whose 3-run majority PASSED) are counted
    and reported **per side**: v1.3.0, v1.2.0 and the candidate.
  - Re-sampling only FAILs leans toward PASS, so it must lean the same way on every side.
- **J4. Regression (O2).**
  - A regression is a gated grader whose final verdict is PASS in the re-baselined v1.3.0 and
    FAIL in the candidate. Likewise against the re-baselined v1.2.0, for its four cases.
  - **No CP5 or CP6 haiku verdict is ever used.**
  - investigate has no v1.2.0 case. R3 gates it absolutely; the comparison with v1.3.0 is
    reported.
- **J5. Reasoning.**
  - Every real run writes the eval's debug log (`eval-debug.log`). The first run checks whether
    it holds the judge text, and says so in the report.
  - If it doesn't, `--explain` (opus, $0.30 per call, $1.00 per side) runs only for gated LLM
    graders that FAILED or split. It explains; it never changes a verdict.
- **J6. Spend guard.** A running total against $11. Before each step: if what's left can't cover
  that step's caps, stop and report before starting it.

### Planner additions, fixed before any results

- **X1. Eval code frozen** for all three sides at the commit that adds this section: evals/run.py,
  evals/lint/ and evals/realuse/. Any change to them means re-running every side.
- **X2. Flips both ways.** escalation.json records `flipped_to_pass` (FAIL on run 1, PASS in the
  3-run majority) and `flipped_to_fail` (PASS on run 1, FAIL in the majority). Both are counted
  and reported per side.
- **X3. 1.3.1's own acceptance, gated in CP7.** Card-fresh 5×3 must show:
  - **C1 at 0 of 15**: no run, whether it saw the card or not, Reads derive.md, guide/01 or
    stack-matrix;
  - **each case's card-fresh median strictly below its card-less median** from CP7's own
    card-less probe.
  - The probe prints this as check "X3".
  - Risk, stated up front: if a case's card-less runs mostly *don't* read derive.md, its
    card-less median is just the floor. The card-fresh median then equals it (not below), and
    X3 fails that case on the measure rather than on a defect. Under 1.3.1's card-first Step 0
    a card-less run is told `card … (absent)`, so it should derive. That is what X3 tests.
- **X4. No load regression.** Each case's CP7 card-less median ≤ its v1.3.0 CP6 stored median
  + 2%, and plan ≤ 30,615 (v1.1.0):

  | Case | v1.3.0 stored median | limit |
  |---|---|---|
  | fix | 33,218 | 33,882 |
  | plan | 30,059 | 30,615 (the v1.1.0 cap is tighter than +2% = 30,660) |
  | redesign | 31,876 | 32,514 |
  | slice | 32,435 | 33,084 |
  | investigate | 34,953 | 35,652 |

- **X5. Judge cost check.** If the first quality case's judge cost is above $0.10 (2× the
  assumed $0.05), stop and re-estimate before the next case.
- **X6 (applied after the X5 stop).** The v1.2.0 re-baseline is **redesign only**, which clears
  the 1.3.0 known issue. R4 for 1.3.1 compares against the re-baselined v1.3.0 on every case,
  and against v1.2.0 on redesign only. The cap stays $13.
- **X5 stop, as recorded** (`evals/CP7.md`, e6d4fd9): the opus judge cost $0.2300 on v1.3.0 fix,
  4.6× the assumed $0.05. The debug log holds request ids only, no judge text (J5:
  `--explain` is the only source of reasoning).
- **Judge-inclusive caps, replacing §3's caps.** First run / escalation:

  | Case | first-run cap | escalation cap |
  |---|---|---|
  | fix | $0.95 | $1.55 |
  | plan | $1.00 | $1.60 |
  | redesign | $1.10 | $1.75 |
  | slice | $1.40 | $2.30 |
  | investigate | $0.95 | $1.55 |

- **Re-estimate with X6:**

  | Step | Expected |
  |---|---|
  | v1.3.0 fix (done) | $0.66 |
  | v1.3.0, the other four cases | $3.12 |
  | v1.2.0 redesign | $0.80 |
  | CP7 load | $0.90 |
  | CP7 quality | $3.77 |
  | **Total, no escalation** | **≈ $9.25** |

  That leaves about $3.75 for escalations (about $1.3–2.0 each) and `--explain`. J6 still stops
  before any step whose cap doesn't fit what's left.
- **V-a to V-d (Planner and Shoaib, after the card-less X4 FAIL, before card-fresh).**
  - **V-a.** Split card-less runs into derive.md readers and non-readers. Non-readers must meet X4,
    and the gap should be about derive.md's size. Otherwise stop.
  - **V-b.** "Wrote the card" means every deriving run wrote it at the right by-repo path and the
    card passes lint. Non-deriving runs with no card are recorded separately (the 1.3.0 bug).
  - **V-c.** Card-less doesn't trigger the §4.19 remedy. It stays armed for card-fresh plan and quality.
  - **V-d (Shoaib: GATED).** Card-fresh medians must meet the X4 limits (each case ≤ v1.3.0 stored
    median + 2%, plan ≤ 30,615). That's in addition to X3 (C1 0/15; card-fresh < card-less per case).
- **Pre-stated remedy (Planner).** If plan regresses on any gated grader in CP7, the remedy is
  to restore §4.19 to F (594595d removed it; the 821 B margin absorbs it), not a new patch.

## 2. Order

1. Re-baseline **v1.3.0**: quality on 5 cases (J1–J2).
2. Re-baseline **v1.2.0**: quality on 4 cases (no investigate).
3. Report both baselines (verdicts, votes, flips, cost) and wait for GO.
4. **CP7** on A's frozen 1.3.1 candidate:
   1. card-less load, 5 × 3 haiku runs, ≤ v1.1.0 and ≤ v1.2.0 stored load medians (R1);
   2. card-fresh 5 × 3, validity then C1/C2 (R2);
   3. quality on 5 cases (J1–J2), R4 vs both re-baselines (J4), R3 for investigate.

## 3. Cost estimate (O4)

Basis: CP6's opus generator actuals: fix $0.43, plan $0.47, redesign $0.48–0.56, slice $0.76,
investigate $0.45. v1.2.0 per CP5: $0.53, $0.51, $0.57, $0.77. The opus judge is assumed to cost
about $0.05 per case (5× haiku's $0.006–0.010); step 1's first case checks that.

**Per-case caps.** The first run is capped at about 1.4× expected. The escalation (2 runs) is
capped at about 2.3× expected, which caps the re-sample path per case.

| Case | expected (1 run) | first-run cap | escalation cap (2 runs) |
|---|---|---|---|
| fix | 0.50 | 0.70 | 1.15 |
| plan | 0.52 | 0.75 | 1.20 |
| redesign | 0.58 | 0.80 | 1.35 |
| slice | 0.80 | 1.10 | 1.85 |
| investigate | 0.50 | 0.70 | 1.15 |

**Estimates, kept separate:**

| Step | Expected, no escalation | each escalation adds |
|---|---|---|
| Re-baseline v1.3.0 (5 cases) | $2.90 | +$1.0–1.6 |
| Re-baseline v1.2.0 (4 cases) | $2.55 | +$1.0–1.6 |
| **Re-baselines subtotal** | **$5.45** | |
| CP7 load (card-less + card-fresh incl. X3, haiku) | $0.90 (CP6 actuals: card-less $0.33–0.50, card-fresh $0.49) | — |
| CP7 quality (5 cases) | $2.90 | +$1.0–1.6 |
| **CP7 subtotal** | **$3.80** | |
| `--explain` (only if the debug log lacks the reasoning) | $0–1.00 per side | — |
| **Total** | **$9.25 with no escalation** (cap $13) | |

- **With the $13 cap (was $11): expected $9.25 leaves $3.75** for two escalations plus `--explain` on one side. (Original $11 note: about one escalation at the expected $1.0–1.6, or none
  if `--explain` is used too. CP6's history suggests about one gated FAIL per 5-case pass, so on
  expected numbers the plan fits with **one** escalation across all three sides, and two only if
  they're cheap cases.)
- **Worst case is guarded, not funded.**
  - If every first run hits its cap: re-baselines $4.05 + $3.35, CP7 load about $1.20, CP7
    quality $4.05. That's $12.65 with no escalation, which J6 would stop before CP7's quality step.
  - J6 always checks before starting: the next step's caps must fit what's left.
- Options, Shoaib's call:
  - **(a)** keep $11 and accept that a second escalation or a costly side may stop CP7 for a cap
    decision;
  - **(b)** raise the cap to **$13**, which funds two escalations plus `--explain` on one side;
  - **(c)** skip the v1.2.0 re-baseline (saves $2.55). R4 is then against v1.3.0 only, a rule
    change for the Planner.

## 4. What the report gives per side

- Per case: the first-run gated verdicts with their opus votes, whether it escalated, the 3-run
  verdicts and the final majority.
- Flips counted (J3) and the cost.
- Whether the debug log held the judge's reasoning (J5), and `--explain` answers if it was run.
