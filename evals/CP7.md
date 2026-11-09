# CP7 (1.3.1 under J-method option D): STOPPED, card-less load FAILS X4 (and plan fails the v1.1.0 load gate)

| | |
|---|---|
| Eval code | frozen at `a977724` (X1); unchanged through 01104e0 |
| Spend | **$5.7298 of $13** (re-baselines $4.6481 + CP7 card-less interrupted $0.5377 + card-less re-run $0.5440; $7.2702 left) |
| Status | Re-baselines complete under Shoaib's X6 ruling. Every case PASSES all four gated graders 3/3 on its first run, so none escalated: 0 flips either way on both sides (X2). CP7 (candidate 2fad0fa) waits for the PE's GO |

## P-c: real-home / username grep over every CP7 output (free)

- **Scope:** probe dirs 180449 (interrupted card-less), 184529 (card-less), 212154 (card-fresh) and
  onetime (ii).
- **Sources:**
  - every emitted prompt, as the archive parts JSON `prompt` (49 files);
  - every card (15 seeded, plus 1 written by (ii));
  - the (ii) archived prompt;
  - every run's final message (TARGET LOCK + prompt, 47 runs).
- **Patterns:** `C:\…`, `C:/…` and `/c/…` forms of the real home, plus the username.

| Where | slice | fix | redesign | plan | investigate |
|---|---|---|---|---|---|
| emitted prompt (parts) | 0/10 | 0/8 | 0/8 | 0/10 | **4/8** (AUTONOMY write area: 180449 r1, 184529 r1, 212154 r1, r2) |
| cards (seeded + (ii)) | 0 | 0 | 0 | 0 (+ (ii) card 0, (ii) archive 0) | 0 |
| final message, outside the prompt | **1** (184529 r3) | 0 | 0 | **1** (180449 r2) | **1** (184529 r3) |

