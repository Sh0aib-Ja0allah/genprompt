# CP6: 1.3.0 candidate fb17b8c (INCOMPLETE: stopped at the card-fresh load gate)

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
