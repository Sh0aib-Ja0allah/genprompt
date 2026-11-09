# CP6: 1.3.0 release check: COMPLETE, ships at frozen da5997e with two stated known issues

## Summary

| | |
|---|---|
| Frozen candidate | **`da5997e`** (R5). It is fb17b8c plus: A's F-plan naming fix; B's Step 0 fix (`--where` alone); A's restore of §4.6/§4.13 to L and A, with L's `[UNVERIFIED]` bullet and bare tool names; A's OUT OF SCOPE line in F; A's bare tool names in A, D and X, with A's missing-input wording |
| Total spend | **$7.7087 of the $9.50 cap** (Shoaib raised it $6.25 → $7.50 → $8.50 → $9.50). Itemised in the run sections below. $1.7913 unspent |
| Rules | `evals/CP6-plan.md`: R1–R5, the validity rule with V1–V3, and the A5 general rule with N1 (frozen at 5a2504b) |
| Not run | D1–D6, the manual dispatch checks, are deferred until after 1.3.0 (Shoaib). `--send` and `--from` ship marked experimental |

**Load (haiku, real-use probe).** A result carries over from an earlier candidate only when that
case's whole @-include set is byte-identical to `da5997e` (PE's md5 checks) or the ruling says
its Step 0–2 text is unchanged.

| Gate | Result | Where |
|---|---|---|
| Isolation (13 checks incl. real-home ls/head/cd under the shim grant) | **PASS** | run 2; probe permissions unchanged since |
| Card-less medians ≤ v1.1.0 and ≤ v1.2.0 | **PASS**: fix 33,218 · plan 30,059 (556 B under v1.1.0) · redesign 31,876 · slice 32,435 | fix run 5, plan run 6, the other two run 7 |
| investigate card-less (R1, reported) | 34,953, under the 40,000 soft line, so no CHANGELOG note | run 7 |
| Card-fresh validity (V1–V3) | **VALID**: all 15 of 15 runs saw the card | run 4 re-run (c8edb15) |
| C2 (card-fresh ≤ card-less + card) | **PASS** | run 4 |
| **C1 (no derive.md read in a card-fresh run)** | **FAIL, stated:** 3 of 15 runs read derive.md *before* the card. The medians are unaffected | run 4 |
| A1 (no Read of an @-included file) | PASS in every run | all |
| A5 (isolation, frozen general rule) | PASS in every graded run | all |

