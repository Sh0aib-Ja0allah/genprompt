# Utility: `/genprompt:doctor [--suite|--archive]`

Emits no worker prompt. Writes nothing.

1. **Run exactly this**, with the genprompt root that the command states, written the same way
   (forward slashes; quote the path only if it contains a space). The command is pre-approved in
   exactly this form:
   `python3 <genprompt root>/tools/doctor.py [--suite|--archive]`
   If `python3` is missing or is only a store alias (common on Windows), run the same command with
   `python`. Never `cd` first, and never chain it with another command.
2. **Summarise the output:**
   - the ERROR count, with every ERROR line
   - the WARN count, with the top 10
   - the INFO counts grouped by kind (legacy drift)
   - the live library statistics the script prints (prompts per repo, per archetype, latest dates)
3. **For each ERROR, say the fix:**
   - a suite error means the installed plugin is damaged or out of date: suggest updating or
     reinstalling it (`/plugin`), or reporting the error as an issue on the genprompt repository.
     Never edit the genprompt root.
   - an archive error means a shard fix; show the exact row change. Never edit a prompt file.
4. **The exit code is non-zero only on ERROR.** Report it.

**What doctor checks** (the source of truth is the script itself):
- **Suite:**
  - every archetype has a command file in `commands/`, and every command file has an archetype
  - the command files match `tools/build_shims.py`, so the `allowed-tools` baseline is identical
  - § references resolve
  - the help table lists every command
  - letters are unique
  - stale strings are banned, and no rule file names one user's absolute home path
  - every command file loads the protocol
- **Archive:**
  - shard rows point to files that exist
  - v3 files carry the line-1 header and a full fenced prompt
  - v3 rows follow the 5-field / ≤200-character / no-em-dash rule
  - keys are lowercase
  - profile staleness
  - `follows` links resolve
