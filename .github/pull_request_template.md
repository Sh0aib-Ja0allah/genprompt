## What this changes

<!-- One rule change per PR. Which file and section, and why. -->

## Checklist

- [ ] `python3 tools/doctor.py --suite` reports 0 ERROR
- [ ] If a command was added or renamed: tables edited in `tools/build_shims.py`, then `python3 tools/build_shims.py` run (no hand edits in `commands/`)
- [ ] A `CHANGELOG.md` line: `- <YYYY-MM-DD> · <file> · <what and why>`
- [ ] No section renumbered and no archetype re-lettered
- [ ] No project names, personal paths, private code or secrets
- [ ] The generator stays read-only on repos (writes only under `~/.genprompt/`)