**Quality (opus-5-5, plugin eval, judge = CLI default haiku, rubrics identical to CP5's):**

| Case | Gate | Result | Votes (grounding / scope) | Where |
|---|---|---|---|---|
| fix | R4 vs CP5 | **PASS** | PPP / FFF (CP5 PPP / FPF) | run 5 (94f259e; L set identical at da5997e) |
| plan | R4 vs CP5 | **PASS** | PPP / PPP | run 6 (6c3e60a; F set identical at da5997e) |
| **redesign** | R4 vs CP5 | **FAIL, stated** | FFP / FPF (CP5 PPP / PPP) | run 7 (da5997e) |
| slice | R4 vs CP5 | **PASS** | PPF / PPP (CP5 PPP / PPF) | run 7 |
| investigate | R3 (absolute) | **PASS**: all four gated graders PASS | PPF / PPF | run 7 |

cites-real and gates-exist PASS in every case.

**Shoaib's rulings, as recorded:**
1. **C1: ship with it stated.** 3 of 15 card-fresh runs read derive.md before reading the card,
   an ordering lapse in Step 2. The medians are unaffected and the card was used once read. The
   card-first ordering fix goes to **1.3.1**.
2. **Redesign's R4 FAIL: ship with it stated.** It is recorded as a FAIL, with no re-grade and
   no re-run.
   - Hand check of the failing output (`evals/results/2026-11-09T15-08-23Z`): every cited path
     and `path:line` is in the rubric's file list and in range. Every code claim holds against the
     fixture (exit-code order, `--currency` with no value, the uncaught RangeError, lint's scope,
     the 6-test baseline, the CLAUDE.md branch prefixes).
   - The earlier trigger is gone: no `tools/archive.py`, and no `missing.json`.
   - The haiku judge's redesign vote history:
     - grounding: CP5 PPP, CP6a-2 PPP, run 6 FPF, run 7 FFP;
     - scope: CP5 PPP, CP6a-2 PPP, run 6 PPP, run 7 FPF.
   - The best explanation is judge variance at the 2-of-3 margin. That is inference: the judge's
     reasoning isn't stored.
3. Gate and probe rulings along the way (CP6-plan.md):
   - the probe mirrors the shims' Bash grant;
   - A5 became a general rule plus N1, then was frozen;
   - the validity rule and V1–V5 were added;
   - investigate is R1-reported;
   - J1: the same judge and rubrics as CP5.

**Fixes CP6 drove into the candidate:**
- Step 0 runs `--where` alone (B).
- §4.6/§4.13 restored to L and A, which E-09 had cut.
- An OUT OF SCOPE line in F.
- Bare genprompt tool names in L, A, D and X.
- F, B, N and P name their doc by `PROFILE.docnaming`.

**Not gated, reported:**
- investigate: no-placeholders FAIL. `<does X>`, `<file:line>`, `<step>` and `<what the user
  sees>` are format slots in the worker's report template; doctor rates them WARN.
- investigate: one 103-character line.
- fix (run 5): line-length FAIL at 101 characters.

Quality results: `evals/results/2026-11-09T14-08-53Z` (fix), `…14-34-55Z` (plan), `…15-08-23Z`
(redesign), `…15-23-02Z` (slice), `…15-27-13Z` (investigate).

### Run 7, continued (after the "finish and ship" ruling)

| Case | cap | cost | rubric-scope | rubric-grounding | cites-real | gates-exist | others |
|---|---|---|---|---|---|---|---|
| slice | $1.29 | $0.7634 | PASS (PPP); CP5 PASS (PPF) | PASS (PPF); CP5 PPP | PASS (37; CP5 53) | PASS (lint, test) | eval score 1; skepticism PPP; line-length PASS; archive-valid 8/0/0 |
| investigate | $1.19 | $0.4490 | PASS (PPF) | PASS (PPF) | PASS (15) | PASS (lint, start, test) | R3: all four PASS; eval score 1; skepticism PPP; no-placeholders FAIL (report-template slots); line-length FAIL (L62 = 103); archive-valid 6/2/0 |

Run 7 total: $0.8024 + slice $0.7634 + investigate $0.4490 = $2.0148. CP6 total: $6.4963 +
$0.7634 + $0.4490 = **$7.7087**.

Run 7's earlier total line, kept for the itemisation:
Total CP6 spend: $5.6939 through run 6 (itemised below) + run 7 card-less $0.3267 + redesign
$0.4757 = **$6.4963** of the $9.50 cap ($3.0037 left).

## Run 7: candidate da5997e (INCOMPLETE: quality FAIL at redesign)

| | |
|---|---|
| Candidate | `da5997e`, **frozen** (R5): 6c3e60a plus A's d587b33 (bare tool names in A, D and X; A describes missing inputs as "a path that does not exist"). fix's and plan's full @-include sets are md5-identical to 6c3e60a (PE), so their PASSes stand |
| Floors | redesign 31,876 · slice 32,435 · investigate 34,953 (fix 33,218 and plan 30,059 unchanged) |
| Cost | card-less $0.3267 + redesign $0.4757 = **$0.8024** |
| Status | **INCOMPLETE, R4 FAIL at redesign: rubric-grounding FFP and rubric-scope FPF, both PPP at CP5.** slice and investigate were not run |

**Card-less (redesign, slice, investigate, 3 runs each): PASS.**
- Medians: redesign 31,876 (≤ v1.2.0's 39,314); slice 32,435 (≤ 61,230; 1 of 3 runs read
  derive.md); investigate 34,953 (under the R1 soft line).
- A1 PASS, A5 PASS.
- Trace: `C:/genprompt-probe/genprompt-probe-20261109-164329/`.

**Quality, redesign** (cap $1.19, cost $0.4757; `evals/results/2026-11-09T15-08-23Z`; rubric hashes
equal CP5):

| Grader | Run 7 | CP5 |
|---|---|---|
| rubric-grounding | **FAIL (F F P)** | PASS (P P P) |
| rubric-scope | **FAIL (F P F)** | PASS (P P P) |
| cites-real | PASS (15) | PASS (17) |
| gates-exist | PASS (lint, test) | PASS |
| skepticism | PPP | PPP |
| eval score | 0.8 | 1 |
| line-length | PASS | FAIL |
| archive-valid | 8/0/0 | 7/1/0 |

**What I checked offline (no spend):** A's fix took effect: the output names no
`tools/archive.py` and no `missing.json` (it says "a path that does not exist"). Every cited
path and `path:line` is in the rubric's file list and in range:
- src/cli.js:9–31, :10, :11, :15, :25–29;
- invoice.js:7, :14, :22;
- package.json:6–9;
- scripts/lint.js:9 and :16;
- test/invoice.test.js:18.

Its code claims hold against the fixture:
- the exit-code order (no file → 2, unknown flag → 2, read error, bad JSON and missing lines → 1);
- `--currency` with no value prints `undefined`;
- the uncaught RangeError from invoice.js:7 and :22;
- lint scans only the top level of src/ (lint.js:9) and bans console.log there (:16);
- the 6-test baseline;
- CLAUDE.md:6's `feat/`/`fix/` prefixes.

Its out-of-scope block names src/invoice.js (with the :14 defect), src/format.js, src/index.js and
S-02 `--csv`. The one wording the scope rubric could catch ("FAIL if it lets the worker …
change output and exit codes") is the stop-list entry "Any output or exit-code change: needs my
yes on the plan". But CP5's redesign had the same kind of entry ("approve a behaviour change")
and scored PPP.

**Best explanation:** judge variance. I can find no citation or claim error, and both failures
are at the 2-of-3 margin. Across the stored redesign runs the haiku judge has given:
- grounding: CP5 PPP, CP6a-2 PPP, run 6 FPF, run 7 FFP;
- scope: CP5 PPP, CP6a-2 PPP, run 6 PPP, run 7 FPF.

That is inference: the judge's reasoning isn't stored.

**Options for Shoaib (none taken):**
1. A Planner ruling on the judge for R4, e.g. `--judge-model` set to a stronger model, or more
   votes per rubric. That's a rule change, so earlier verdicts would need re-grading under it.
2. One redesign re-run (about $0.48) to test variance. A re-run needs his OK.
3. Accept the FAIL as recorded.

Left after run 7: $3.0037. slice ($0.95) and investigate ($0.85) are expected at about $1.80.

Run 6's total line, kept for the itemisation:
Total CP6 spend: runs 1–5 and the extras $4.5788 (itemised in run 5 below) + run 6 card-less
$0.0853 + plan $0.4672 + redesign $0.5626 = **$5.6939** of the $9.50 cap ($3.8061 left).

## Run 6: candidate 6c3e60a (INCOMPLETE: quality FAIL at redesign, R4 rubric-grounding)

| | |
|---|---|
| Candidate | `6c3e60a`, **frozen** (R5): 94f259e plus A's 9ae303b (the F template line "OUT OF SCOPE (do not plan or start): …"). Only archetypes/F-plan.md and the CHANGELOG changed |
| Floors (S2) | **plan 30,059** (556 B under v1.1.0's 30,615) · fix 33,218 · redesign 31,559 · slice 32,307 · investigate 34,825. All but plan are unchanged from 94f259e |
| Stands from earlier runs | fix's R4 PASS (run 5): everything fix loads is byte-identical to 94f259e (S1, PE's md5 check). Card-fresh, and the slice and investigate loads, stand from run 4 |
| Cost | card-less plan $0.0853 + plan $0.4672 + redesign $0.5626 = **$1.1151** |
| Status | **INCOMPLETE, R4 FAIL at redesign (rubric-grounding PASS → FAIL).** slice and investigate were not run |

### Step 1: card-less plan: PASS ($0.0853)

Per-run rule bytes 30,059 · 35,280 · 30,059, so the median is **30,059**: 556 B under v1.1.0
and under v1.2.0's 41,367. derive.md was read in 1 of 3 runs. A1 PASS, A5 PASS.
Trace: `C:/genprompt-probe/genprompt-probe-20261109-162748/`.

### Step 2: quality (vs CP5 `2026-11-08T19-07-58Z`; rubric hashes equal per case)

| Case | cap | cost | rubric-scope | rubric-grounding | cites-real | gates-exist | others |
|---|---|---|---|---|---|---|---|
| plan | $1.05 | $0.4672 | **PASS (PPP)**; CP5 PPP | PASS (PPP); CP5 PPP | PASS (21; CP5 20) | PASS (lint, test) | eval score 1 (CP5 1); skepticism PPP; line-length PASS; no-placeholders PASS; archive-valid 8/0/0 |
| redesign | $1.19 | $0.5626 | PASS (PPP); CP5 PPP | **FAIL (FPF); CP5 PASS (PPP): REGRESSION** | PASS (23; CP5 17) | PASS (lint, test) | eval score 0.9 (CP5 1); skepticism PPP; line-length PASS; archive-valid 8/0/0 |

- **plan passes R4.** A's OUT OF SCOPE line cured the scope regression (FFF → PPP).
- **redesign fails R4 on rubric-grounding** (2 of 3 FAIL votes), so CP6 stops. slice and
  investigate were not run. Results: `evals/results/2026-11-09T14-34-55Z` (plan),
  `…14-37-07Z` (redesign).

**Why redesign's grounding failed: offline, no spend, inference.** The redesign grounding
rubric is the same shared text as fix's: FAIL if the response "cites a file that is not in the
list" of 13 workspace files. Compared with CP5 (PPP) and CP6a-2 (PPP), the new redesign output
has two names outside that list that the older ones don't:
- **`tools/archive.py`**, in the closing advice: "run `python3 tools/archive.py --where`
  yourself". That is the same flaw that took fix to FFF in run 4. A's 2b146ba told **L** to name
  genprompt tools bare. It restored §4.6 and §4.13 to A but didn't add the bare-name rule to A
  (archetypes/A-redesign.md changed by 2 lines, all for §4.6/§4.13). CP5 and CP6a-2 wrote bare
  `archive.py`.
- **`missing.json`**, in the behaviour matrix: "g) missing.json", a deliberately absent input
  for the CLI's cannot-read path. That's legitimate test design, but it reads as a citation of a
  file that doesn't exist. CP5 and CP6a-2 didn't use a named missing file.
- Every other path and `path:line` is in the list and within range: cli.js:9–37, invoice.js:6–14,
  format.js:3, package.json:6, scripts/lint.js:9 and :16, test/invoice.test.js:18.
  `test/cli.test.js` is a file the prompt asks the worker to create, as at CP5.
- With 2 of 3 votes FAIL, this is likely the same haiku reading as fix's. `tools/archive.py`
  is the stronger trigger, since it alone took fix from PPP to FFF.

**Options for Shoaib (none taken):**
1. A extends the bare-tool-name rule from L to A (and, to avoid a third round, to D-slice and
   X-investigate, the cases not run yet). The line is tiny; check the floors. That's a new
   candidate: R5 for the touched cases means card-less redesign (plus slice and investigate if
   touched), then quality on redesign, slice and investigate. The PASSes for fix and plan stand
   if L and F are byte-identical.
2. Optionally the matrix example too: a missing input described as "a path that does not
   exist", not a filename. That's a wording choice for A.
3. A Planner ruling on the haiku judge, which is a rule change.

Run 5's total line, kept for the itemisation:
Total CP6 spend: run 1 $0.5596 + V4 trace $0.0047 + run 2 $0.3228 + run 3 $0.6173 + replay
$0.0169 + run 4 card-less $0.4977 + run 4 card-fresh (interrupted) $0.4877 + run 4 card-fresh
re-run $0.4948 + run 4 quality fix $0.4492 + run 5 card-less $0.2262 + run 5 quality fix
$0.4290 + plan $0.4729 = **$4.5788** of the $9.50 cap (raised from $6.25 to $7.50, $8.50 and
$9.50 by Shoaib; $4.9212 left).

## Run 5: candidate 94f259e (INCOMPLETE: quality FAIL at plan, R4 rubric-scope)

| | |
|---|---|
| Candidate | `94f259e`, **frozen** (R5): c8edb15 plus A's 2b146ba (§4.6 and §4.13 restored to L and A, the L `[UNVERIFIED]` bullet, genprompt tools named bare). Floors measured: fix 33,218 · redesign 31,559 · plan 29,983 · slice 32,307 · investigate 34,825 |
| Scope | card-less for fix and redesign only (Step 0–2 text unchanged, so card-fresh and the other load results stand from run 4), then quality on all 5 |
| Judge (J1) | the same as CP5: `--judge-model` never set, so the CLI default haiku on Claude Code 2.1.318 both times. The rubric files are unchanged since CP5 (`git diff 483d021 94f259e`), and the per-case rubric hashes in the results match CP5's |
| Cost | card-less $0.2262 + fix $0.4290 + plan $0.4729 = **$1.1281** |
| Status | **INCOMPLETE, R4 FAIL at plan (rubric-scope PASS → FAIL).** redesign, slice and investigate were not run |

### Step 1: card-less, fix and redesign: PASS ($0.2262)

| Case | per-run rule bytes | median | v1.1.0 | v1.2.0 |
|---|---|---|---|---|
| fix | 38,439 33,218 33,218 | 33,218 | 53,561 | 43,475 |
| redesign | 36,780 36,780 31,559 | 36,780 (2,534 B under v1.2.0) | 53,481 | 39,314 |

A1 PASS, A5 PASS (frozen A5). redesign read derive.md in 2 of 3 runs, fix in 1.
Trace: `C:/genprompt-probe/genprompt-probe-20261109-155300/`.

### Step 2: quality (opus-5-5, plugin eval at 94f259e, vs CP5 `2026-11-08T19-07-58Z`)

Each case's cap is the lower of its ~1.4× cap and $9.50 minus the running total.

| Case | cap | cost | rubric-scope | rubric-grounding | cites-real | gates-exist | others |
|---|---|---|---|---|---|---|---|
| fix | $0.77 | $0.4290 | FAIL (FFF); CP5 FAIL (FPF): no regression | **PASS (PPP)**; CP5 PPP | PASS (26; CP5 22) | PASS (lint, start, test) | eval score 0.9 (CP5 0.9); skepticism PPP; line-length FAIL (L23 = 101); archive-valid 7/1/0 |
| plan | $1.05 | $0.4729 | **FAIL (FFF); CP5 PASS (PPP): REGRESSION** | PASS (PPP); CP5 PPP | PASS (19; CP5 20) | PASS (lint, start, test) | eval score 0.9 (CP5 1); skepticism PPP; no-placeholders FAIL (`<n>`); line-length FAIL (L48 = 109); archive-valid 6/2/0 |

- **fix passes R4.** A's restore cured the grounding regression (FFF → PPP), and the new output
  names no `tools/archive.py`.
- **plan fails R4 on rubric-scope**, so CP6 stops. redesign, slice and investigate were not
  run. Results: `evals/results/2026-11-09T14-08-53Z` (fix), `…14-10-56Z` (plan).

**Why plan's scope failed: offline, no spend, inference.** The scope rubric PASSES a prompt that
"names out-of-scope items by path, ID or command", and FAILS one that "plans S-02 or S-04
instead of S-03". What the three stored plan outputs do:

| | CP5 (PPP) | CP6a-2 (PPP) | run 5 (FFF) |
|---|---|---|---|
| dedicated out-of-scope block | **yes**: `OUT OF SCOPE: do not start these, do not drift into them:` then "- S-02 CSV export design, because it is its own slice (ROADMAP.md:6); record interactions only." / "- S-04 multi-currency, because it is a later slice (ROADMAP.md:8)." | **yes**: "OUT of scope: S-02 CSV export and S-04 multi-currency (ROADMAP.md:6,8). Plan only where S-03 …" | **no**: S-04 appears only as a deferral ("anything further (multi-currency S-04, …) is a deferral") and in a DON'T line ("plan S-02 or S-04 work beyond naming interactions") |
| `WHAT YOU CANNOT DO` stop-list (§4.13) | yes | yes (`WHAT YOU CANNOT DO`) | no; "STOP AND REPORT (do not fake these)" instead |

- **F's block excerpt lost §4.13** (WHAT YOU CANNOT DO: the stop-list) between CP5's candidate
  (a8ba587) and CP6a-2's (f846d85). That's the same E-09 cut A restored for L and A. It's still
  missing at 94f259e: F's excerpt runs §4.0–4.3, 4.5–4.7, 4.14, 4.19–4.22.
- F's template carries the out-of-scope only as one line: "Constraints: no code changes, no
  commits, <out-of-scope areas>."
- At CP6a-2 the model still wrote an "OUT of scope" line unprompted. This time it didn't, and the
  out-of-scope items are scattered (a deferral sentence, a DON'T clause). For the haiku judge
  that apparently isn't "names out-of-scope items", and it may read S-02/S-04 being mentioned in
  phase text as planning them.
- **Best explanation:** the same class as fix. An E-09 block cut (§4.13 for F) removed the
  structure that reliably carried the negative scope, and the judge marks its absence.

**Options for Shoaib (none taken):**
1. Restore §4.13 to F's excerpt (and its stop-list, out-of-scope block), as A did for L and A.
   That's a new candidate, so R5 means card-less for plan, then quality from the start.
2. Checked offline: among the five quality cases, only F is missing §4.13. At 94f259e, D (slice)
   has §4.6 and 4.8–4.14, X (investigate) has §4.6, 4.9 and 4.13, and A and L have §4.6 and
   4.13. So restoring §4.13 to F is the only E-09 gap of this kind left in the CP6 set.
3. A Planner ruling on the haiku judge (e.g. `--judge-model`), which is a rule change.

## Run 4: candidate c8edb15, probe code eea02ad (INCOMPLETE: A5 FAIL at card-less)

| | |
|---|---|
| Candidate | `c8edb15`, **frozen** (R5): 9ed9d44 plus B's 7ffe72d (Step 0 runs `archive.py --where` alone, retries with `python`, then reads one per call). Floors: plan 29,983 · slice 32,307 · fix 31,798 · redesign 30,892 · investigate 34,825 (measured offline, same as the probe's) |
| Cost | card-less **$0.4977** |
| Status | **INCOMPLETE, A5 FAIL at card-less.** Card-fresh and quality were not run. Nothing was re-run or changed |

| # | Step | Command (`--cand c8edb15 --model haiku --runs 3`) | Cost | Result |
|---|---|---|---|---|
| 1 | card-less load | `compare --cases slice fix redesign plan investigate --home empty --budget 0.08 --max-total 0.55` | $0.4977 | **FAIL (A5)**; load within the gates |

| Case | per-run rule bytes | median | v1.1.0 | v1.2.0 | $ |
|---|---|---|---|---|---|
| slice | 32,307 ×3 | 32,307 | 62,894 | 61,230 | 0.1010 |
| fix | 31,798 37,019 37,019 | 37,019 | 53,561 | 43,475 | 0.1003 |
| redesign | 36,113 30,892 30,892 | 30,892 | 53,481 | 39,314 | 0.0875 |
| plan | 29,983 29,983 35,204 | 29,983 (632 B under) | 30,615 | 41,367 | 0.1022 |
| investigate (R1) | 34,825 40,046 34,825 | 34,825 (under 40,000) | — | — | 0.1068 |

- Every median is at or below both baselines. derive.md was read 5 times (fix ×2, redesign,
  plan, investigate). investigate r2 went over the 40,000 soft line in one run; the median is
  what R1 reports.
- A1 PASS.
- B's Step 0 works: `--where` output naming the sandbox home appears in **15 of 15** runs (run
  3's card-fresh managed 2 of 15). That isn't gated in card-less, but card-fresh depends on it.
- **A5 flags 2 runs, on 3 Bash calls that ran inside the fixture or the sandbox home:**

| Run | Call | Why it flags |
|---|---|---|
| fix r1 | `cd "<fixture>" && git log --format='%h %s' -- src/invoice.js && git show 82de56a:src/invoice.js \| sed -n '12,18p'` | `sed` is not a granted command and not in the run 3 read-only list |
| investigate r2 | the same chain with `git log -n 3 …` | the same (`sed -n`) |
| investigate r2 | `python "<cand>/tools/archive.py" --dry-run "<home>/tmp/….json" \| grep -E "FAIL\|WARN\|DRY RUN\|would write"` | a pipeline stage `grep` (shell grep, not `git grep`) is not in the list |

**Diagnosis (no remedy applied):** both are text filters on a pipe, with no file of their own.
`sed -n '12,18p'` prints lines 12–18 of the `git show` output, and `grep -E …` filters the
dry-run's output. Nothing left the probe root, and the home scan found nothing. Under the
rules as written they flag: the run 3 ruling lists git subcommands and `--version` only.
Claude Code ran both under dontAsk as read-only commands.

**Options for Shoaib (none taken):**
1. Extend the read-only list to pipe filters with no file argument and no write option:
   `sed -n '<addr>p'` (print-only, no `w`, `-i` or `e`), `grep` / `grep -E` (no `-r` or path
   arguments), `sort`, `uniq`, `cut` as later pipeline stages. Then re-grade run 4 (expect 0
   flags) and continue from card-fresh on the same candidate, since card-less passes on load.
2. Keep them flagged. Then the generator must avoid shell filters in Bash (use Read with
   offset/limit instead), which is another candidate and a full re-run.
- Trace: `C:/genprompt-probe/genprompt-probe-20261109-122027/`.

### Run 4 continued: A5 general rule (frozen 5a2504b), card-fresh INCOMPLETE (spend guard)

- Shoaib ruled "general rule, continue". The pre-check passed: the P1 leak still flags, and
  run 4 card-less re-grades to 0 of 15 (CP6-plan.md, "Run 4 ruling"). So card-less PASSES on
  the frozen A5, with the medians above.
- Card-fresh ran 5×3 on c8edb15 with `--cardless slice=32307 fix=37019 redesign=30892
  plan=29983 investigate=34825 --budget 0.08 --max-total 0.55`.
- **The spend guard stopped it after 13 of 15 runs, at $0.4877.** investigate r2 and r3 never
  ran. The probe survived the window loss in between and exited on the guard, not a crash.
- Cause: card-fresh runs now cost about $0.0375 each, against the about $0.025 the 0.55 total
  assumed. With B's Step 0 fix the runs find the card and do more work.
- **INCOMPLETE, not graded** (a partial set is never a pass). Traces:
  `C:/genprompt-probe/genprompt-probe-20261109-131401/` (13 jsonl, no report).
- Proposed: re-run card-fresh whole with `--max-total 0.70`. Awaiting GO.

### Run 4 card-fresh re-run (cap raised to $8.50): VALID, C1 FAIL

- Re-run whole and fresh on c8edb15 with the same flags but `--max-total 0.75`.
- Cost **$0.4948**; CP6 total **$3.0015** of $8.50 ($5.4985 left).
- Trace: `C:/genprompt-probe/genprompt-probe-20261109-145426/`.

| Case | per-run rule bytes | median | C2 limit (card-less + 1,245) | $ |
|---|---|---|---|---|
| slice | 32,307 32,307 37,528 | 32,307 | 33,552 | 0.1170 |
| fix | 31,798 37,019 31,798 | 31,798 | 38,264 | 0.0905 |
| redesign | 30,892 36,113 30,892 | 30,892 | 32,137 | 0.0911 |
| plan | 29,983 ×3 | 29,983 | 31,228 | 0.0947 |
| investigate | 34,825 ×3 | 34,825 | 36,070 | 0.1014 |

- **Validity: VALID, 15 of 15 runs saw the card** (B's Step 0 fix works). 12 runs Read the
  card file; the other 3 saw it only through `--where` output, which counts by definition.
- A1 PASS, C2 PASS, A5 PASS (frozen A5, no flags).
- **C1 FAIL:** slice r3, fix r2 and redesign r2 each Read `guide/blocks/derive.md` (5,221 B),
  although all three saw the card.

**Diagnosis (no remedy applied):** in all three runs the order was:
1. `--where` (home found);
2. fixture reads;
3. a `Glob **/*`;
4. **`derive.md`**;
5. only then the card Read.

After reading the card they used it: redesign r2 noted "the profile card is fresh (stamps
`9c672ba` match, derived today)". In the 9 runs that Read the card *before* anything else, none
read derive.md. So the generator sometimes reaches for derive.md before it looks for the cached
card. That is a Step 2 ordering lapse, not a stale or unusable card. For scale: card-less runs
read derive.md in 5 of 15 (run 4), card-fresh in 3 of 15.

**Options for Shoaib (none taken):**
1. Generator fix (new candidate, so R5 means a full re-run): right after `--where`, Step 2
   checks `<home>/generated-prompts/by-repo/<key>.profile.md` before any fixture survey, and
   reads derive.md only if the card is missing or stale.
2. Planner ruling on C1 (a gate change after a result): e.g. C1 judged only on runs that never
   Read the card, or a rate instead of zero.

**C1 result and decision (Shoaib).**
- C1 is recorded as a FAIL and is not re-ruled: 3 of 15 card-fresh runs read derive.md before
  the card.
- The medians are unaffected: every card-fresh median equals its card-less one, and C2 passes.
- Decision: 1.3.0 ships with this stated as a known issue, and the card-first ordering fix goes
  to 1.3.1.

### Run 4 quality (opus-5-5, plugin eval at c8edb15): FAIL at fix (R4, rubric-grounding)

Order: fix, plan, redesign, slice, investigate. Each case is capped at the lower of its planned
cap and $8.50 minus the running total.

| Case | cap used | cost | rubric-scope | rubric-grounding | cites-real | gates-exist | others |
|---|---|---|---|---|---|---|---|
| fix | $0.77 (left $5.4985) | **$0.4492** | FAIL (FFF), CP5 FAIL (FPF): no regression | **FAIL (FFF), CP5 PASS (PPP): REGRESSION** | PASS (25 citations; CP5 22) | PASS (lint, start, test) | eval score 0.8 (CP5 0.9); skepticism PPP; line-length PASS; no-placeholders PASS; self-check PASS; archive-valid 8/0/0 |

- **R4 FAILS at fix:** rubric-grounding's majority verdict went from PASS to FAIL (0 of 3 votes,
  against 3 of 3 at CP5). CP6 stops here. plan, redesign, slice and investigate were not run.
- Results: `evals/results/2026-11-09T13-37-09Z` (run from the probe tree with
  `--plugin ../genprompt-wt-c-cand --doctor ../genprompt-wt-c-cand/tools/doctor.py`).

**What I could check (no remedy applied):**
- The judge sees the whole emitted prompt: the eval's `focus` is the last message, and the run
  had a single text message holding the lock, the fence and the notes.
- The harness doesn't expose the judge's reasoning, only its votes.
- Every claim I could check against the fixture holds:
  - each cited `path:line` is inside the file;
  - src/invoice.js:14's loop, :32's export, and :21's NaN gap in applyDiscount;
  - test/invoice.test.js:14/:18 and the 6 test declarations;
  - CLAUDE.md:6–9, :12–13, :16–18; package.json:9, :11–12; src/cli.js:4, :24–29;
  - only `lint`, `start` and `test` are used as gates.
- So I can't name the claim the judge found false.
- The same prompt shape passed grounding at CP6a-2 (PFP) and at CP5 (PPP). The same fix
  output is also FAIL 3/3 on scope, although its SCOPE section names the out-of-scope items by
  path and ID. That points at judge variance or a reading I can't see, not a clear generator
  regression.
- **This is my reading, not a ruling:** under R4 it is a FAIL.

**Why the fix judge failed it: offline investigation, no spend (Shoaib: "find out why
first")**

- **The reasoning isn't stored anywhere.**
  - aggregate.json, aggregate-result.json and structural.json keep only `judgeVotes` (true or
    false) and "judge votes: FAIL FAIL FAIL"; report.html has the same.
  - The eval's temp dir (`claude-eval-eMoaRc`) holds only the scaffolded workspace.
  - No judge transcript exists under the projects folder.
- **The harness can't re-grade stored output.** `claude plugin eval` has no judge-only or
  re-grade mode. `--verbose` with `--debug-file` logs per-message trace events, but only on a new
  run, and it is untested whether that includes judge text. `evals/run.py --regrade` re-applies
  only the deterministic graders.
- **The judge is haiku** (`--judge-model`, default haiku) with 3 votes per rubric, which explains
  the vote swings run to run (fix grounding: CP5 PPP, CP6a-2 PFP, now FFF).
- **Rubric "grounding"** (cases/fix/graders/rubric-grounding.md) FAILS a response that "cites a
  file that is not in the list" of 13 workspace files, a line past a file's end, a script that
  doesn't exist, or a claim contradicting the ground truth. Unchecked claims must be marked
  [UNVERIFIED].

**The three stored fix outputs compared** (CP5 `2026-11-08T19-07-58Z`, CP6a-2 `…01-41-45Z`, now
`…13-37-09Z`):

| | CP5 (grounding PPP, scope FPF) | CP6a-2 (PFP, PPP) | now (FFF, FFF) |
|---|---|---|---|
| file paths outside the 13-file list | bare `archive.py` (×3) | bare `archive.py` (×2), `~/.genprompt`, `local-rules.md` | **`tools/archive.py` (×2)**: "couldn't run `tools/archive.py --dry-run`", "run `python3 tools/archive.py --where`" |
| `[UNVERIFIED]` tags | 0 | 0 | 0 |
| "not run" disclosure | "Grounded by: I read every file … without running anything" | "**Environment limits this run:** Bash is disabled …" up top, and "Nothing was run" | "I confirmed this by reading the code and the fixture, not by running anything"; "(pass/fail not run by me)" |
| FALSE POSITIVES heading | "(re-checked, all correct)" | "(re-checked by reading)" | no qualifier |
| SCOPE names a src/cli.js refactor | **yes**: "Refactoring src/cli.js (its comment at :4 admits accretion)" | **no** | **yes**: "src/cli.js refactor (its own comment, src/cli.js:4, invites one)" |

- I checked every `path:line` and code claim in the new output against the fixture (above), and
  all of them hold. The only citation outside the rubric's file list is `tools/archive.py`, a
  repo-relative path to genprompt's own tool that doesn't exist in the workspace. It's also wrong
  as an instruction: run from the repo, that path is missing.
- **Best explanation (inference, not proven):**
  - **Grounding FFF:** the haiku judge took `tools/archive.py` as a cited file that isn't in the
    workspace, which is the rubric's first FAIL clause. Older outputs wrote bare `archive.py`,
    which reads as a tool name, not a path. This is model wording variance in the self-check
    notes, not a change in the generator's rules: B's Step 0 text says
    `"${CLAUDE_PLUGIN_ROOT}/tools/archive.py"` both before and after.
  - **Scope FFF:** the scope rubric FAILS if the prompt "also asks for … a refactor of
    src/cli.js". CP5 and now both *name* the cli.js refactor as out of scope and both fail
    (FPF, FFF). CP6a-2 didn't name it and passed PPP. The haiku judge appears to match the
    mention, not the negation. That one isn't gated (no regression vs CP5) but has the same
    cause: haiku reading surface text.
- **Re-grade cost estimate (not run):** the harness can't re-grade, so a replica judge would be
  `claude -p --model haiku` with the rubric plus the stored final message, asked for a verdict
  *and a reason*.
  - The harness's own judge costs about $0.0007 a vote (this run: $0.0059 for 9 votes). Through
    `claude -p` the Claude Code system prompt dominates, so about $0.01–0.03 a vote.
  - Grounding only, the new output, 3 votes: about $0.06.
  - An A/B to test the explanation (the new output as is, and with `tools/archive.py` →
    `archive.py`), 3 votes each: about $0.12.
  - Both rubrics on all three stored outputs: about $0.36.
  - It isn't the harness's exact judge wrapper, so it explains a verdict rather than replacing
    one.

**Options for Shoaib (none taken):**
1. One fix re-run (about $0.45) to separate judge variance from a real regression. A re-run
   needs your OK under the stop rules.
2. Accept the FAIL as recorded and decide 1.3.0 on it.
3. Expose the judge's reasoning in the eval harness offline (no spend), then re-grade this
   result if the harness allows (`run.py --regrade` re-applies the deterministic graders only;
   the LLM votes would need a re-run).

**V4 outcome, stated plainly (P3).** Run 1's refusal of the chained `archive.py --where; git …`
calls was a probe artefact. Real Claude Code checks a chained command one subcommand at a
time: the V4 trace under slice.md's real grant ran `--where; git status` and the `||` / `cd`
chains. So a real user whose generator chains `--where` with granted commands finds their card.
The probe's own deny list (cd, ls, head, …) caused run 1's refusals, and 4bb6bc7 removed it.

## Replay after run 3 (Shoaib's GO; cap raised to $7.50)

Run 3's unexplained refusals were replayed: plan r2's exact first command, under the probe's
exact flags on 9ed9d44, with the shim grant from slice.md. Two sessions cost $0.0081, three
more cost $0.0088, so the replay totals **$0.0169**. Traces:
`C:/genprompt-probe/genprompt-replay-20261109-121606/` and `…-121738/`.

| Deny rules in effect | plan r2 exact command (`python3 …--where; cd … && git … && ls -la && ls docs`) |
|---|---|
| all probe rules | **refused** (dontAsk: no matching allow rule) |
| none | ran |
| Read/Glob/Grep denials only (home, ~/.genprompt, shared roots, other top-level folders) | **refused** |
| Bash denials only (cat, echo, …) | ran |
| Write/Edit denials only | ran |

- Shorter variants ran under all rules: `--where; git status`, `--where; cd …`,
  `--where; cd … && git status`, and the same chain without the `--where` part. So the refusal
  needs the probe's Read/Glob/Grep deny rules together with this longer chain (the `ls` parts
  after the `--where` part).
- **Verdict: a probe-only cause, not a product finding.** A real user has none of those deny
  rules, and without them the exact command runs under the shim grant.
- **No probe change.** Those deny rules are what seal the real home (isolation shows
  `ls <home>` "blocked by a deny rule"), so dropping them would break isolation. Isolation
  doesn't need re-running.
- B's Step 0 fix sidesteps the problem: `--where` alone always ran under the full rules (run 1
  slice r1, run 3 fix r2 and redesign r1), so card discovery doesn't depend on the chain. Chains
  still refused in the probe after that cost only the reads, not the card.

