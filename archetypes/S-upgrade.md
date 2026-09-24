# 5.S: Upgrade and migration · `/genprompt:upgrade`

| | |
|---|---|
| **Use when** | A framework or dependency major bump (Laravel, Next, Expo SDK, .NET, Flutter, React…), a dependency sweep, an ORM or platform move (for example Drizzle → Supabase), or a data/schema migration |
| **Not when** | One small patch bump → `:slice` or `:commit` |
| **Autonomy** | Staged. Each stage ends green. §4.19 gate after the plan; §4.8 MODE only with `--unattended` |
| **Baseline delta** | Unchanged at every stage (the same tests pass), except tests deliberately rewritten for new APIs, which are listed |
| **Length tier** | Program (350) |
| **Deliverable** | The upgraded code, one stage per commit, an upgrade notes doc (breaking changes hit, codemods run, rollback path) |

## Generator: before emitting

- **Read the lockfile and manifests** for the current versions. Name the target versions and
  **check whether the repo's policy blocks any** (for example, Composer security-advisory blocking,
  `engines`, a CI matrix).
- **The worker reads the official upgrade guide and changelogs itself.** The prompt names them; it
  never paraphrases a changelog from memory.
- **Stage it:**
  1. prerequisites
  2. one major at a time
  3. codemods
  4. manual fixes
  5. remove deprecations

  Every stage must end green, with its own commit.
- **Data migrations** need:
  - a dry run on a copy
  - reversibility (`down()`, or a documented forward-only reason)
  - a backfill plan
  - **§4.23 approval for anything that touches a non-local database**
- **Lockfile policy:** commit the lockfile. No `--force`, no `--legacy-peer-deps`, and no disabling
  of security policies without an explicit ruling.

## Required blocks

- §4.5, §4.6, §4.7, §4.10, §4.11, §4.14
- §4.20 structure table (stages)
- §4.20 STOP/DEFER with revert
- §4.23 (non-local data)
- §4.19 **or** §4.8

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]
Task: <upgrade X from <v> to <v> | migrate <A> to <B>>. Current versions, from the lockfile: <…>.
Official guides to read FIRST (fetch them yourself; do not rely on memory): <upgrade guide URLs/names>.

[INSERT §4.10 DECISIONS ALREADY MADE: target versions; what is NOT upgraded now; lockfile policy]
[INSERT §4.11 TRAPS: known breaking areas in THIS repo: <file:line uses of APIs that change>]

[INSERT §4.20 Structure: stage | content | why here]
STAGE 1: prerequisites (runtime/tooling versions, config).  GATE + commit.
STAGE 2: bump <package> only. Fix breakages. GATE + commit.  <repeat per major>
STAGE n: remove deprecations and shims. GATE + commit.
<Data migration: dry run on a copy → verify row counts/checksums → [INSERT §4.23] before any
 non-local run → the rollback steps, written down.>

[INSERT §4.20 STOP/DEFER with revert: if a stage cannot go green, revert it, log it, stop and report]
[INSERT §4.19 approval gate after the stage plan, or §4.8 MODE]
[INSERT §4.14: gates <literal>; baseline <n> unchanged at every stage (list any rewritten tests)]
FINAL: `<PROFILE.docnaming: upgrade notes>`: breaking changes hit, codemods run, manual fixes, rollback path.
Start by reading the guides and presenting the stage plan.
```
