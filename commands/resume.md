---
description: "Resume a worker that lost context after compaction: rebuild it, continue (worker prompt)"
argument-hint: "<unit/slice the worker was mid-way through>   [--repo <name|path>] [--go] [--attended|--unattended] [--dry-run] [--brief] [--follows <file>] [--verbose]"
allowed-tools: Read, Glob, Grep, Write(~/.genprompt/**), Edit(~/.genprompt/**), Bash(cd:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git rev-list:*), Bash(git shortlog:*), Bash(git grep:*), Bash(git cat-file -p:*), Bash(git config --get:*), Bash(git worktree list:*), Bash(git stash list:*), Bash(git branch --show-current:*), Bash(git branch -a:*), Bash(git branch -r:*), Bash(git branch --list:*), Bash(git branch -vv:*), Bash(git remote -v:*), Bash(git remote get-url:*), Bash(git symbolic-ref refs/remotes/origin/HEAD:*), Bash(git symbolic-ref --short refs/remotes/origin/HEAD:*), Bash(ls:*), Bash(wc:*), Bash(tail:*), Bash(head:*), Bash(date:*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python3 "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*), Bash(python ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*)
---

@${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md
@${CLAUDE_PLUGIN_ROOT}/archetypes/K-resume.md
@${CLAUDE_PLUGIN_ROOT}/guide/blocks/K-resume.md

Paths for this run: the genprompt root (these rules, read-only) is `${CLAUDE_PLUGIN_ROOT}`. The genprompt home (the archive and your personal rules) is `~/.genprompt/`.

Step 0: the files listed above are already in your context: their text follows the `@` lines, and PROTOCOL.md's third line contains `GENPROMPT-PROTOCOL v3 LOADED`. Do not Read them again. Read one only if its text is truly absent from your context (for example, the marker is nowhere above): `${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md`, `${CLAUDE_PLUGIN_ROOT}/archetypes/K-resume.md`, `${CLAUDE_PLUGIN_ROOT}/guide/blocks/K-resume.md`. Then run `ls -d ~ ~/.genprompt/local-rules.md` once: it prints your absolute home directory (use it for every Write), and if `local-rules.md` exists, Read it (personal rules, see PROTOCOL). Everything below assumes they are loaded.

Command `/genprompt:resume` → archetype **K: Resume after compaction** (§5.K). Follow PROTOCOL Steps 1–7 with this archetype. If the request is really a different archetype, say so in the TARGET LOCK and use the right one (hybrids are fine).

Request: $ARGUMENTS