## Run 3: candidate 9ed9d44, probe code ddff904 (INCOMPLETE: card-fresh INVALID)

| | |
|---|---|
| Candidate | `9ed9d44`, frozen (same as run 2) |
| Probe | `evals/realuse/run.py` at ddff904: run 2's code plus the run 3 A5 rulings (quote-aware; Claude Code's read-only commands accepted). Isolation skipped (permissions unchanged since run 2) |
| Pre-check (no spend) | run 2 card-less re-graded 0 of 15; P1 CP6a v1.2.0 drive-root leak still flags; P2 CP6a 3 of 36 (was 4), CP6a-2 0 of 12 |
| Cost | card-less $0.3690 + card-fresh $0.2483 = **$0.6173** |
| Status | **INCOMPLETE: card-fresh INVALID (2 of 15 runs saw the card).** Under V3 that stops CP6. Quality was not run |

| # | Step | Command (`--cand 9ed9d44 --model haiku --runs 3`) | Cost | Result |
|---|---|---|---|---|
| 1 | card-less load, 5 cases | `compare --cases slice fix redesign plan investigate --home empty --budget 0.08 --max-total 0.55` | $0.3690 | **PASS** |
| 2 | card-fresh load, 5 cases | `compare … --home card --cardless slice=32310 fix=31801 redesign=30895 plan=29986 investigate=34828 --budget 0.08 --max-total 0.55` | $0.2483 | **INVALID** (2/15) |
| 3 | quality | not run | $0 | — |

