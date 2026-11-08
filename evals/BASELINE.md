# genprompt eval baseline

**Phase-1 baseline (pre-E-04b: archive.py not yet wired, archive-valid skipped).** E-07 (the
stop-report header) and E-08 (the compact self-check and row 23) are in the code under test, so
this one run is the reference for Phase 2. It replaces the planned pair of a provisional run now
and a re-run at the end of Phase 1.

| | |
|---|---|
| Code under test | main `758e59e` (E-08: because-clauses and checklist row 23), plus the evals commits on `enh/E-06-evals`, which touch `evals/` only |
| Run date | 2026-11-07 |
| Eval CLI | `claude plugin eval`, Claude Code 2.1.318 |
| Model under test | claude-opus-5-5 (`--model claude-opus-5-5`) |
| Judge model | the eval CLI default (`--judge-model` not set). Each llm grader gets 3 votes and passes on 2 of 3 |
| Runs | 1 per case, `--ablation none` (no no-plugin arm), `--max-cost-usd 8` |
| Tools in the run | Read, Glob and Grep. No Bash: the eval refuses an unconfined shell on Windows, so the generator could not run git |
| Grader versions | In-eval graders: one version, as `build_cases.py` generates them at this commit. Structural graders: **v2** (see below); the v1 counts are shown for reference |
| Total cost | **$3.3844** for the six cases, plus $0.0031 for the negative control. The earlier smoke run ($0.5918, before the rebase, on `bc1e689`) is not part of this baseline |

Main moved to `5f2b956` (E-04a: archive.py and `doctor --prompt`) after this run started. E-04a
changes only `tools/`, so it does not change what the generator emits, and the baseline was not
re-run.

## Scores per case and grader

The letters in brackets are the three judge votes (P = PASS, F = FAIL).

| Grader | slice | fix | redesign | next-hybrid | commit | plan |
|---|---|---|---|---|---|---|
| eval: archetype-label | PASS | PASS | PASS | PASS | PASS | PASS |
| eval: dry-run-declared | PASS | PASS | PASS | PASS | PASS | PASS |
| eval: lock-present | PASS | PASS | PASS | PASS | PASS | PASS |
| eval: no-edit | PASS | PASS | PASS | PASS | PASS | PASS |
| eval: no-generator-marker | PASS | PASS | PASS | PASS | PASS | PASS |
| eval: no-write | PASS | PASS | PASS | PASS | PASS | PASS |
| eval: protocol-loaded | PASS | PASS | PASS | PASS | PASS | PASS |
| eval: rubric-grounding | PASS (PPP) | PASS (PPP) | PASS (PPP) | PASS (PPP) | FAIL (FPF) | FAIL (FPF) |
| eval: rubric-scope | PASS (PPF) | FAIL (FFF) | FAIL (FFF) | PASS (PPP) | FAIL (FFF) | PASS (PFP) |
| eval: rubric-skepticism | PASS (PPP) | PASS (PPP) | PASS (PPP) | PASS (PPP) | FAIL (FFF) | PASS (PPP) |
| **eval score** | **1** | **0.9** | **0.9** | **1** | **0.7** | **0.9** |
| structural: lock-present | PASS | PASS | PASS | PASS | PASS | PASS |
| structural: one-fence | PASS | PASS | PASS | PASS | FAIL | PASS |
| structural: no-placeholders | PASS (v1 FAIL) | PASS (v1 FAIL) | PASS (v1 FAIL) | PASS | FAIL | PASS (v1 FAIL) |
| structural: line-length | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| structural: length-cap | PASS | PASS | PASS | PASS | FAIL | PASS |
| structural: gates-exist | PASS | PASS | PASS | PASS | FAIL | PASS |
| structural: cites-real | PASS (v1 FAIL) | PASS (v1 FAIL) | PASS (v1 FAIL) | PASS (v1 FAIL) | FAIL | PASS |
| structural: self-check | PASS | FAIL | PASS | PASS | FAIL | PASS |
| structural: protocol-loaded | PASS (new in v2) | PASS (new in v2) | PASS (new in v2) | PASS (new in v2) | PASS (new in v2) | PASS (new in v2) |
| structural: no-writes | PASS | PASS | PASS | PASS | PASS | PASS |
| structural: archive-valid | SKIPPED | SKIPPED | SKIPPED | SKIPPED | SKIPPED | SKIPPED |
| **structural passed (v2)** | **9/10** | **8/10** | **9/10** | **9/10** | **3/10** | **9/10** |
| structural passed (v1) | 6/9 | 5/9 | 6/9 | 7/9 | 2/9 | 7/9 |

