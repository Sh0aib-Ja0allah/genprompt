## 0. Invariants that never change

| | |
|---|---|
| Genprompt root | The plugin folder (its path is stated by the command that loaded the protocol): protocol, guide, archetypes, stacks, tools. Read-only at runtime. |
| Protocol (loaded on every command) | `PROTOCOL.md` in the genprompt root |
| Genprompt home | `~/.genprompt/`: the archive and the personal rules. Outside every repo and outside the plugin. |
| Prompt library | `~/.genprompt/generated-prompts/` |
| Personal rules | `~/.genprompt/local-rules.md` (optional; written by `:learn`, read by every command) |
| Per-repo shard and profile | `~/.genprompt/generated-prompts/by-repo/<key>.tsv` and `<key>.profile.md` |
| Per-repo prompt folder | `~/.genprompt/generated-prompts/<key>/` |
| Legacy archive | Only in an archive migrated from genprompt v1/v2: `~/.genprompt/generated-prompts/INDEX.md` and flat prompt files at the root. Read only; never append. |
| **Write boundary** | The generator may Write/Edit only under `~/.genprompt/generated-prompts/`. `:learn` alone may also edit `~/.genprompt/local-rules.md`. Every repo is read-only, and so is the genprompt root. |
| **Commit rule** | The generated prompt decides the worker's git posture. The *generator* never commits anything in a worker repo. |

Ancestor files are discovered, never assumed. A `CLAUDE.md` or `AGENTS.md` above the repo root
describes a different project and governs nothing here, unless the repo's own contract adopts it.
The protocol scans for them on every run (Step 2) and records the literal result. Don't hardcode
one, derive a profile from one, or tell a worker to ignore a file you did not find, because the next
machine may not have it.

---

## 1. Target resolution

The runtime steps are in PROTOCOL Step 1. The rules behind them:

Order: argument ▸ continuation ▸ cwd ▸ ask.
- Always state which rule fired.
- Continuation outranks cwd because a generator chat parked in repo A often receives a report from
  repo B. Retargeting to A would be silent and wrong.
- When the two disagree, show both in the lock.

Running outside a repo is legal. A home or desktop folder is usually not a git repo. The
genprompt root and the genprompt home are the generator's own folders (a clone of the genprompt
root *is* a git repo), so a cwd inside either never selects a target. When there is no candidate,
ask, and offer the most recent targets from `by-repo/`.

The git root is not the code root. In a monorepo the git root often has no manifest, so a
prompt anchored there has no stack, no gates and no role. Resolve to the nearest manifest. When
nothing points inside, ask which sub-project, and name the siblings as out of scope.

Narrow to a code root (moved here from PROTOCOL Step 1). Count manifest directories below
the repo root, honouring EXCLUDE (§2.1). Two manifests in the same directory, such as
`composer.json` + `package.json`, are one root.
- One directory: that is the scope.
- Several, and cwd or the target file is inside one: the nearest wins. Name the siblings as out
  of scope.
- Several, and nothing points inside: ask which sub-project. Don't anchor a prompt at a root
  with no manifest of its own, because it has no stack, gates or role.

Multi-repo prompts are a real shape (a mobile app and its API, with different branches and
commit permissions). Resolve both and give each its own lock row, branch, gates and commit
permission. Add the paired-change rule: *a change to a response shape, route path or status code is
a paired slice on both sides, never a one-sided edit.* Archive under the primary repo: the one
where the first change lands. The other repo's shard gets a row whose file field is
`<primary-key>/<file>`.

Non-git and non-code targets.
- A folder with no git or zero commits is legal: say so in the lock; its git posture is "no git
  operations".
- A deliverable with no repo (a presentation, a research doc) archives under the key `unsorted`.

Facts that cannot be derived. Ask rather than guess:
- which branch work lands on, when `origin/HEAD`, the checkout and the CI triggers disagree
- priority among several open items
- anything on the repo's own blocker list
- credentials and third-party account state
- whether a deliberately inert feature should be switched on
- whether a destructive gate may run against the current database
- design or brand *direction* beyond what a committed design doc pins down

