---
description: "Audit an area read-only: one doc with a ranked backlog, no code (worker prompt)"
argument-hint: "<area to assess>   [--repo <name|path>] [--go] [--dry-run] [--brief] [--follows <file>] [--verbose]"
allowed-tools: Read, Glob, Grep, Write(~/.genprompt/generated-prompts/**), Edit(~/.genprompt/generated-prompts/**), Write(~/.genprompt/tmp/**), Edit(~/.genprompt/tmp/**), Bash(cd:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git rev-list:*), Bash(git shortlog:*), Bash(git grep:*), Bash(git cat-file -p:*), Bash(git config --get:*), Bash(git worktree list:*), Bash(git stash list:*), Bash(git branch --show-current:*), Bash(git branch -a:*), Bash(git branch -r:*), Bash(git branch --list:*), Bash(git branch -vv:*), Bash(git remote -v:*), Bash(git remote get-url:*), Bash(git symbolic-ref refs/remotes/origin/HEAD:*), Bash(git symbolic-ref --short refs/remotes/origin/HEAD:*), Bash(ls:*), Bash(wc:*), Bash(tail:*), Bash(head:*), Bash(date:*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python3 "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*), Bash(python ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*)
---

@${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md
@${CLAUDE_PLUGIN_ROOT}/archetypes/B-audit.md
@${CLAUDE_PLUGIN_ROOT}/guide/blocks/B-audit.md

Paths for this run: the genprompt root (these rules, read-only) is `${CLAUDE_PLUGIN_ROOT}`. The genprompt home (the archive and your personal rules) is `~/.genprompt/` unless Step 0's `archive.py --where` prints another.

Step 0: the files listed above are already in your context: their text follows the `@` lines, and PROTOCOL.md's third line contains `GENPROMPT-PROTOCOL v3 LOADED`. Do not Read them again. Read one only if its text is truly absent from your context (for example, the marker is nowhere above): `${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md`, `${CLAUDE_PLUGIN_ROOT}/archetypes/B-audit.md`, `${CLAUDE_PLUGIN_ROOT}/guide/blocks/B-audit.md`. Then run `python3 ${CLAUDE_PLUGIN_ROOT}/tools/archive.py --where` once (if `python3` is missing or only a store alias, run the same command with `python`). Its `home` line is the genprompt home as an absolute path: use it wherever these rules write `~/.genprompt/`, and for every Write. If its `local-rules` line says `present`, Read that file (personal rules, see PROTOCOL). Everything below assumes they are loaded.

Command `/genprompt:audit` → archetype **B: Audit / read-only assessment** (§5.B). Follow PROTOCOL Steps 1–7 with this archetype. If the request is really a different archetype, say so in the TARGET LOCK and use the right one (hybrids are fine).

Request: $ARGUMENTS