- Every hit is the `C:/` form plus the username. There are no `C:\` or `/c/` forms.
- **The hits outside investigate are not in any emitted prompt or card.** All three are on the TARGET
  LOCK's `Ancestors` line, inside the lock's fence, which the user sees and the worker doesn't. For example:
  `user-level: unreadable (<REALHOME>/.claude/CLAUDE.md is in a permission-denied directory)`.
  This follows the lock and card templates (`user-level: <path | none>`). Here it names the denied
  path instead of `none`/`unreadable` alone.
- **So the emitted-prompt leak is investigate only:** the AUTONOMY write area, in 4 of 8 investigate
  prompts across the three probes.
- The lock line is a separate, smaller question for A:
  - it's shown to the person whose home it is;
  - but the card template has the same `user-level: <path>` slot, and a card written in real use could
    store that path. In CP7, both written cards said `unreadable` with no path.

## P-f: raw-text grep over everything stored in every sandbox home (free)

- **Scope:** all files under `homes/` in 180449, 184529, 212154 and onetime, searched as raw text, not
  only the `prompt` field.
- **Patterns:** the same as P-c.
- **Kinds found:** shard, card, archived prompt and parts. No file sits outside these kinds.
- **History:** genprompt has no separate history store in these homes. The shard *is* the history.

| Case | parts (tmp/*.json) | cards | archived prompt | shard (*.tsv) |
|---|---|---|---|---|
| slice | **1/10** | 0/3 | — | — |
| fix | 0/8 | 0/3 | — | — |
| redesign | 0/8 | 0/3 | — | — |
| plan (incl. onetime) | 0/10 | 0/4 | 0/1 | 0/1 |
| investigate | **4/8** (the AUTONOMY leak, as in P-c) | 0/3 | — | — |

- **New hit outside the investigate prompt: slice, 184529 r3, parts file, field `grounding`**
  (not `prompt`, which P-c checked):
  `… the user-level <REALHOME>/.claude/CLAUDE.md is in a denied directory (unreadable) …`.
- This is the same user-level Ancestors content as the P-c lock-line hits. Here it sits in the
  "Grounded by" paragraph that the parts file carries.
- A non-dry-run archive would store that paragraph with the prompt. So in real use, this kind of line
  ends up in the user's own archive, and it's the 1.4.0 backlog item (P-c ruling) in a third place.
- All hits are the `C:/` form plus the username; no `C:\` or `/c/`.

**Ruling on P-c (PE): A's fix is not widened for the lock's Ancestors line.**
- The lock is shown only to the home's own user, and the card is stored in that user's own home.
- Changing it means editing shared text (the lock or card template). Under R5 that would void the other
  cases' load results.
- **1.4.0 backlog:** "user-level reported as present / unreadable / none, never a path, in lock and card".

## Shoaib's rulings on card-fresh, and what's next

- **Redesign X3: stated, not a FAIL.** It's the pre-stated artefact: the card-less median is the floor
  because of the (i) skip-derive runs. V-d passes for redesign.
- **Investigate A5: a product fix.** The leak is **in both investigate runs, r1 and r2**. A5's Grep only
  surfaced r2. A is changing X-investigate so the scratch area is a worker variable, never a generator
  path. That gives a new candidate (R5).
- **On the merged SHA:** if slice, fix, redesign and plan's include sets are unchanged (md5, checked by
  the PE), their card-less and card-fresh results stand. Then investigate re-runs card-less 3× and
  card-fresh 3× (X3, V-d, A5), then quality on all 5 cases.

**Guards and budget, prepared before the run** (running total $6.3602 of $13; $6.6398 left):

| Step | Command shape | per-run cap | `--max-total` | expected (CP7 actuals) |
|---|---|---|---|---|
| investigate card-less 3× | `compare --cand <SHA> --cases investigate --home empty --runs 3` | $0.08 | **$0.30** (worst case 3 × 0.08 = 0.24 fits) | $0.13 |
| investigate card-fresh 3× | same with `--home card --cardless investigate=<new card-less median>` | $0.08 | **$0.30** | $0.14 |
| quality, 5 cases (J1–J2) | scratch rb_driver, opus generator + judge, `--escalate`, plugin = a temp worktree at `<SHA>` | first / escalation per case (below) | J6 before every case | $3.83 (the re-baselines' actuals: slice 0.83, redesign 0.64, plan 1.01, fix 0.66, investigate 0.69) |
| **Expected total** | | | | **$4.10, finishing at about $10.46 of $13**; about $2.54 left, enough for **one** escalation |

- **Quality order:** largest caps first, so J6 is least likely to block a case late:
  **slice** (1.40/2.30) → **redesign** (1.10/1.75) → **plan** (1.00/1.60) → **fix** (0.95/1.55) →
  **investigate** (0.95/1.55).
- **J6 walk.** With load at the worst case $0.60, the total is $6.96 and $6.04 is left. Each case's
  first + escalation cap fits when its turn comes, at expected costs with no escalation: slice 3.70 ≤ 6.04,
  redesign 2.85 ≤ 5.21, plan 2.60 ≤ 4.57, fix 2.50 ≤ 3.56, investigate 2.50 ≤ 2.90.
  - With load at its expected $0.27, each check has $0.33 more room.
  - An escalation early on (about $1.3–2.0) would make J6 stop before investigate, or before fix and
    investigate. That's a cap stop for Shoaib, not an overrun.
- **Gates.** R4 / J4 against the re-baselined v1.3.0 on all 5, and against v1.2.0 on redesign. R3 for
  investigate. `--explain` only for a gated FAIL or a split. The §4.19 remedy stays armed for plan (V-c).

## CP7 card-fresh 5×3 (`--max-total 1.00`): **FAIL: X3 (redesign) and A5 (investigate r2). STOPPED**

`C:/genprompt-probe/genprompt-probe-20261109-212154/`, **$0.5775**, haiku. Running total: **$6.3602 of $13**.

| Case | card-fresh per-run rule bytes | median | card-less median | X3 (strictly <) | V-d limit (X4) | V-d |
|---|---|---|---|---|---|---|
| slice | 32,458 ×3 | 32,458 | 37,679 | PASS | 33,084 | PASS |
| fix | 33,241 ×3 | 33,241 | 38,462 | PASS | 33,882 | PASS |
| redesign | 31,899 ×3 | 31,899 | 31,899 | **FAIL (equal)** | 32,514 | PASS |
| plan | 29,794 ×3 | 29,794 | 35,015 | PASS | 30,615 | PASS |
| investigate | 35,016 ×3 | 35,016 | 40,237 | PASS | 35,652 | PASS |

- Validity: VALID, 15/15 runs saw the card. **C1 PASS** (0/15 forbidden Reads; X3's all-runs part is
  0/15 too). **C2 PASS. A1 PASS.** V-d (by hand, not in the frozen probe): **PASS on all five**. Every
  card-fresh run sits exactly on its case's floor.
- **X3 FAIL, redesign.** This is the risk stated up front in the plan. Redesign's card-less median is its
  floor, because 2 of its 3 card-less runs were known-issue (i) skip-derive runs. So card-fresh equals it
  rather than beating it. The candidate is at its floor; the comparison side was depressed by (i).
- **A5 FAIL, investigate r2.** Two Greps of the run's *own* sandbox parts file printed the real home.
  The cause is in the generated prompt itself: its AUTONOMY line names a write area under the real
  user's home.
  - r2: `<REALHOME>/AppData/Local/Temp/claude/<id>/<session>/scratchpad/investigate-subtotal/`, which is
    the generator's own Claude Code scratchpad, lifted from its environment.
  - r1 has the same leak (`<REALHOME>/AppData/Local/Temp/ledgerlite-investigate/`). Only r2's Grep
    happened to surface it, so A5 caught one of two.
  - Nothing outside the probe root was read and nothing was written outside the sandbox. But the
    emitted prompt carries a real user path, a privacy defect in the investigate output.
- Quality was **not** run.

## Ruling (ii): one-time evidence, standalone (outside the frozen probe): **PASS**

Driver: the scratch `onetime.py`, which imports evals/realuse/run.py's helpers read-only and doesn't
edit them (X1 holds). Setup: 2fad0fa staged as gp-cand, the ledgerlite fixture, and one fresh sandbox
GENPROMPT_HOME with no card. The request was plan without `--dry-run` (with `--go`), run twice in the
same home on haiku. Spend: **$0.0529** (run 1 $0.0363, run 2 $0.0165). Traces:
`C:/genprompt-probe/genprompt-probe-onetime-20261109-211753/`.

| | run 1 (no card) | run 2 (same home) |
|---|---|---|
| `--where` card | absent | present |
| derive.md read | yes | **no** |
| rule bytes | 35,015 | **29,794** (the floor; ≤ X4 plan 30,615) |
| card | **written** at `homes/onetime/generated-prompts/by-repo/fixture.profile.md`, plus shard `fixture.tsv` and the archived prompt | reused |
| card lint (doctor.py `check_profiles`, GENPROMPT_HOME = the sandbox) | **0 ERROR, 0 WARN**: all §2.9 keys, key = filename, stamps `package.json@9c672ba ; CLAUDE.md@9c672ba` | — |
| Stack line (honesty) | `card 0d, fresh (new)`, and a card was really written: **honest** | `card 0d, stamps fresh (package.json@9c672ba, CLAUDE.md@9c672ba both match …)`, with no "new": **honest** |

- So the +5,221 B is paid once per repo. The next run in the same home reads no derive rules.
- Run 1's real `archive.py` write is flagged under the probe's A5 rule (it allows only `--where` or
  `--dry-run`). That's expected for a non-dry-run request. This run sits outside CP7's gates.
- (i) Per the ruling, the 4/15 skip-derive runs are a stated 1.3.1 known issue, not a blocker. 3 of the
  4 reasoned about `--dry-run`. B adds it to the notes.
- Spend: $5.7298 + $0.0529 = **$5.7827 of $13**.

## Planner V-a / V-b (free, traces of 184529): V-a CLEAN, **V-b NOT CLEAN → STOPPED**

**V-a: derive-readers vs non-readers.** The only extra rule Read in any run is derive.md.

| Case | non-readers (rule bytes) | readers (rule bytes) | gap | X4 limit | non-readers vs X4 |
|---|---|---|---|---|---|
| slice | none (static floor 32,458) | r1–r3 37,679 | 5,221 | 33,084 | no runs; floor would pass |
| fix | none (static floor 33,241) | r1–r3 38,462 | 5,221 | 33,882 | no runs; floor would pass |
| redesign | r1, r2 31,899 | r3 37,120 | 5,221 | 32,514 | PASS |
| plan | r1 29,794 | r2, r3 35,015 | 5,221 | 30,615 | PASS |
| investigate | r1 35,016 | r2, r3 40,237 | 5,221 | 35,652 | PASS |

The gap is exactly derive.md's 5,221 B in every case, so nothing else grows. Caveat: slice and fix
have no non-reader runs, so for those two the comparison rests on the static floor.

**V-b: card written and linted?** No. 0 of 11 deriving runs wrote the card (see the card-write check
below): every probe request is `--dry-run`, so there's no card to lint.

**V-b: the 4 non-deriving runs.** All four had no card: Step 0's `--where` printed
`…/by-repo/fixture.profile.md (absent)` in each. All four still skipped derive.md. **That is the 1.3.0
bug (no card, no derive), still present in 4 of 15 runs:**

| Run | Stack-line card status the run emitted |
|---|---|
| investigate r1 | `card new (not written: --dry-run)`, a "new card" without reading derive.md |
| plan r1 | `card new (dry run writes none)`, same |
| redesign r1 | `card none (not derived this run)`, skipped deriving openly |
| redesign r2 | `card new, not written (--dry-run)`, a "new card" without reading derive.md |

So the X4 FAIL's cause is real (derive.md is read when a card is absent), but 1.3.1 doesn't apply it
consistently. In 27% of card-less runs it claims or skips a card without the derive rules. This is a
product finding, and it's separate from the load gate.

**V-c** (recorded): card-less doesn't trigger the §4.19 remedy. It stays armed for card-fresh plan
and for quality. **V-d** is written into CP7-plan.md. Card-fresh and quality were not run. Spend
is unchanged at $5.7298.

## Card-write check (Shoaib: "verify, then continue"; free, traces of 184529): **STOPPED, not shown one-time**

| | count |
|---|---|
| runs that Read derive.md | 11 of 15 |
| of those, runs that Wrote or Edited `…/generated-prompts/by-repo/<key>.profile.md` | **0 of 11** (no Write, Edit or shell write naming profile.md in any of the 15 traces) |
| of those, attempts blocked by the probe's tool permissions | **0** (no permission denial names profile.md) |
| `*.profile.md` files present in any sandbox home afterwards | **0** |
| runs whose request ends in `--go --dry-run` | **15 of 15** (every REQUESTS entry in evals/realuse/run.py) |

- Writes into the sandbox home were permitted: `--allowedTools Write(<homes>/**) Edit(<homes>/**)`.
  The same runs did write their archive JSON to `<home>/tmp/` (14 files).
- So the card wasn't written because every probe request is `--dry-run`, and PROTOCOL.md
  ("`--dry-run` never writes it") forbids it. That's correct behaviour. It wasn't a permission block.
- Under the ruling's own branch ("If they didn't write it: stop and report"), I stopped. The probe can't
  show the cost is one-time: by construction it never runs a card-writing request. That rests on
  PROTOCOL.md's text alone.
- Card-fresh and quality were not run. Spend is unchanged at $5.7298.

## CP7 card-less re-run (`--max-total 1.00`): complete; **FAIL X4**

`C:/genprompt-probe/genprompt-probe-20261109-184529/`, $0.5440, A1 PASS, A5 PASS.

| Case | floor | per-run rule bytes | median | X4 limit (v1.3.0 + 2%) | X4 | v1.1.0 / v1.2.0 load gate |
|---|---|---|---|---|---|---|
| slice | 32,458 | 37,679 ×3 | 37,679 | 33,084 | **FAIL** | pass (62,894 / 61,230) |
| fix | 33,241 | 38,462 ×3 | 38,462 | 33,882 | **FAIL** | pass (53,561 / 43,475) |
| redesign | 31,899 | 31,899 31,899 37,120 | 31,899 | 32,514 | PASS | pass |
| plan | 29,794 | 29,794 35,015 35,015 | 35,015 | 30,615 | **FAIL** | **FAIL vs v1.1.0 30,615** (pass vs v1.2.0 41,367) |
| investigate | 35,016 | 35,016 40,237 40,237 | 40,237 | 35,652 | **FAIL** | (R1: over the 40,000 soft line) |

**Diagnosis (no remedy applied):**
- The floors are within the expected range: plan's 29,794 is *lower* than v1.3.0's 30,059.
- The growth is entirely `derive.md` (5,221 B): read in 11 of 15 runs (slice 3/3, fix 3/3,
  plan 2/3, investigate 2/3, redesign 1/3). In v1.3.0's CP6 card-less runs it was 0–1 of 3
  per case.
- This is 1.3.1's intended behaviour. The card-first Step 0 prints `card … (absent)` and a
  card-less run then derives. X3 (card-fresh strictly below card-less) depends on exactly that.
- **X3 and X4 conflict by construction.**
  - X4 caps card-less at v1.3.0's median + 2%, and those medians were floor medians: the runs
    mostly skipped deriving.
  - So the change that makes X3 passable makes X4 fail. Card-less medians now include
    derive.md, while card-fresh (with a card) should not.
- **Not a regression for a user with a card.** That's card-fresh, not yet run. It is a real cost
  increase on first use in a repo: no card means 1.3.1 always derives, where 1.3.0 often
  skipped it.
- Card-fresh and quality were not run.

**Options for Shoaib (none taken):**
1. **Planner ruling on the load gate for 1.3.1:** compare like with like, e.g. X4 applied to
   the card-fresh medians (the steady state with a card), while the card-less median is gated
   at floor + derive.md, so the first-use cost is stated rather than capped at the old
   skip-derive median. That's a rule change after a result.
2. **Accept the X4 FAIL as stated** (first use in a repo costs about +5.2 KB) and continue to
   card-fresh and quality.
3. **A product change:** let card-less runs skip derive.md when the request doesn't need the
   full profile. That's a new candidate, and it undoes the point of card-first.

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
