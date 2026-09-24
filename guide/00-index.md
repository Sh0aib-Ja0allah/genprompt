# genprompt v3: rulebook index

> **What this is.** The rulebook for generating the phase-driven Claude Code prompts that drive
> work across your repos. It encodes the structure that has held across a large archived
> library (target lock → grounding → scoped parts → gates → report), so every new prompt comes
> out consistent, grounded and copy-paste ready.
>
> **Two chats.** A **generator** chat (these rules; read-only on every repo) produces prompts. A
> **worker** chat (the repo open, full write access) executes them. The split is why the write
> boundary exists: keep it.
>
> **No repo table.** The target is resolved at runtime, and its profile is derived from the repo
> itself (§1, §2, `stacks/`). Nothing here needs editing when a new repo shows up.

## Section map

Section numbers are stable: prompts and commands cite them. The v2 single file was split along
them in v3.

| § | Topic | File |
|---|---|---|
| — | Runtime steps (was §9) | `PROTOCOL.md` |
| 0–2 | Invariants, target resolution, profile derivation, gates, truth, naming, branch, profile card | `guide/01-target-profile.md` |
| 2.3–2.5 (expanded) | Stack detection, role labels, per-stack gate ladders | `stacks/stack-matrix.md` |
| 3 | Core principles | `guide/02-principles.md` |
| 4 | Building blocks 4.0–4.27 | `guide/03-blocks.md` |
| 5 | Archetypes A–W | `archetypes/README.md` + `archetypes/<X>-<cmd>.md` |
| 6 | Emission checklist | `guide/04-checklist.md` |
| 7 | Anti-patterns | `guide/05-anti-patterns.md` |
| 8 | Request grammar and flags | `guide/08-grammar.md` |
| 10 | Prompt library (archive spec) | `guide/06-library.md` |
| 11 | Environment facts (general; yours go in `~/.genprompt/local-rules.md`) | `guide/07-environment.md` |
| 12 | Keeping this current | this file, below |
| — | Worked examples (illustrative only) | `examples/worked-examples.md` |
| — | Utility command specs | `utilities/<name>.md` |
| — | Integrity checker, and the command-file generator | `tools/doctor.py`, `tools/build_shims.py` |
| — | History | `CHANGELOG.md` |

## 12. Keeping this current

Strong turns end with `## The transferable rule from this turn`. In v2 nothing ever folded those
rules back, so the rules froze on the day they were written while the library kept learning.
**`/genprompt:learn` is that loop.** It has two levels:
- **Personal (every user):** `/genprompt:learn` saves the rule to `~/.genprompt/local-rules.md`,
  which every command reads. It never edits the plugin, so an update cannot erase it.
- **Upstream (everyone):** a rule that would help every user becomes a change to the suite itself,
  proposed as an issue or pull request against the genprompt repository. `:learn` offers a
  ready-to-paste issue for that.

**Where a lesson goes in the suite** (and the heading it takes in `local-rules.md`):

| Kind of lesson | Where it goes |
|---|---|
| A mechanism that failed, or a block that was missing | §4 (`guide/03-blocks.md`) |
| A class of mistake | §7 (`guide/05-anti-patterns.md`) |
| An environment surprise | §11 (`guide/07-environment.md`) |
| A shape that keeps repeating | §5 (a new or amended archetype) |
| A stack or gate fact | `stacks/stack-matrix.md` |

**Every change to the suite also:**
- adds a `CHANGELOG.md` entry
- regenerates the command files if a command changed (`python3 tools/build_shims.py`)
- passes `python3 tools/doctor.py --suite`

**Stability rules.**
- **Letters A–W keep their meaning forever.** Archived prompts reference them. A new archetype
  takes the next letter (X, Y, Z, then AA…).
- **Section numbers are never renumbered.** New blocks append (4.27…).
- **No library statistics in runtime files.** Counts rot. `/genprompt:doctor` computes live
  numbers on demand.