### 1. Card-less: PASS

| Case | per-run rule bytes | median | v1.1.0 | v1.2.0 | $ |
|---|---|---|---|---|---|
| slice | 32,310 32,310 37,531 | 32,310 | 62,894 | 61,230 | 0.1062 |
| fix | 31,801 ×3 | 31,801 | 53,561 | 43,475 | 0.0409 |
| redesign | 30,895 ×3 | 30,895 | 53,481 | 39,314 | 0.0624 |
| plan | 35,207 29,986 29,986 | 29,986 (629 B under v1.1.0) | 30,615 | 41,367 | 0.0726 |
| investigate (R1) | 34,828 ×3 | 34,828 (under 40,000) | — | — | 0.0869 |

derive.md was read once by slice (r3) and once by plan (r1). A1 PASS, A5 PASS (no flags).
Trace: `C:/genprompt-probe/genprompt-probe-20261109-111114/`.

### 2. Card-fresh: INVALID

- Card seen per run: slice n n n · fix n Y n · redesign Y n n · plan n n n · investigate n n n.
  That is **2 of 15** (12 needed), and three cases have 0 of 3 (2 needed).
- Gates are reported but not counted (V3):
  - A1 PASS, A5 PASS, C1 PASS (over the 2 runs that saw the card).
  - C2 can't be judged for slice, plan or investigate (no run saw the card). It passes for fix
    and redesign.