---

## 2. Repo profile derivation

A deterministic, ordered process in which every step is a filesystem or read-only git operation.
The output is the profile: the fields that `<PROFILE.x>` placeholders refer to (see §2.9).

### 2.0 Derivation path (a card-less run reads this, not the rest of §2)

`guide/blocks/derive.md` carries this section and the §2.9 card template. Fill the card in this
order. Read a numbered section below only when its step names a condition that holds.

1. Exclusions. Walk to depth 3 and skip the EXCLUDE list (§2.1, copied here):
   `.git node_modules vendor .next .nuxt .svelte-kit .angular .turbo dist build out coverage .expo
   .dart_tool Pods bin obj target .gradle .idea .vs __pycache__ .venv venv test-results
   storage/framework`
2. Ancestors. In every directory from the root's parent up to the drive root, check `CLAUDE.md`,
   `AGENTS.md`, `.claude/CLAUDE.md` and `CLAUDE.local.md` (`ls` or Glob). They describe other
   projects and govern this one only if its contract adopts them. Report `~/.claude/CLAUDE.md` as
   `user-level: present`, `unreadable` or `none`, never its path (it names the user's home).
   Record the literal result, e.g. `none found`.
3. Contract. Root `CLAUDE.md` binds, with `.claude/CLAUDE.md`; a body that is only `@AGENTS.md`
   points at the contract. No `CLAUDE.md`: `AGENTS.md`. Neither: the contract is unstated. Mine
   it for commands (fenced blocks, and inline "run `…`" lines: `(contract)` gates), hard rules
   (branching, deploy, push, attribution, logging), forbidden trees and a stated persona. Read §2.2
   only when there is a `<subdir>/CLAUDE.md` or `<subdir>/AGENTS.md`, or the contract has no
   commands.
4. Stack and scope. Manifest directories are code roots; the shallowest wins in a subtree.
   Versions come from the manifest or lockfile. `stack`: the framework with major versions; `role`:
   `senior <stack> engineer`, or the contract's persona verbatim. The gate ladder is
   `stacks/ladders/<name>.md`, one of `node bun deno php-laravel dotnet flutter-dart go python
   rails elixir-phoenix jvm rust cpp-cmake swift terraform pulumi` (`bun.lock` or `deno.json`
   beside a `package.json` means bun or deno). Read `stacks/stack-matrix.md` only when no ladder
   name fits the manifest. Read `stacks/workspaces.md` only when the repo has more than one
   manifest directory or a workspace file.
5. Gates, re-derived every run and never cached. Order: the contract's, else CI's step order,
   else format → lint → typecheck → test → build → smoke. A `(script)` gate is a manifest script
   key that exists; a `(derived)` one needs the tool declared (or shipped with the SDK) and a
   config file, or a zero-config tool, as the ladder says; a script beats a derived command. A
   derived gate nothing shows was ever run is `(derived, no baseline)`. The package manager comes
   from the lockfile. No test runner: `test: NONE`, stated as a finding. Mark destructive
   commands ⚠ (`migrate:fresh`, `db:wipe`, `down -v`, anything the contract calls dangerous).
   Read §2.5 only when a compose service, `Makefile` or `justfile` wraps the commands.
6. `truth`: the contract, then binding external docs, the roadmap, then audits; the newer commit
   wins within a tier; annotate authority and give at least one staleness warning (read §2.6
   only when two docs both claim authority). `forbidden`: EXCLUDE, build output, `docs/archive/**`,
   vendored and generated code, dead code the contract names. `default_branch`: the basename of
   `git symbolic-ref refs/remotes/origin/HEAD`, else `origin/main` or `origin/master`, said to be
   inferred. `docnaming`: the pattern the repo's own docs show, else `docs/<kebab-topic>.md`;
   read §2.7 only when the repo shows no naming pattern.
7. Write the card to `~/.genprompt/generated-prompts/by-repo/<key>.profile.md`. `key`: the
   directory basename, lowercased, `_` and spaces turned into `-`. `stamp:` the manifests and the
   contract, each `<file>@<git log -1 --format=%h -- <file>>`. `--dry-run` never writes it.

### 2.1 Exclusions, and ancestors

```text
EXCLUDE = .git node_modules vendor .next .nuxt .svelte-kit .angular .turbo dist build out coverage
          .expo .dart_tool Pods bin obj target .gradle .idea .vs __pycache__ .venv venv
          test-results storage/framework
```

This is the single exclusion list; the protocol and every archetype refer to it.

Only agent-rule files at or below the repo root describe the repo. If there is no in-root
contract, the contract is *unstated*, never the ancestor's. The protocol's ancestor scan lists what
it found above the root, so the lock can say `Ancestors: none found` or name them as non-governing.

The ancestor scan (moved here from PROTOCOL Step 2; it runs whenever the card is derived):
- In every directory from the repo root's parent up to the drive root, check four names:
  `CLAUDE.md`, `AGENTS.md`, `.claude/CLAUDE.md` and `CLAUDE.local.md`. Use `ls` or Glob.
- What you find describes other projects. It does not govern this one unless the repo's own
  contract explicitly adopts it.
- Separately, check the user-level `~/.claude/CLAUDE.md`. Claude Code loads it into every
  session, including the worker's, so report it as `user-level: present`, `unreadable` or
  `none`, not as an ancestor, and never by path: the path names the user's home.
- Record the literal result, e.g. `none found`, rather than assuming a file exists.

### 2.2 Conventions layer

Binding contract: `CLAUDE.md` at the repo root. Also read `.claude/CLAUDE.md` if present, and
`CLAUDE.local.md` as local notes. If a `CLAUDE.md` body is only `@AGENTS.md` (or another
`@import`), follow the pointer: the target is the contract.

Fallback contract: `AGENTS.md`, when there is no `CLAUDE.md`.

Subtree contracts: `<subdir>/CLAUDE.md` or `<subdir>/AGENTS.md`. The file nearest the target
wins, for its subtree only.

Supplementary, never binding over CLAUDE.md: `.cursorrules`, `.cursor/rules/`,
`.github/copilot-instructions.md`, `GEMINI.md`, `.windsurfrules`. Cite them where they add facts.

Mine the contract for hard facts rather than inferring:
- commands:
  - fenced shell blocks under `Commands|Development|Testing|Verification`
  - and inline backticked commands in the contract's prose that it tells you to run (e.g.
    "run `php tools/check-tokens.php` before committing"). These become `(contract)` gates.
