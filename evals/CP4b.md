# CP4b: E-09's token saving in real use (@-includes expanded)

CP4 showed that `claude plugin eval` does not expand the shims' @-includes (evals/CP4.md), so it
cannot measure E-09. CP4b runs the same commands with `claude -p`, where @-includes do expand.

| | |
|---|---|
| Baseline copy | `c3fa3ee` (main, which E-09 sits on), renamed `gpbase`. The only difference from the candidate is E-09b + E-09a |
| Candidate copy | `4fb361a` (E-09a-excerpts, containing E-09b), renamed `gpcand` |
| Run | 2026-11-08, `claude -p --model haiku --output-format stream-json --verbose --plugin-dir <copy>`, cwd = the ledgerlite fixture (base variant), `--go --dry-run`, 1 run per cell |
| Harness | `evals/realuse/run.py` (stage / fixture / case / analyze) |
| Cost | **$0.1123** in total: four runs at $0.1093, plus a $0.0030 isolation probe. No sonnet re-run was needed (see G4) |

## Acceptance

| Gate | Result |
|---|---|
| The candidate does not Read PROTOCOL.md, its archetype or 03-blocks | **PASS**: it read none of them (it read 04-checklist, plus stack-matrix in slice) |
| The excerpt arrives via @-include | **PASS**: no Read of `guide/blocks/*`, and the first-turn context grew (next row) |
| First-turn context is larger | **PASS**: slice 24,904 → 30,814 tokens, fix 25,108 → 31,872 |
| Total rule bytes are lower | **PASS** in both cases |
| Median rule bytes drop ≥25% | **PASS**: slice −25.4%, fix −27.7%, median **−26.5%** |

| Case | first-turn ctx | @-included bytes | rule Read bytes (files) | rule bytes total | cache write | cache read | output | turns | $ |
|---|---|---|---|---|---|---|---|---|---|
| slice, base | 24,904 | 23,786 | 46,063 (01-target-profile, 03-blocks, 04-checklist) | 69,849 | 65,132 | 290,573 | 29,619 | 27 | 0.0307 |
| slice, cand | 30,814 | 36,542 | 15,579 (04-checklist, stack-matrix) | **52,121 (−25.4%)** | 46,888 | 228,818 | 34,567 | 25 | 0.0290 |
| fix, base | 25,108 | 24,312 | 38,121 (03-blocks, stack-matrix, 04-checklist) | 62,433 | 52,183 | 219,823 | 26,712 | 29 | 0.0260 |
| fix, cand | 31,872 | 39,438 | 5,720 (04-checklist) | **45,158 (−27.7%)** | 40,321 | 229,047 | 26,585 | 21 | 0.0236 |

## What the numbers say

- **@-includes expand in real use.** The candidate starts about 6k tokens larger, which matches its
  extra @-included excerpt plus the Step 0 text. It never Reads the excerpt.
- **In this run the saving comes from E-09a, not E-09b.** Haiku on the baseline did not re-Read
  PROTOCOL.md or its archetype either, so E-09b's double-read fix has nothing to remove here. The
  saving is the 22.5 KB `guide/03-blocks.md` Read (plus 01-target-profile in slice), which the
  excerpt replaces. E-09b still matters where a model does re-read: the opus runs in the eval read
  every rules file, though for a different reason (no expansion).
- **Cost and cache:** cache writes fell in both cases (−28% and −23%), and cost fell 6% and 9%.
  Cache reads fell in slice and were flat in fix (+4%).
- **Quality (structural graders on the chat output):** base 7/9 and 7/9, candidate 8/9 and 8/9.
  Every run fails line-length. The baseline also left a `<total>` placeholder (slice) and cited
  `CLAUDE.md:19` in an 18-line file (fix); the candidate made neither mistake. Every output had a
  TARGET LOCK and DRY RUN.
- **Caveats:** this is haiku, not the opus model used for the baseline, and one run per cell. It
  shows the direction and the size of the effect, not a stable mean. Reading behaviour depends on
  the model.

## Isolation, and one gap

The real HOME was kept, because sign-in needs it; credentials were never copied. Every run used:
- `--setting-sources local`: no user settings, hooks or user plugins
- `--strict-mcp-config` and `--no-session-persistence`
- `--permission-mode dontAsk`, with only the plugin copy added via `--add-dir`
- deny rules for `~/.genprompt`
- Bash, Write, Edit and the messaging tools disallowed

A $0.003 probe confirmed that a Read outside the working directories is denied.

- **Every `~/.genprompt` access was denied:** 5 Glob or Read attempts were denied, and 5 Bash `ls`
  attempts failed because Bash was unavailable.
- **Gap:** `dontAsk` does not stop **Glob from listing names** outside the working directories.
  Runs listed file names under `~/.claude` (which CLAUDE.md files exist) and timed out walking the
  home directory. One of those walks was a Glob rooted at the home directory with the pattern
  `.genprompt/local-rules.md`, which the `~/.genprompt` deny rule does not cover. It timed out
  before returning anything. No file contents outside the fixture and the plugin copy were read.
  Next time: put the fixture outside the home directory and deny Glob and Grep on the home
  directory.