- Every median equals its card-less one; the card is 1,245 B.
- Trace: `C:/genprompt-probe/genprompt-probe-20261109-114445/`.

**Why 13 runs never saw the card (diagnosis, no remedy):** each one put `archive.py --where` in
a long chained first Bash call, the call was refused, and the run carried on without the card.
The two runs that found it ran `--where` on its own. The refusals fall into three kinds:

| Kind | Runs | What refused the chain |
|---|---|---|
| a part no shim grants (`cat`, `echo`, `find`, a `( … )` group, a relative `tools/archive.py`) | fix r1, investigate r1, investigate r3, plan r1, redesign r2, redesign r3, slice r2, slice r3 | the probe's deny rule (cat, echo) or dontAsk (find, relative path). In real use these prompt the user instead |
| a chain whose parts all look granted, refused by dontAsk ("no matching allow rule") | fix r3, investigate r2, plan r2, plan r3, slice r1 | e.g. plan r2: `python3 <cand>/tools/archive.py --where; cd "<fixture>" && git status --porcelain -uall && git rev-parse --show-toplevel && git branch --show-current && git log --oneline -5 && ls -la && ls docs`. **Not explained.** The V4 trace ran a similar chain under the same grant, but without the probe's deny rules |
| `python3` is the Windows store alias here | (also in slice r3, fix r2) | an `&&` chain stops at `python3 … --where` (exit 49) before any `--where` output |

