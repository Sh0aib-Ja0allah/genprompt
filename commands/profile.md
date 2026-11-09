---
description: "Derive or refresh a repo's genprompt profile card (no prompt)"
argument-hint: "[repo] [--dry-run]"
allowed-tools: Read, Glob, Grep, Write(~/.genprompt/generated-prompts/by-repo/**), Edit(~/.genprompt/generated-prompts/by-repo/**), Bash(cd:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git rev-list:*), Bash(git shortlog:*), Bash(git grep:*), Bash(git cat-file -p:*), Bash(git config --get:*), Bash(git worktree list:*), Bash(git stash list:*), Bash(git branch --show-current:*), Bash(git branch -a:*), Bash(git branch -r:*), Bash(git branch --list:*), Bash(git branch -vv:*), Bash(git remote -v:*), Bash(git remote get-url:*), Bash(git symbolic-ref refs/remotes/origin/HEAD:*), Bash(git symbolic-ref --short refs/remotes/origin/HEAD:*), Bash(ls:*), Bash(wc:*), Bash(tail:*), Bash(head:*), Bash(date:*)
disable-model-invocation: true
---

@${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md
@${CLAUDE_PLUGIN_ROOT}/utilities/profile.md
@${CLAUDE_PLUGIN_ROOT}/guide/01-target-profile.md
@${CLAUDE_PLUGIN_ROOT}/stacks/stack-matrix.md

Paths: the genprompt root (read-only rules) is `${CLAUDE_PLUGIN_ROOT}`.

Step 0: the files above are already in context (their text follows the `@` lines; PROTOCOL's third line says `GENPROMPT-PROTOCOL v3 LOADED`). Don't Read them again unless that marker is absent. Then run `ls -d ~ ~/.genprompt/local-rules.md` once: it prints your absolute home (for every Write); if `local-rules.md` exists, Read it.

Utility `/genprompt:profile`: follow `utilities/profile.md`. It emits no worker prompt.

Request: $ARGUMENTS
