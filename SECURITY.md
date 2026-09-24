# Security policy

genprompt is designed to be **read-only on your repos**. Its commands pre-approve only file reads,
read-only git and listing commands, and writes under `~/.genprompt/`. It sends no data anywhere.

## What counts as a vulnerability

- A command that can write outside `~/.genprompt/`, or run a build, test, install or mutating git
  command without your approval
- A pre-approved tool rule that is broader than it needs to be
- Anything that could make the generator leak repo content to a third party
- A way for a malicious repo (for example, its `CLAUDE.md` or files) to make the generator break
  these guarantees

## Reporting

Please **do not open a public issue**. Report it privately through GitHub:
**Security → Report a vulnerability** on this repository
([direct link](https://github.com/Sh0aib-Ja0allah/genprompt/security/advisories/new)).

Include the command, what it did, and how to reproduce it, with private details removed. You will
get an answer within 7 days. Fixes ship in a new release, and the advisory credits you unless you
prefer otherwise.

## Supported versions

Only the latest release gets fixes. Update with `/plugin` in Claude Code.
