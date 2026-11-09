---
description: "Rule on findings, lock decisions, or amend a sent prompt (worker prompt)"
argument-hint: "decisions: <list>; order: <...>  |  amend <prior prompt>   [--repo <name|path>] [--go] [--attended|--unattended] [--dry-run] [--brief] [--follows <file>] [--send <session>] [--verbose]"
allowed-tools: Read, Glob, Grep, Write(~/.genprompt/generated-prompts/**), Edit(~/.genprompt/generated-prompts/**), Write(~/.genprompt/tmp/**), Edit(~/.genprompt/tmp/**), Bash(cd:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git rev-list:*), Bash(git shortlog:*), Bash(git grep:*), Bash(git cat-file -p:*), Bash(git config --get:*), Bash(git worktree list:*), Bash(git stash list:*), Bash(git branch --show-current:*), Bash(git branch -a:*), Bash(git branch -r:*), Bash(git branch --list:*), Bash(git branch -vv:*), Bash(git remote -v:*), Bash(git remote get-url:*), Bash(git symbolic-ref refs/remotes/origin/HEAD:*), Bash(git symbolic-ref --short refs/remotes/origin/HEAD:*), Bash(ls:*), Bash(wc:*), Bash(tail:*), Bash(head:*), Bash(date:*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python3 "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*), Bash(python ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*), ListAgents, SendMessage
---

@${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md
@${CLAUDE_PLUGIN_ROOT}/archetypes/E-approve.md
@${CLAUDE_PLUGIN_ROOT}/guide/blocks/E-approve.md

Paths: the genprompt root (read-only rules) is `${CLAUDE_PLUGIN_ROOT}`.

Step 0: the files above are already in context (their text follows the `@` lines; PROTOCOL's third line says `GENPROMPT-PROTOCOL v3 LOADED`). Don't Read them again unless that marker is absent. Then run `python3 ${CLAUDE_PLUGIN_ROOT}/tools/archive.py --where` once (`python` if `python3` is missing or a store alias): its `home` line is the absolute home for every `~/.genprompt/` path and Write; if its `local-rules` line says `present`, Read that file.

Command `/genprompt:approve` → archetype **E: Approval / rulings / amendment** (§5.E): follow PROTOCOL Steps 1–7. If the request is really another archetype, say so in the lock and use it (hybrids are fine).

Request: $ARGUMENTS