- an explicit hierarchy (`source of truth|outranks|authoritative|binding|supersedes`)
- forbidden trees (`orphan|stale|predates|not used by|do not (use|edit|fix)|deprecated`)
- hard process rules (branching, deploy, push, attribution, required logging tools)
- a stated persona (`Operate as a senior…`). If one is stated, use it verbatim and skip the role
  table.

A thin contract (only a few lines, with no commands or architecture) is still binding for
whatever it does say. Take the missing facts from `docs/` and the manifests, and say in the lock
that the contract is thin.

README command blocks are tier 2. Mine the fenced blocks under `README.md`'s
`Commands|Getting started|Development|Testing` headings for facts, but they never outrank the
contract. A README that disagrees with the contract is a staleness finding, not a gate source.

### 2.3–2.4 Manifests, stack and role

Detection, stack labels and role labels live in `stacks/stack-matrix.md`. The rules that apply to
every stack:

- Walk to depth 3, honouring EXCLUDE.
- Code roots are manifest directories. The shallowest one wins within a subtree, and
  nearest-manifest-wins for any target file.
- Count greater than 1 means a monorepo: one profile per root, plus a root orchestration
  profile (Makefile, compose, or a workspace orchestrator: pnpm/Yarn/npm/Bun workspaces, Turborepo,
  Nx, a Cargo or Go workspace, an Elixir umbrella). Read `stacks/workspaces.md` only when the repo
  has more than one manifest directory or a workspace file: it has the evidence files and decides
  per-package vs orchestrator gates.
