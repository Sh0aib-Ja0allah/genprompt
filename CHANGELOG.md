# Changelog

One line per rule change: `- <YYYY-MM-DD> · <file> · <what changed and why>`.

## Unreleased

- 2026-11-08 · guide/01-target-profile.md, utilities/profile.md, tools/doctor.py · A profile card is
  fresh while its file@sha stamps hold (no 14-day TTL), with a 90-day ceiling; age shown; first use
  writes the card. Gates stay uncached. PROTOCOL Step 2's wording follows in E-11 part 2.
- 2026-11-07 · tools/build_shims.py · Step 0 no longer re-reads the @-included PROTOCOL and
  archetype (probe showed they are already in context); saves ~20 KB per emission.
- 2026-11-07 · tools/build_shims.py, guide/blocks/, PROTOCOL.md · Each archetype shim @-includes a
  generated excerpt of the 03-blocks sections it needs, instead of the generator reading 03-blocks.
  Real-use check (evals/CP4b.md): median rule bytes −26.5%.

## 1.1.0 (2026-11-08): archive written and checked by a tool, a measurable workflow

The generator now archives every prompt through `tools/archive.py`, which writes the file and the
shard row and then lints them, so a broken record is flagged instead of silently saved; doctor also
prints a print-only repair plan for older archive errors (`--suggest-fixes`). The chat output is
shorter: the prompt comes first and the self-check is one exact verdict line plus its FAIL/N/A rows.
Worker reports start with a GENPROMPT-REPORT line, the TARGET LOCK shows whether the last prompt
landed, and each archived prompt records its flags, how the repo was found and the lock outcome.
Commands lead with what they are for, utilities stay out of the model's listing, and the plugin now
has CI, a unit-test suite and an eval baseline.

- 2026-11-07 · tools/build_shims.py · Trigger-first descriptions; help/doctor skip PROTOCOL.
- 2026-11-07 · tools/doctor.py, tools/tests/, .github/workflows/ · CI, unit tests, version-sync check.
- 2026-11-07 · tools/build_shims.py, guide/08-grammar.md · Grammar table generated; 5 hint drifts
  fixed; :auto filed as Entry; read-only archetypes drop autonomy flags.
- 2026-11-07 · tools/build_shims.py · doctor, learn, history, profile get disable-model-invocation:
  still typeable, but out of the model's skill listing (frees listing budget; help stays visible).
- 2026-11-07 · guide/03-blocks.md, guide/04-checklist.md, PROTOCOL.md, archetypes/ · Every report
  starts with a GENPROMPT-REPORT header line; Step 1 and :next parse it as claims verified by git.
- 2026-11-07 · PROTOCOL.md, guide/04-checklist.md, tools/build_shims.py · Prompt first in chat; the
  self-check prints as a verdict line plus FAIL/N/A rows (full table in the archive, or --verbose).
- 2026-11-07 · guide/03-blocks.md, guide/04-checklist.md, archetypes/, README.md · Traps, decisions,
  stop-list and out-of-scope items carry a "because" clause; checklist row 23 appended.
- 2026-11-07 · tools/archive.py, tools/doctor.py · Deterministic archive writer; doctor --prompt lint.
- 2026-11-07 · PROTOCOL.md, guide/06-library.md, guide/04-checklist.md, tools/build_shims.py · Step 6
  archives only through tools/archive.py (hand-writing removed); archetype shims and :auto may run it.
- 2026-11-07 · README.md, utilities/help.md, archetypes/C, G, M · First-run doctor step, core loop and
  an I-want-to table; onboard/greenfield/kickoff cross-links with reasons; :help routes next/approve.
- 2026-11-07 · tools/build_shims.py · An empty :auto shows the target plus six core commands with
  their purpose, and points to :help for the rest, in one message.
- 2026-11-07 · PROTOCOL.md, tools/doctor.py, utilities/history.md · flags/via/lock vocabulary pinned;
  lock shows landed:; doctor and :history report via/lock/flag stats; width-aware stub check.
- 2026-11-07 · evals/ · Eval fixtures, 6 cases, graders and the Phase-1 baseline.
- 2026-11-08 · assets/, README.md · Screenshots re-rendered from the sample repo to show 1.1.0 output:
  the lock's landed check, the GENPROMPT-REPORT line, the compact self-check.
- 2026-11-08 · tools/doctor.py, utilities/doctor.md · doctor --suggest-fixes: a print-only repair plan
  for archive ERRORs (derivable vs manual, nothing invented) plus legacy label drift; writes nothing.
- 2026-11-08 · PROTOCOL.md, guide/04-checklist.md · The chat verdict line is pinned as an exact
  string (two forms, dry-run included) because tools and evals match it literally.
- 2026-11-08 · tools/doctor.py · Lint WARN when a chat verdict line is not exactly `Self-check: <n> PASS
  · <n> N/A · <n> FAIL (…)` or its counts miss the row count (the table's, or the §6 checklist's when
  no table is shown); never runs on table-only files.

## 1.0.0 (2026-09-24): first public release

The rules suite (protocol v3) packaged as a Claude Code plugin.

- 2026-09-24 · plugin · Packaged as a Claude Code plugin with a single-plugin marketplace. The
  commands are generated into `commands/` by `tools/build_shims.py` and reference the rules through
  `${CLAUDE_PLUGIN_ROOT}`, so they work wherever the plugin is installed.
- 2026-09-24 · PROTOCOL.md, guide/01-target-profile.md, guide/06-library.md · The archive moved
  out of the rules folder to `~/.genprompt/generated-prompts/`. The plugin cache is replaced on
  every update, so an archive inside it would be lost.
- 2026-09-24 · utilities/learn.md, guide/00-index.md · `:learn` saves personal rules to
  `~/.genprompt/local-rules.md` and never edits the plugin. It offers a ready-to-paste upstream
  issue for rules that would help everyone.
- 2026-09-24 · guide/07-environment.md · §11 now holds general per-OS facts. Machine-specific facts
  belong in `local-rules.md`.
- 2026-09-24 · commands · The entry point that picks the archetype is `/genprompt:auto`, because a
  plugin cannot expose a bare `/genprompt`.
- 2026-09-24 · tools/doctor.py · Checks the plugin's `commands/` folder and the archive in
  `~/.genprompt/`. A missing archive is normal on a fresh install. A new suite check rejects any
  runtime file that names one user's home directory.
- 2026-09-24 · examples/worked-examples.md · Project-identifying details were replaced with a
  fictional booking app. The shape of each block is unchanged.

## Before 1.0.0

genprompt grew through three private versions:
- **v1:** one prompt-generation guide and a flat archive of prompts.
- **v2:** a protocol file, twelve slash commands and per-repo shard indexes.
- **v3:** the rulebook split into `guide/` by section, one file per archetype (A–W), the stack
  matrix, the TARGET LOCK, the 22-row self-check, the archive line-1 header, and the doctor and
  shim-generator tools.
