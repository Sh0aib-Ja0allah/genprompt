---
description: "Check the genprompt rules suite and prompt archive for integrity errors (no prompt)"
argument-hint: "[--suite | --archive | --suggest-fixes]"
allowed-tools: Read, Glob, Grep, Bash(cd:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git rev-list:*), Bash(git shortlog:*), Bash(git grep:*), Bash(git cat-file -p:*), Bash(git config --get:*), Bash(git worktree list:*), Bash(git stash list:*), Bash(git branch --show-current:*), Bash(git branch -a:*), Bash(git branch -r:*), Bash(git branch --list:*), Bash(git branch -vv:*), Bash(git remote -v:*), Bash(git remote get-url:*), Bash(git symbolic-ref refs/remotes/origin/HEAD:*), Bash(git symbolic-ref --short refs/remotes/origin/HEAD:*), Bash(ls:*), Bash(wc:*), Bash(tail:*), Bash(head:*), Bash(date:*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py:*), Bash(python3 "${CLAUDE_PLUGIN_ROOT}/tools/doctor.py":*), Bash(python ${CLAUDE_PLUGIN_ROOT}/tools/doctor.py:*), Bash(python "${CLAUDE_PLUGIN_ROOT}/tools/doctor.py":*)
disable-model-invocation: true
---

@${CLAUDE_PLUGIN_ROOT}/utilities/doctor.md

Paths: the genprompt root (read-only rules) is `${CLAUDE_PLUGIN_ROOT}`.

Step 0: if any file listed here is missing from context, Read it now: `${CLAUDE_PLUGIN_ROOT}/utilities/doctor.md`. This utility does not need `PROTOCOL.md`; do not Read it. If `~/.genprompt/local-rules.md` exists, Read it (personal rules). Everything below assumes they are loaded.

Utility `/genprompt:doctor`: follow `utilities/doctor.md`. It emits no worker prompt.

Request: $ARGUMENTS
