# Changelog

One line per rule change: `- <YYYY-MM-DD> · <file> · <what changed and why>`.

## Unreleased

- 2026-11-09 · tools/build_shims.py, guide/06-library.md, PROTOCOL.md, tools/doctor.py,
  tools/archive.py · E-12 `--send <session>`: opt-in dispatch of the archived prompt to another
  Claude session. The rules are in the on-demand §10.8: a strict project-key check, a yes per send
  even under --go/auto-go, the worker's own toplevel check, prompt-only payload. Emitters get
  ListAgents/SendMessage. A new `sent: <name>|copy` header field is linted and counted. PROTOCOL
  gains one pointer line, net +17 B.
- 2026-11-09 · archetypes/H-commit.md, P-review.md, Q-security.md, R-perf.md, guide/08-grammar.md,
  tools/build_shims.py, tools/doctor.py, README.md · E-15: `:commit --pr` adds the PR step (branch,
  push, open PR, each a §4.23 approval the worker asks for; a placeholder-only body or the repo's
  own template), read on demand from §8.2 so only --pr runs load it. Hidden options become
  per-command flags on their own argument-hints only: `--chat-only` (review), `--verify` (commit;
  `verify+` still accepted), `--readonly-phase` (security Phase 1, perf measure-only); the grammar
  gains a per-command modifier table.
- 2026-11-09 · archetypes/F-plan.md, archetypes/I-roadmap.md, tools/build_shims.py, tools/doctor.py,
  README.md · E-13: :plan and :roadmap offer `--split <N>` (argument-hint; archive and doctor know
  the flag) and point to §8.1; F tightened to offset, so the plan floor stays 29,854 B.
- 2026-11-09 · guide/08-grammar.md, archetypes/J-next.md · E-13: new §8.1 `--split <N>` for :plan
  and :roadmap (N disjoint-ownership lanes in worktrees, a shared findings folder, one merge prompt,
  siblings archived under one follows); :next recognises a lane report and re-issues the merge prompt.
- 2026-11-09 · guide/03-blocks.md, guide/blocks/, examples/worked-examples.md · E-20: the §4.1
  header gains an advisory `Worker` row (model, effort, fast mode) read from a new Worker column in
  the §4.21 tier table (Delta Sonnet 5.5; Focused, Slice, Program Opus 5.5); set with /model.
  Net-zero floor: offset by wording cuts in §4.1/§4.21 (every archetype −7 to −30 B).
- 2026-11-09 · archetypes/X-investigate.md, tools/build_shims.py, .claude-plugin/ · New archetype X,
  /genprompt:investigate: an unknown-cause bug traced to a root cause at path:line and handed to
  :fix, read-only plus a scratch repro; 24 archetypes.
- 2026-11-09 · archetypes/, guide/00-index.md, README.md · Bug-report lifecycle becomes investigate
  → fix → commit; fix, audit and hotfix point to :investigate with reasons; letters A–X; README
  lists :investigate.
- 2026-11-09 · guide/, archetypes/, utilities/ · Editorial never pass: imperative never outside the
  six invariants becomes a plain statement with a one-clause reason; descriptive uses, headings and
  worker-facing labels stay.
- 2026-11-09 · PROTOCOL.md, guide/03-blocks.md, tools/build_shims.py, tools/doctor.py · E-09f floor
  cut: every archetype's always-loaded rules shrink ~5.2 KB (plan 35,081 → 29,853 B) by cutting
  wording and duplication in PROTOCOL, the common §4 blocks, the compact checklist and the shims;
  no rule, row ID or verdict form dropped. PROTOCOL budget 16,800 → 14,600.

- 2026-11-09 · tools/build_shims.py, commands/, tools/doctor.py · Security: Write/Edit grants narrowed
  from all of ~/.genprompt to PROTOCOL's boundary per command (prompts: generated-prompts/, tmp/;
  :learn: local-rules.md; :profile: by-repo/; others none); doctor --suite fails any widening.