- The second kind is the open question. V4 showed that real Claude Code runs a chain of granted
  parts. These chains look granted too, yet were refused.
- Candidate causes:
  - a deny rule the probe adds that V4 didn't have (Read denials on other top-level folders,
    the home and the shared roots) changes how Claude Code judges the chain;
  - or one part fails the grant's prefix match in a way I can't see from the trace.
- A V4-style trace replaying plan r2's exact command under the probe's exact flags, with and
  without the probe's deny rules, would settle it: one haiku run, about $0.01. Not run, under V3.
- The first kind is generator behaviour: haiku builds big chains with `cat`/`echo`, which no shim
  grants. In real use the user gets a permission prompt. Under the probe's dontAsk the call is
  refused, and it is not retried with `--where` alone.

**Options for Shoaib (none taken):**
1. Authorise the about $0.01 replay to explain the second kind before deciding anything.
2. Generator fix: Step 0 runs `archive.py --where` as its own Bash call (never chained) and
   falls back to `python` if `python3` is the store alias. That makes card discovery independent
   of the rest of the chain, in real use and in the probe.
3. Accept card-fresh as unmeasurable in headless dontAsk and gate 1.3.0 on card-less plus
   quality only. This changes R2, so it's the Planner's call.

## Run 2: candidate 9ed9d44, probe code 4bb6bc7 (INCOMPLETE: A5 FAIL at card-less)

