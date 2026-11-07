<!-- genprompt v3: key=lint-demo | repo=lint-demo | path=/srv/repos/lint-demo | date=2026-10-07 | archetype=D | follows=- -->

| Field | Value |
|---|---|
| Repo | lint-demo, branch main |
| Archetype | D: Slice execution |

Grounding: the gates come from package.json:7-9 (fixture).

````text
Repo: /srv/repos/lint-demo, branch main. Contract: CLAUDE.md governs.

NOW: Slice S02, add the settings page.

MODE FOR THIS SESSION: work through the checkpoints without asking.

VERIFY AT START:
- git status is clean: check with `git status --porcelain`, expect no output.

CHECKPOINT A: settings page
BUILD: the page and its route.
GATE: npm test (script) · npm run lint (script)
Example of a nested block the worker may need:
```bash
git show {sha}:{path}
```
COMMIT: stage by path.

WHAT YOU CANNOT DO: push, or edit files outside src/settings/.
REPORT: gates with real numbers, git status, negative confirmations.

Start with CHECKPOINT A now.
````

| # | Item | Verdict | Reason |
|---|---|---|---|
| 21 | Length | PASS | 24 lines, Slice cap 260 |