- 2026-11-09 · PROTOCOL.md, tools/build_shims.py, commands/ · E-09e: the home is `~/.genprompt/` unless `GENPROMPT_HOME` names another; archetype and `:auto` shims read it in Step 0 with `archive.py --where` (existing ARCHIVE grant), while learn/profile/history keep `ls -d ~`. The write boundary now names `~/.genprompt/tmp/` (the parts file Step 6 writes) next to `generated-prompts/`; allowed-tools unchanged.
- 2026-11-09 · tools/doctor.py, tools/archive.py · Every tool resolves the genprompt home through
  doctor.genprompt_home() (GENPROMPT_HOME, absolute); archive.py --where prints it, read-only.
- 2026-11-09 · tools/build_shims.py, guide/01-target-profile.md, guide/blocks/, PROTOCOL.md, guide/00-index.md · E-09d load cut. Excerpts carry only the blocks PROTOCOL uses on every run (§4.0–§4.3, §4.14, §4.21, §4.22) plus those the archetype names; §4.20 keeps only the named rows and §4.21 only the archetype's tier. Each excerpt ends with a compact §6 checklist (all 23 row IDs, one line each), so a normal run reads no rule file. New §2.0 is the card-less derivation path; `guide/blocks/derive.md` (§2.0 + the card template, generated) replaces reading guide/01 and stack-matrix in full.

## 1.2.0 (2026-11-09): rules loaded per archetype and per stack, a profile card that stays fresh

Each command now @-includes only the rule excerpt its archetype needs, the stack matrix routes to
one per-stack gate ladder, and workspace detection is read only for monorepos. A profile card stays
fresh while its file@sha stamps hold (90-day ceiling), and auto-go can skip the lock wait when you
opt in. Prompts wrap at 100 characters, fix and redesign prompts bound their scope, and doctor
checks the Agensi bundle. Measured load is mixed (evals/CP5.md, CP5c, haiku, 3 runs vs 1.1.0):
slice −24% and plan −42% rule bytes, but fix +12% and redesign +34%, because a first run with no
profile card derives it from guide/01 and the stack matrix, and every run now loads its full
excerpt (1.1.0 sometimes skipped 03-blocks). Repeat runs with a cached card skip derivation; a cut
of the excerpts and the profile path is planned for 1.3.0.

- 2026-11-09 · utilities/doctor.md · Documents the suite's Agensi bundle check (deferred from E-18b).
- 2026-11-08 · stacks/ladders/, stacks/stack-matrix.md, tools/doctor.py · Per-stack gate ladders moved
  verbatim to stacks/ladders/<stack>.md (16 files); the matrix routes to the detected stack's file only.
- 2026-11-08 · stacks/workspaces.md, stacks/stack-matrix.md, tools/doctor.py · Workspace detection moved
  to its own file, read only for multi-root or workspace repos; the bundle and its check include it.
- 2026-11-08 · tools/doctor.py · Fix: verdict-line WARN compared counts with the partial chat table
  (only FAIL/N/A rows are shown); counts now match the §6 checklist and shown rows match N/A + FAIL.
- 2026-11-08 · tools/doctor.py, tools/build_skill_bundle.py · doctor --suite checks the Agensi bundle the
  tool would build (SKILL.md version and counts vs plugin.json and the tables; the file set), in memory.
- 2026-11-08 · tools/doctor.py · Final PROTOCOL budget 16,800 bytes (16,212 achieved); the lint's
  line-width WARN cites the §4.21 wrap rule and exempts a lone unbreakable token.
- 2026-11-08 · PROTOCOL.md, tools/doctor.py, utilities/learn.md, utilities/history.md, guide/08-grammar.md
  · Opt-in auto-go (`auto-go: on` in local-rules): explicit argument + fresh card + no unknowns
  skips the lock wait, archived as lock=auto and counted apart from confirmed locks. Off by default.
