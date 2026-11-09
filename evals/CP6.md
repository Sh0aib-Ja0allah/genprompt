# CP6: 1.3.0 candidate (INCOMPLETE: run 3 card-fresh INVALID)

Total CP6 spend: run 1 $0.5596 + V4 trace $0.0047 + run 2 $0.3228 + run 3 $0.6173 =
**$1.5044** of the $6.25 cap ($4.7456 left).

**V4 outcome, stated plainly (P3).** Run 1's refusal of the chained `archive.py --where; git …`
calls was a probe artefact. Real Claude Code checks a chained command one subcommand at a
time: the V4 trace under slice.md's real grant ran `--where; git status` and the `||` / `cd`
chains. So a real user whose generator chains `--where` with granted commands finds their card.
The probe's own deny list (cd, ls, head, …) caused run 1's refusals, and 4bb6bc7 removed it.

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
