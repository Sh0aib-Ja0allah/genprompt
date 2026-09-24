# Changelog

One line per rule change: `- <YYYY-MM-DD> · <file> · <what changed and why>`.

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
