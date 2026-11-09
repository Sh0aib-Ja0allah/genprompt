# Utility: `/genprompt:doctor [--suite|--archive|--suggest-fixes]`

Emits no worker prompt. Writes nothing.

1. Run exactly this, with the genprompt root that the command states, written the same way
   (forward slashes; quote the path only if it contains a space). The command is pre-approved in
   exactly this form:
   `python3 <genprompt root>/tools/doctor.py [--suite|--archive|--suggest-fixes]`
   If `python3` is missing or is only a store alias (common on Windows), run the same command with
   `python`. Don't `cd` first or chain it with another command, because only this exact form is
   pre-approved.
2. Summarise the output:
   - the ERROR count, with every ERROR line
   - the WARN count, with the top 10
   - the INFO counts grouped by kind (legacy drift)
   - the live library statistics the script prints (prompts per repo, per archetype, latest dates)
3. For each ERROR, say the fix:
   - a suite error means the installed plugin is damaged or out of date: suggest updating or
     reinstalling it (`/plugin`), or reporting the error as an issue on the genprompt repository.
     Never edit the genprompt root.
   - an archive error means a shard fix; show the exact row change. Never edit a prompt file.
4. The exit code is non-zero only on ERROR. Report it.
5. `--suggest-fixes` prints a repair plan for the archive ERRORs instead of the check: per row or
   file, the ERROR, the exact before -> after (or an instruction), and a tag: `derivable` (the right
   value follows from the archive itself) or `manual` (it does not; nothing is invented, e.g. a
   missing self-check "cannot be repaired automatically"). It also counts legacy label drift
   (`--verbose` lists it). It writes nothing and always exits 0. Relay its summary and the backup
   line; the user applies the plan, never you.

What doctor checks (the source of truth is the script itself):
- Suite:
  - every archetype has a command file in `commands/`, and every command file has an archetype
  - the command files match `tools/build_shims.py`, so the `allowed-tools` baseline is identical
    and the extra frontmatter (`EXTRA_FM`: `disable-model-invocation` on doctor, learn, history and
    profile, which stay typeable but leave the model's skill listing) is exactly as generated
  - each command's Write/Edit grants match PROTOCOL's write boundary exactly: prompt commands
    `~/.genprompt/generated-prompts/**` and `~/.genprompt/tmp/**`, `:learn` only
    `local-rules.md`, `:profile` only `generated-prompts/by-repo/**`, the rest none
  - the dispatch tools (ListAgents, SendMessage, for `--send`, §10.8) sit on the prompt commands
    only, never on a utility
  - § references resolve
  - the help table lists every command
  - letters are unique
  - stale strings are banned, and no rule file names one user's absolute home path
  - every command file loads the protocol, except the protocol-free utilities (`help`, `doctor`)
    listed in `PROTOCOL_FREE` in `tools/build_shims.py` (enforced by the generator comparison)
  - the Agensi bundle that `tools/build_skill_bundle.py` would build is current: its SKILL.md
    version and counts match plugin.json and the tables, and every runtime file (every routed
    stack ladder included) ships while CI, evals, tests and assets do not; checked in memory
- Archive:
  - shard rows point to files that exist
  - v3 files carry the line-1 header and a full fenced prompt
  - v3 rows follow the 5-field / ≤200-character / no-em-dash rule
  - keys are lowercase
  - profile staleness
  - `follows` links resolve