- A lockfile with no manifest is debris, not a code root.
- Versions come from the manifest or lockfile, never from memory.
- Append dependency modifiers that change the review lens: `+ Supabase/RLS`,
  `+ TanStack Query`, `+ i18n/RTL`, `+ Stripe`, `+ Filament`, `+ Sanctum`, `+ MSW`,
  `+ GSAP/Three.js`.
- A persona stated in the contract overrides the role table.

### 2.5 Verification gates: the field that must never be stale

Re-derive the gates on every invocation, whether or not a cache exists.

1. Order.
   - If the contract states an order, use it.
   - Otherwise use the step order of CI (`.github/workflows/*.yml`, `.gitlab-ci.yml`).
   - Otherwise use format → lint → typecheck → test → build → smoke.
   - Emit the union of contract-mandated and CI gates, placing the contract's extras where the
     contract puts them.
   - If the contract gives no position, a `(contract)` gate goes in the lint slot (after format,
     before typecheck).
2. Existence and labels. Every gate carries exactly one label:
   - `(script)`: a manifest script key that exists (`typecheck` and `type-check` differ between
     sibling repos).
   - `(contract)`: a command the contract tells you to run (§2.2).
   - `(derived)`: the tool is provably present (the next bullet).
   - A `(derived)` gate is emitted only when:
     - it is a declared dependency, or it ships with the SDK (`dotnet`, `go`, `flutter`/`dart`)
     - and either its config file exists, or the tool is zero-config by design (Pint,
       `gofmt`, `dart format`, `dotnet format`, `deno fmt`, `mix format`, `terraform fmt`)

     The per-stack ladder is the `stacks/ladders/<stack>.md` file that `stacks/stack-matrix.md`
     routes to; read only that one. Read `stacks/workspaces.md` first only when the repo has more
     than one manifest directory or a workspace file.
   - A script beats a derived command for the same gate. The script is the form the repo
     agreed to.
   - Never emit a command whose tool you could not prove is present.
   - A derived gate with no evidence of prior use (no script, no CI step, no doc mention) has an
     unknown baseline. It may already be red on untouched files. Emit it as
     `(derived, no baseline)`, and tell the worker to judge it only on the files the change
     touches. A pre-existing red is a finding, not a regression.
3. "No tests" is a finding, not a gap. Emit `test: NONE (verification is lint + typecheck +
   build + smoke)` and say so. Do not invent a runner, and do not propose one unasked.
4. Containers change the form. With a compose service whose build context is a code root,
   prefix that root's commands with `docker compose exec <service> `. If a `Makefile` or `justfile`
   already wraps them, that target is the agreed form; prefer it.
5. Mark destructive gates ⚠ and gate them on confirmation: `migrate:fresh`, `db:wipe`,
   `make clean`, `down -v`.
   - Everything the contract calls dangerous joins the ⚠ list, including flag variants such as
     an `--env=testing` that silently hits the dev database. Quote the contract's own warning.
6. Gates have side effects. Build output, caches, and a test database migrated or seeded. A
   prompt that is otherwise read-only must list those side effects as its only permitted writes.
   Don't let two sessions run a suite against the same test database at once, because each
   corrupts the other's state (§4.27).
7. The package manager comes from the lockfile, not habit: `pnpm-lock.yaml` → pnpm,
   `yarn.lock` → yarn, `bun.lockb`/`bun.lock` → bun, otherwise npm.
8. The generator never runs gates. It emits them for the worker, and it verifies the worker's
   numbers by reading artifacts (PROTOCOL Step 4).

### 2.6 Source-of-truth hierarchy