- 2026-11-08 · tools/build_skill_bundle.py, .gitignore · The Agensi SKILL.md bundle is generated from
  plugin.json and the build_shims tables (no hand-typed counts), deterministically, into dist/.
- 2026-11-08 · stacks/stack-matrix.md · Workspace detection (pnpm/yarn/npm/bun, Turborepo, Nx, Cargo,
  go.work, Elixir umbrella) with per-package vs orchestrator gate rules; Bun, Deno, Elixir/Phoenix,
  C/C++ (CMake), Terraform and Pulumi rows (apply/destroy/up never gates); plainer tone.
- 2026-11-08 · guide/01-target-profile.md, utilities/profile.md, tools/doctor.py · A profile card is
  fresh while its file@sha stamps hold (no 14-day TTL), with a 90-day ceiling; age shown; first use
  writes the card. Gates stay uncached. PROTOCOL Step 2's wording follows in E-11 part 2.
- 2026-11-07 · tools/build_shims.py · Step 0 no longer re-reads the @-included PROTOCOL and
  archetype (probe showed they are already in context); saves ~20 KB per emission.
- 2026-11-07 · tools/build_shims.py, guide/blocks/, PROTOCOL.md · Each archetype shim @-includes a
  generated excerpt of the 03-blocks sections it needs, instead of the generator reading 03-blocks.
  Real-use check (evals/CP4b.md): median rule bytes −26.5%.
- 2026-11-08 · PROTOCOL.md · Step 2's card rule follows §2.9 (90-day ceiling, freshness is the
  stamps) and the lock's Stack line reports the card's age.
- 2026-11-08 · PROTOCOL.md, guide/01, 03, 06, 07, tools/doctor.py · PROTOCOL core 19.9 → 16.5 KB:
  read-on-demand detail moved to its owning section behind "Read only when" pointers; doctor WARNs
  past 14,336 bytes.
- 2026-11-08 · PROTOCOL.md, guide/01-target-profile.md · Pointers to the stack matrix's workspace
  section 1b (E-16): monorepo orchestrators, gate ladder order, zero-config formatters.
- 2026-11-08 · archetypes/L-fix.md, archetypes/A-redesign.md, guide/04-checklist.md · Fix and
  redesign prompts bound scope: L-fix gains a SCOPE block naming what not to start, A-redesign keeps
  the public surface and asks before changing behaviour, row 10 checks both.
- 2026-11-08 · archetypes/, tools/build_shims.py · Every abbreviated §4.14 INSERT names the gate
  labels and the GENPROMPT-REPORT line, because the baseline fix prompt composed §4.14 from that
  line alone; --check fails a template whose §4.14 INSERTs never name it.
- 2026-11-08 · guide/03-blocks.md, guide/04-checklist.md · Hard wrap rule: every prompt line wraps
  at 100 characters except a lone unbreakable token (§4.21), and the §4.14 GENPROMPT-REPORT spec is
  shown wrapped, because every baseline prompt had longer lines and copied the one-line spec.
- 2026-11-08 · PROTOCOL.md, guide/, archetypes/, utilities/ · Tone pass: bold kept only on the six
  invariants and structural table labels (626 to ~190 markers); PROTOCOL wording compressed 16,548
  to 15,747 bytes with every tool-matched literal unchanged.
- 2026-11-08 · PROTOCOL.md, guide/01-target-profile.md · Read pointers state a testable condition: a
  fresh card means no profile reads, archive.py exit 0 means no §10 read, stacks/workspaces.md only
  for multi-manifest or workspace repos (CP5 showed reads leaking past them).
- 2026-11-08 · guide/01-target-profile.md, guide/00-index.md, README.md · Ladder pointers name
  stacks/ladders/<stack>.md, the one file stack-matrix.md routes to, so a run reads one ladder, not
  all of them.

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