| | |
|---|---|
| Candidate | `9ed9d44`, **frozen** (R5): fb17b8c plus A's `fix/F-plan-naming` (32a474c; F, B, N and P name their doc by `PROFILE.docnaming`, derive step 6 narrowed). Floors measured offline and in the probe: plan 29,986 · slice 32,310 · fix 31,801 · redesign 30,895 · investigate 34,828 |
| Probe | `evals/realuse/run.py` at 4bb6bc7 (CP6-plan.md "Re-run rules after the CP6 stop") |
| Cost | isolation $0.0060 + card-less $0.3168 = **$0.3228** |
| Status | **INCOMPLETE, A5 FAIL at card-less.** Card-fresh and quality were not run. Nothing was re-run or changed |

| # | Step | Command (`--cand 9ed9d44 --model haiku --runs 3`) | Cost | Result |
|---|---|---|---|---|
| 1 | isolation (13 checks) | `run.py isolation` | $0.0060 | **PASS** |
| 2 | card-less load, 5 cases | `compare --cases slice fix redesign plan investigate --home empty --budget 0.08 --max-total 0.55` | $0.3168 | **FAIL (A5)**; load numbers all at the floor |
| 3 | card-fresh load | not run | $0 | — |
| 4 | quality | not run | $0 | — |

### 1. Isolation: PASS

The 5 home and shared-root Glob/Grep calls were denied. The work dir was readable. The
drive-root Glob returned 101 names, 0 of them outside the probe root. All five real-home Bash
calls (`ls <home>`, `ls -la <home>/.genprompt`, `head -5 <home>/.gitconfig`, `cd <home> && ls`,
`cd <home>/.genprompt && ls`) were made and refused. The bare `cd && ls -a` was refused too, so
this step did not show the sandbox profile in use (allowed by the rule: refused or sandbox
listing). Trace: `C:/genprompt-probe/genprompt-isolation-20261109-095802/`.

### 2. Card-less load: A5 FAIL (load itself within the gates)

| Case | floor | per-run rule bytes | median | v1.1.0 | v1.2.0 | $ |
|---|---|---|---|---|---|---|
| slice | 32,310 | 32,310 ×3 | 32,310 | 62,894 | 61,230 | 0.0532 |
| fix | 31,801 | 31,801 ×3 | 31,801 | 53,561 | 43,475 | 0.0830 |
| redesign | 30,895 | 30,895 ×3 | 30,895 | 53,481 | 39,314 | 0.0777 |
| plan | 29,986 | 29,986 ×3 | 29,986 | 30,615 (629 B under) | 41,367 | 0.0397 |
| investigate (R1) | 34,828 | 34,828 ×3 | 34,828 | soft line 40,000 | — | 0.0631 |

No run read any rule file (derive.md included). A1 PASS. Every median is at or below both
baselines, so the load gate would pass; **A5 fails the step**:

| Run | Bash call that ran (all inside the fixture) | Why A5 flags it |
|---|---|---|
| fix r3 | `cd "<probe>/fixture" && git blame -L 12,18 -- src/invoice.js` | `git blame` is not on the A5 safe list (no shim grants it; Claude Code ran it as a read-only git command) |
| fix r3 | `cd "<probe>/fixture" && git grep -c "^test(" HEAD -- test/` | the `(` inside the quoted pattern: A5 flags any `(` as a subshell, quoted or not |
| redesign r2 | `cd "<probe>/fixture" && git grep -c -E "^\s*(test\|it)\(" HEAD -- test/ && git grep -n -E "'lint'\|\"lint\"\|require\(" HEAD -- scripts/ src/index.js` | the same: parentheses inside a quoted regex |
| investigate r3 | `python --version; python3 --version` | `python --version` is not on the safe list (it printed `Python 3.12.10`) |

**Diagnosis (no remedy applied):**
- Nothing left the probe root. Each output is fixture data (blame lines, per-file test counts)
  or the Python version, and the home scan found nothing.
- Two flags (fix r3 `git grep`, redesign r2) are the grader being stricter than the ruling
  meant. A `(` inside a quoted argument is not a subshell, but `BASH_BAD_SYNTAX_RE` doesn't
  look at quoting.
- Two (`git blame`, `python --version`) are commands that no shim grants, yet Claude Code ran
  them under dontAsk as read-only commands. The A5 safe list follows the shim grant, so they
  flag. Real use would run them the same way.
- Chains containing `cat` or `echo` were refused whole, as in real use (fix r1, fix r3's first
  call).
- Trace: `C:/genprompt-probe/genprompt-probe-20261109-095838/` (report.md).

**Options for Shoaib (none taken):**
1. Rule that A5 parses quotes: a `(`, `|`, `;` or `>` inside a quoted argument is not shell
   syntax. That clears fix r3's `git grep` and redesign r2.
2. Rule on Claude Code's own read-only auto-allow list: add `git blame` and `--version` probes
   to the safe list (they read only the fixture or print a version), or keep them flagged.
3. Either way it's a grader change after a result, so it needs a ruling. Then re-run from
   card-less (R5: same candidate, about $0.32). Isolation needn't repeat unless the probe's
   permissions change.

## Run 1: candidate fb17b8c (INCOMPLETE: stopped at the card-fresh load gate)

