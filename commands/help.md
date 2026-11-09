---
description: "Which genprompt command fits my goal? Picker with flags and examples (no prompt)"
argument-hint: "[goal, e.g. 'I need to upgrade Laravel']"
allowed-tools: Read, Glob, Grep, Bash(cd:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git rev-list:*), Bash(git shortlog:*), Bash(git grep:*), Bash(git cat-file -p:*), Bash(git config --get:*), Bash(git worktree list:*), Bash(git stash list:*), Bash(git branch --show-current:*), Bash(git branch -a:*), Bash(git branch -r:*), Bash(git branch --list:*), Bash(git branch -vv:*), Bash(git remote -v:*), Bash(git remote get-url:*), Bash(git symbolic-ref refs/remotes/origin/HEAD:*), Bash(git symbolic-ref --short refs/remotes/origin/HEAD:*), Bash(ls:*), Bash(wc:*), Bash(tail:*), Bash(head:*), Bash(date:*)
---

@${CLAUDE_PLUGIN_ROOT}/utilities/help.md
@${CLAUDE_PLUGIN_ROOT}/archetypes/README.md
@${CLAUDE_PLUGIN_ROOT}/guide/08-grammar.md

Paths for this run: the genprompt root (these rules, read-only) is `${CLAUDE_PLUGIN_ROOT}`. The genprompt home (the archive and your personal rules) is `~/.genprompt/`.

Step 0: if any file listed here is missing from context, Read it now: `${CLAUDE_PLUGIN_ROOT}/utilities/help.md`, `${CLAUDE_PLUGIN_ROOT}/archetypes/README.md`, `${CLAUDE_PLUGIN_ROOT}/guide/08-grammar.md`. This utility does not need `PROTOCOL.md`; do not Read it. If `~/.genprompt/local-rules.md` exists, Read it (personal rules). Everything below assumes they are loaded.

Utility `/genprompt:help`: follow `utilities/help.md`. It emits no worker prompt.

Request: $ARGUMENTS