The first match wins; later rules append lower tiers.

- S1 Explicit. A contract file that declares an order (`source of truth|outranks|binding`).
  Parse it and use it verbatim.
- S2 Binding external document. A client- or funder-authored terms doc (a TOR, SOW,
  project-definition or requirements spec, often with a `.docx`/`.pdf` twin) comes first. Then
  numbered specs ascending, then the internal roadmap, then audits/reports (chronological,
  non-authoritative).
- **S3 `docs/*ROADMAP*.md` or task sheets:** contract files, then the roadmap, then its
  audit/report companions, then topical docs.
  - Where the roadmap and an audit disagree, check `git log -1 --format=%cI` on both and prefer
    the later.
  - Say which one you used.
- S4 `docs/README.md`: it is the index; rank by its own ordering.
- S5 No `docs/`, or fewer than 3 markdown files: contract, then `README.md`, then the code.
  Announce that the repo has no planning corpus.
- S6 Always demote. `README.md` drops below the contract whenever a staleness check hits it.
- S7 Freshness tiebreak. Within a tier, the newer last-commit date wins, or a self-dated
  header.

Every source-of-truth block you emit carries **authority annotations and at least one explicit
exclusion or staleness warning**. A flat numbered list implies equal weight, and it gets read that
way.

### 2.7 Naming new doc artifacts

Judge only against files the repo has actually produced.

- N1 Sprint series (`sprint-<N>-{plan,gap-audit,implementation-report}.md`, at least 2
  present): match it.
  - `N_next = N_max + 1`, unless `N_max` has a plan and no implementation report. Then `N_max`
    is in flight: continue it.
  - Write where the live sprints are, not where an old doc claims.
- N2 Numbered deliverables (`^[A-Z]{2,6}_\d{2}_.+\.md$`). Apply the binary-twin test:
  - If some numbered file has no `.docx`/`.pdf` twin, the repo mints its own numbers. The next one
    is `<PREFIX>_<NN+1>_<Title_Case>.md`.
  - If every numbered file has a twin, they are externally authored and read-only. **Do not
    mint a number.** Fall through to N3 or N6.
- N3 Roadmap companions: kebab-case siblings (`<topic>-implementation-report.md`). Copy the
  roadmap's own work-unit id style (`S<N>`, `P<N>`, `WS-A`/`A-03`, `BE07`, bare numeric) by reading
  it, not assuming it.
- N4 Dated audit folder (`docs/audit-YYYY-MM-DD/`): a new dated folder, split into parts.
- N5 Dominant case style. Count at least 3 repo-authored docs in `docs/` (or 5 at the root),
  ignoring externally authored ones with binary twins. If one case style dominates, name new docs
  in it: `SCREAMING_SNAKE`, `Title_Snake_Case` or `kebab-case`.
- N6 No signal: `docs/<kebab-topic>.md`. State in the prompt that you are establishing a
  convention.
- Default topic per archetype, rendered in whichever case style N1–N6 selects:

  | Archetype | Default topic |
  |---|---|
  | B | `assessment-<area>` |
  | F | `<unit>-plan` |
  | M | `repo-map` |
  | N | `adr-<nnn>-<topic>` or `<topic>-design` |
  | P | `code-review-<YYYY-MM-DD>` |
  | Q | `security-review-<area>` |
  | R | `performance-<area>` |
  | S | `upgrade-<package>-<to>` |
  | T | `release-runbook` |
  | U | `incident-<YYYY-MM-DD>-<topic>` |
  | W | named by the request |
- N7 Don't rename or renumber existing artifacts, because other docs cite them. History docs are
  append-only, everywhere.

### 2.8 Code root, forbidden trees, branch

Code roots are per stack (see `stacks/stack-matrix.md`). For example, a Laravel root is
`app routes database resources tests config`, not `app/` alone. Don't narrow to one folder when the
stack's convention spans several, because the rest of the stack then goes unread.

