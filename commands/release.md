---
description: "Release or deploy: version, changelog, runbook, smoke, rollback, approvals (worker prompt)"
argument-hint: "<version | environment | handover>   [--repo <name|path>] [--go] [--attended|--unattended] [--dry-run] [--brief] [--follows <file>] [--verbose]"
allowed-tools: Read, Glob, Grep, Write(~/.genprompt/**), Edit(~/.genprompt/**), Bash(cd:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git rev-list:*), Bash(git shortlog:*), Bash(git grep:*), Bash(git cat-file -p:*), Bash(git config --get:*), Bash(git worktree list:*), Bash(git stash list:*), Bash(git branch --show-current:*), Bash(git branch -a:*), Bash(git branch -r:*), Bash(git branch --list:*), Bash(git branch -vv:*), Bash(git remote -v:*), Bash(git remote get-url:*), Bash(git symbolic-ref refs/remotes/origin/HEAD:*), Bash(git symbolic-ref --short refs/remotes/origin/HEAD:*), Bash(ls:*), Bash(wc:*), Bash(tail:*), Bash(head:*), Bash(date:*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python3 "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*), Bash(python ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*)
---

@${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md
@${CLAUDE_PLUGIN_ROOT}/archetypes/T-release.md
@${CLAUDE_PLUGIN_ROOT}/guide/blocks/T-release.md

Paths for this run: the genprompt root (these rules, read-only) is `${CLAUDE_PLUGIN_ROOT}`. The genprompt home (the archive and your personal rules) is `~/.genprompt/` unless Step 0's `archive.py --where` prints another.

Step 0: the files listed above are already in your context: their text follows the `@` lines, and PROTOCOL.md's third line contains `GENPROMPT-PROTOCOL v3 LOADED`. Do not Read them again. Read one only if its text is truly absent from your context (for example, the marker is nowhere above): `${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md`, `${CLAUDE_PLUGIN_ROOT}/archetypes/T-release.md`, `${CLAUDE_PLUGIN_ROOT}/guide/blocks/T-release.md`. Then run `python3 ${CLAUDE_PLUGIN_ROOT}/tools/archive.py --where` once (if `python3` is missing or only a store alias, run the same command with `python`). Its `home` line is the genprompt home as an absolute path: use it wherever these rules write `~/.genprompt/`, and for every Write. If its `local-rules` line says `present`, Read that file (personal rules, see PROTOCOL). Everything below assumes they are loaded.

Command `/genprompt:release` → archetype **T: Release and deploy** (§5.T). Follow PROTOCOL Steps 1–7 with this archetype. If the request is really a different archetype, say so in the TARGET LOCK and use the right one (hybrids are fine).

Request: $ARGUMENTS