### What the scores mean (read this before comparing)

- **commit: the generator declined to write a commit prompt.** The fixture's S-02 work is
  unfinished on purpose. The docs promise a `--csv` flag that `src/cli.js` lacks, and a new test
  pins the wrong TOTAL because of the planted defect. The generator found both, and instead of a
  commit prompt it offered fix, then slice, then commit. That follows the H archetype's rule
  against committing unfinished work, so it is arguably correct. Even so, every structural grader
  that needs a prompt block fails, and the scope and skepticism rubrics fail because there is no
  prompt to judge. In this baseline, commit measures judgement, not the commit prompt. A later
  fixture variant with finished work would measure the commit prompt itself.
- **rubric-grounding fails on commit and plan (1 of 3 votes PASS on each),** even after the
  smoke-run fix that lists the fixture's git files and SHAs in the rubric. On commit the judge saw
  a closeout, not a prompt. Plan was not investigated further: the instructions were to report a
  grounding failure after the fix, not to re-run. The deterministic grounding checks (cites-real
  and gates-exist) pass on every case that emitted a prompt. **Phase 2 should gate on cites-real
  and gates-exist, and treat rubric-grounding as advisory until it is stable.** It has one run per
  case here. Two more full runs (about $6.80) would not fit under the $8 ceiling on top of this
  run's $3.38, so they were not done.
- **rubric-scope fails on fix and redesign (0 of 3 votes each).** This is the main quality signal
  in the baseline: neither prompt bounds its scope negatively, which is what the rubric asks for.
- **line-length fails on every prompt.** Each prompt has 1 to 9 lines over 100 characters, and the
  longest is 179. This is a real breach of the length rule in guide/03-blocks.md (§4.21).
- **self-check fails on fix.** It printed `Self-check: 12 passed, 3 marked N/A or not done, 0
  failed`, a paraphrase of PROTOCOL.md's literal `Self-check: <n> PASS · <n> N/A · <n> FAIL`.
- The generator could not read the run's temp `~/.genprompt` and had no shell, so every lock says
  the ancestor scan, the occupancy check and the last prompt went unchecked. Scores from a run
  with Bash granted (on Linux or macOS) cannot be compared with these.

### Structural graders v1 → v2 (a re-grade of the same stored runs, with no model spend)

v1 is the module as it was committed for the run. v2 fixes two false positives and adds one
grader:
- **cites-real** now resolves a bare basename such as `ROADMAP.md:11` when it is unique in the
  workspace. In slice, fix, redesign and next-hybrid, v1 failed only on such citations, and every
  line number was in range.
- **no-placeholders** now ignores a `<name>` inside a quoted path pattern, such as `feat/<slug>`
  or `docs/<TOPIC>.md` quoted from the fixture's CLAUDE.md. It also ignores one inside a
  double-quoted string, such as a quoted CLI error message. A bare `<branch>` still fails, as the
  unit tests show.
- **protocol-loaded** is new. It reads the trace, passes on any of three paths, and reports which
  one fired:
  1. The marker is in the logged initial context.
  2. A Read of PROTOCOL.md returned the marker.
  3. The init event registers genprompt commands, and the emission has a TARGET LOCK with an
     Archetype line.

  **Every baseline case passed on path 2.** The trace starts at the system init event and does
  not log the expanded slash-command prompt, so path 1 cannot fire with this CLI. Once E-09b
  removes the double read, path 3 is the one that will pass. The in-eval `protocol-loaded` regex
  also matched the Read result in every case, so it will FAIL once E-09b lands. From CP4 on, use
  the structural grader.

### Where the protocol marker came from

| Case | Marker source | Rules files the generator Read itself |
|---|---|---|
| slice | Read of PROTOCOL.md | PROTOCOL.md, D-slice.md |
| fix | Read of PROTOCOL.md | PROTOCOL.md, L-fix.md |
| redesign | Read of PROTOCOL.md | PROTOCOL.md, A-redesign.md |
| next-hybrid | Read of PROTOCOL.md | PROTOCOL.md, J-next.md, archetypes/README.md, D-slice.md |
| commit | Read of PROTOCOL.md | PROTOCOL.md, H-commit.md |
| plan | Read of PROTOCOL.md | PROTOCOL.md, F-plan.md |

The shim @-includes PROTOCOL.md and the archetype file, and a separate probe confirmed that they
expand. Each of these Reads is therefore a second load of about 19 KB.

### archive-valid: SKIPPED, and why