Forbidden is the union of:
- EXCLUDE
- build artifacts
- dead code the contract declares
- `docs/archive/**` (readable as evidence, never edited)
- vendored and generated sources (applied migrations are append-only)
- duplicate trees (`**/copy*/`, `/*-old/**`, a second manifest with a duplicate `name`)
- sibling-repo confusion. Where two repos share a doc corpus, a doc's presence does not make
  its content this repo's scope; take scope from this repo's own roadmap.

Mark deliberately inert features (flags off by design, commands scheduled nowhere) as *inert,
not dead*. The prompt must forbid "finishing" them without a ruling.

Branch.
- Default: `basename(git symbolic-ref refs/remotes/origin/HEAD)`. Otherwise probe
  `origin/main` and `origin/master`, and say it was inferred. A default other than `main` is
  normal.
- Ask if `origin/HEAD`, the checkout and the CI triggers contradict each other.
- A contract that forbids branch operations overrides any branching in the prompt.

### 2.9 The profile card

Cached at `~/.genprompt/generated-prompts/by-repo/<key>.profile.md`. The field names below are exactly what
`<PROFILE.x>` placeholders refer to.

```markdown
---
repo:     <DirName>
path:     <absolute path>
key:      <key>
derived:  <YYYY-MM-DD>
stamp:    <file>@<short sha> [dirty] ; <file>@<short sha> ...   # manifests + contract, via git log -1 --format=%h -- <file>
---
branch:          <current at derivation time>
default_branch:  <default> (inferred? yes/no)
scope:       <single root | monorepo roots, IN/OUT>
stack:       <stack label with versions>
role:        <role label, or the contract's persona verbatim>
contract:    <path> · hard rules: <one line each>
ancestors:   <paths | none found> · user-level: <present | unreadable | none>
truth:       <ordered list with authority notes>
docnaming:   <N-rule that applies, and the next name it would produce>
code_roots:  <dirs>
forbidden:   <trees>
blockers:    <the repo's own blocker list, short>
gates:       NOT CACHED: always re-derived at runtime (§2.5); <PROFILE.gates> means the derived list
```

Keys and invalidation.
- `key` = the directory basename, lowercased, with `_` and spaces turned into `-`.
- The key is only a filename; `path:` is the identity. If a key collides with a different path,
  suffix the key with `-2` and note it.
- Fresh means the stamps still hold. A card is fresh while every `stamp:` entry still matches
  `git log -1 --format=%h -- <file>` and no stamped file is dirty (`git status --porcelain <file>`).
  Invalidate the whole card as soon as one stamp moves. There is no fixed short TTL: a quiet repo's
  card can stay valid for weeks, because nothing it was derived from has changed.
- Hard ceiling: 90 days. Re-derive a card whose `derived` is more than 90 days old even if every
  stamp matches. Stamps cover the manifests and the contract, not everything the card reads (the
  ancestor scan, the user-level contract, CI triggers, docs naming), so a long-lived card can drift
  without any stamp moving. 90 days bounds that drift without re-deriving active repos for nothing.
- Gates are never cached. Freshness never extends to `gates:`; they are re-derived on every run
  (§2.5, PROTOCOL Step 2), whatever the card's age.
- Age. The card's age is `today − derived`, in days. It is what a reader reports next to the
  verdict, for example `card 37d, stamps fresh` or `card 12d, stale: composer.json moved`, so a
  long-reused card is visible. `derived` changes only when the card is re-derived.
- First use writes it. The first prompt for a repo that has no card derives the profile and
  writes the card to `by-repo/<key>.profile.md`, so the next run can reuse it. A stale or expired
  card is rewritten the same way. `--dry-run` never writes the card.
- Future work, not active: skipping the TARGET LOCK wait when the card is fresh ("auto-go") stays
  off until the archive's `lock=` data (PROTOCOL Step 6) shows that locks are rarely corrected.
- Why git shas and not mtimes: a checkout or pull changes mtimes without changing content.