| | |
|---|---|
| Candidate | `fb17b8c`, **frozen** (R5): local main with E-12 merged plus the CP6 estimate refresh. Floors: plan 29,987 · slice 32,310 · fix 31,801 · redesign 30,895 · investigate 34,828 |
| Rules | `evals/CP6-plan.md` with R1–R5 exactly as written. Stop at the first gate failure, no re-runs, no remedies without Shoaib |
| Scope | the automated part only. D1–D6 (manual dispatch checks) are deferred until after 1.3.0 (Shoaib): `--send` and `--from` ship marked experimental |
| Run | 2026-11-09, haiku load probes from `evals/realuse/run.py` at fb17b8c |
| Cost | isolation $0.0041 + card-less $0.3007 + card-fresh $0.2548 = **$0.5596** of the $6.25 cap |
| Status | **INCOMPLETE, gate FAIL at card-fresh (C1 and A5).** Quality was not run. Nothing was re-run or changed |

## Steps

| # | Step | Command (all `--cand fb17b8c --model haiku --runs 3`) | Cost | Result |
|---|---|---|---|---|
| 1 | isolation | `run.py isolation` | $0.0041 | **PASS** |
| 2 | card-less load, 5 cases | `compare --cases slice fix redesign plan investigate --home empty --budget 0.08 --max-total 0.55` | $0.3007 | **PASS** |
| 3 | card-fresh load, 5 cases | `compare … --home card --cardless slice=32310 fix=31801 redesign=30895 plan=29987 investigate=34828 --budget 0.08 --max-total 0.55` | $0.2548 | **FAIL** (C1, A5) |
| 4 | quality (fix, plan, redesign, slice, investigate) | not run | $0 | — |

## 1. Isolation: PASS

The 5 home and shared-root Glob/Grep calls were denied, the work dir was readable, and the
drive-root `**/*.md` Glob returned 0 names outside the probe root.
Trace: `C:/genprompt-probe/genprompt-isolation-20261109-083900/`.

## 2. Card-less load: PASS

| Case | floor | per-run rule bytes | median | v1.1.0 | v1.2.0 | vs v1.1.0 | vs v1.2.0 | $ |
|---|---|---|---|---|---|---|---|---|
| slice | 32,310 | 37,537 32,310 32,310 | 32,310 | 62,894 | 61,230 | −48.6% | −47.2% | 0.1187 |
| fix | 31,801 | 31,801 ×3 | 31,801 | 53,561 | 43,475 | −40.6% | −26.9% | 0.0438 |
| redesign | 30,895 | 30,895 ×3 | 30,895 | 53,481 | 39,314 | −42.2% | −21.4% | 0.0411 |
| plan | 29,987 | 29,987 ×3 | 29,987 | 30,615 | 41,367 | −2.1% (628 B) | −27.5% | 0.0425 |
| investigate (R1, not gated) | 34,828 | 34,828 ×3 | 34,828 | soft line 40,000 | — | 5,172 B under | — | 0.0545 |

- Every gated case is at or below both stored baselines. investigate is under the R1 soft line,
  so the 1.3.0 CHANGELOG needs no note for it.
- Rule files read: `derive.md` once (slice r1). plan read nothing in any run.
- A1 PASS (no Read of an @-included file, PROTOCOL.md or 03-blocks). A5 PASS.
- Trace: `C:/genprompt-probe/genprompt-probe-20261109-083928/` (report.md).

## 3. Card-fresh load: FAIL

| Case | per-run rule bytes | median | C2 limit (card-less + card 1,245) | $ |
|---|---|---|---|---|
| slice | 32,310 ×3 | 32,310 | 33,555 | 0.0807 |
| fix | 31,801 ×3 | 31,801 | 33,046 | 0.0425 |
| redesign | 30,895 ×3 | 30,895 | 32,140 | 0.0397 |
| plan | 31,596 29,987 29,987 | 29,987 | 31,232 | 0.0505 |
| investigate | 34,828 ×3 | 34,828 | 36,073 | 0.0414 |

Seeded card: 1,245 B in every run.

| Gate | Verdict | Detail |
|---|---|---|
| A1 | PASS | none |
| C1 | **FAIL** | plan r1 Grepped `guide/01-target-profile.md` for "2.7\|docs/\|naming", then Read its §2.7 (lines 277–302, 1,609 B) |
| C2 | PASS | every median equals its card-less median (but see "card never loaded" below) |
| A5 | **FAIL** | slice r1 ran `git branch --show-current; git branch --merged main; git rev-parse --short HEAD`, which returned the fixture's branches (`main`, `feat/s-01-line-totals`) and `4c804d4` |

Trace: `C:/genprompt-probe/genprompt-probe-20261109-090719/` (no report.md: the probe exits 1 on
a FAIL after printing the report).

### What the traces show (diagnosis only, no remedy applied)

**A5 is a strict-grader flag, not a leak.** All three parts are read-only git commands in the
fixture, each on the A5 safe list. `safe_bash` rejects any `;` between parts (only `&&` / `||`
are allowed), so the call counts as unsafe. Claude Code ran it because each part matches a
pre-approved `git` rule. Nothing outside the probe root was read or written.

**The card was not loaded in most runs, so this probe barely measured card-fresh use.**
- Of 15 runs, only slice r1 Read the card (`…/homes/gp-cand-slice-r1/generated-prompts/by-repo/fixture.profile.md`).
  plan r2 Globbed its home and found it.
- The rest batched `archive.py --where` with `;`-chained git commands in one Bash call. The
  probe's permission rules deny the whole call, so the generator never learned where the home
  was and carried on as if card-less.
- **plan r1 is one of these.** With no card, F-plan's deliverable line ("one plan doc (§2.7
  naming)") sent it to §2.7 of `guide/01-target-profile.md`, which C1 forbids. The card it never
  read has `docnaming: docs/<TOPIC>.md … next e.g. docs/CSV-EXPORT.md`, which would have
  answered that question.
- So C2 passes only because the card was rarely in play: medians equal the card-less ones and no
  card bytes were spent. It shows no regression, but it also doesn't show the card saving
  anything.

**Real home: tried, denied.** plan r1 and slice r2 tried to Read
`<user home>/.genprompt/local-rules.md` (the default home, since `--where` had failed). The
probe's deny rules refused both. A5 doesn't flag denied calls, which is right: isolation held.
It does show that a generator that can't run `--where` falls back to the default home path.

### Options for Shoaib (none taken)

1. **Accept C1 as a real finding** and fix the generator offline: e.g. the `--where` call should
   run on its own (not chained with `;`), or F-plan should name `PROFILE.docnaming` before §2.7.
   Then re-run card-fresh (about $0.30) and continue.
2. **Rule the probe invalid for card-fresh** (the card wasn't loaded in 13 of 15 runs) and fix
   the probe offline so the home is known without a Bash call (e.g. state it in the request or
   allow the separate `--where` call). Then re-run card-fresh.
3. **Rule on A5's `;` strictness.** Allowing `;` between safe parts in `safe_bash` would clear
   slice r1. It's a grader change, so it needs a ruling before it counts.

Either way, CP6 is not a pass: card-fresh failed, and quality (fix, plan, redesign, slice,
investigate) is still to run. About $5.69 of the cap is left; the quality estimate was $3.95.

## Bash and writes (card-fresh)

- Bash that ran: read-only git in the fixture, `archive.py --where` (when run on its own) and
  `archive.py --dry-run`. Most chained calls were denied.
- Writes: only under the sandbox homes (`homes/<run>/tmp/*.json`), e.g. slice r1's
  `s-02-csv-export.json`.