archive-valid was **skipped in every case, and counts as neither a pass nor a fail.** There are
three reasons:
- archive.py was not yet wired into PROTOCOL (that is E-04b).
- The cases run with `--dry-run`, so nothing is archived.
- The eval sandbox refuses Bash on Windows, so the generator could not run archive.py inside a
  case anyway.

archive.py and `doctor --prompt` now exist on main (`5f2b956`). **Planned swap:** archive-valid
becomes a post-run check in `run.py` that calls `tools/doctor.py --prompt` on each emitted prompt,
outside the sandbox. The text checks in `lint/structural.py` become calls to the same lint. The
graders were not changed during this baseline.

### Re-grade with structural v3 (2026-11-08, stored runs, no model spend)

The swap is done. Structural v3's archive-valid runs `tools/doctor.py --prompt` at main `77699ec`
on each stored emission, after removing fenced lock blocks and adding a synthetic line-1 header
that carries the case's archetype. doctor's archive-record checks (`header`, `filename-words`,
`header-vocab`, `self-check`) are not graded, because `--dry-run` writes no record. A WARN is
listed but does not fail. Every other row above is unchanged by v3.

| Case | archive-valid (v3) | doctor WARNs |
|---|---|---|
| slice | PASS | line-width |
| fix | PASS | line-width, gates-labelled, report-line |
| redesign | PASS | line-width |
| next-hybrid | PASS | line-width |
| commit | FAIL: no prompt block (the generator wrote a closeout) | none |
| plan | PASS | line-width |

v3 structural passes: slice 10/11, fix 9/11, redesign 10/11, next-hybrid 10/11, commit 3/11,
plan 10/11. The fix prompt asks for a report but has no GENPROMPT-REPORT line (E-07) and
labels no gate. doctor flags both, and the stricter structural checks did not catch them. Compare
CP4 against these v3 rows.

## Negative control

`controls/bad-emission` (haiku, $0.0031) echoes a deliberately broken prompt and attempts one
Write. Every grader the control exercises failed:
- every in-eval grader except no-edit: each llm rubric got 0 of 3 votes, no-write saw the Write,
  and protocol-loaded found no marker
- every structural grader except length-cap

The control does not exercise those two. no-edit is the same tool_used check as no-write, which
failed. length-cap fails in `lint/test_structural.py` (`test_length_cap_fails_when_over`).

## Token use and cost per case

| Case | Turns | Input | Cache write | Cache read | Output (thinking) | Run $ | Judge $ | Total $ |
|---|---|---|---|---|---|---|---|---|
| slice | 33 | 12 | 48,499 | 163,619 | 12,879 (3,847) | 0.6783 | 0.0075 | 0.6858 |
| fix | 22 | 18 | 24,794 | 194,849 | 6,446 (1,074) | 0.3735 | 0.0053 | 0.3788 |
| redesign | 8 | 10 | 25,207 | 98,649 | 8,417 (2,838) | 0.7786 | 0.0075 | 0.7861 |
| next-hybrid | 28 | 14 | 42,416 | 175,358 | 13,257 (5,035) | 0.6396 | 0.0082 | 0.6478 |
| commit | 23 | 14 | 37,363 | 194,678 | 6,991 (3,326) | 0.4777 | 0.0045 | 0.4822 |
| plan | 22 | 14 | 25,757 | 139,938 | 8,147 (1,566) | 0.3970 | 0.0066 | 0.4037 |
| **total** | | | | | | | | **3.3844** |

The totals include the judge. Cache reads dominate, because each turn re-sends the protocol and
the rules already in context.

## Load size per command

Bytes of each shim plus the files it @-includes, at `758e59e`:

| Command | Shim | @-includes | Total |
|---|---|---|---|
| slice | 1,957 | PROTOCOL.md 16,123 + archetypes/D-slice.md 2,740 | 20,820 |
| fix | 1,985 | PROTOCOL.md 16,123 + archetypes/L-fix.md 3,238 | 21,346 |
| redesign | 2,010 | PROTOCOL.md 16,123 + archetypes/A-redesign.md 3,133 | 21,266 |
| next | 1,997 | PROTOCOL.md 16,123 + archetypes/J-next.md 3,209 | 21,329 |
| commit | 1,954 | PROTOCOL.md 16,123 + archetypes/H-commit.md 3,222 | 21,299 |
| plan | 1,936 | PROTOCOL.md 16,123 + archetypes/F-plan.md 2,883 | 20,942 |

## Re-running

Run `python evals/run.py --model claude-opus-5-5 --max-cost-usd 8`, then `python evals/run.py
--controls`. Compare the results with the v2 structural rows and the in-eval rows above. To
re-grade stored results with no model spend, run `python evals/run.py --regrade` on the results
directory.
