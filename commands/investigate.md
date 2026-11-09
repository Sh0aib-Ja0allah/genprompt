---
description: "Find the root cause of a bug with unknown cause: repro, trace, path:line (worker prompt)"
argument-hint: "<symptom: what happens vs expected, and how to trigger it>   [--repo <name|path>] [--go] [--dry-run] [--brief] [--follows <file>] [--send <session>] [--verbose]"
allowed-tools: Read, Glob, Grep, Write(~/.genprompt/generated-prompts/**), Edit(~/.genprompt/generated-prompts/**), Write(~/.genprompt/tmp/**), Edit(~/.genprompt/tmp/**), Bash(cd:*), Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git show:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git rev-list:*), Bash(git shortlog:*), Bash(git grep:*), Bash(git cat-file -p:*), Bash(git config --get:*), Bash(git worktree list:*), Bash(git stash list:*), Bash(git branch --show-current:*), Bash(git branch -a:*), Bash(git branch -r:*), Bash(git branch --list:*), Bash(git branch -vv:*), Bash(git remote -v:*), Bash(git remote get-url:*), Bash(git symbolic-ref refs/remotes/origin/HEAD:*), Bash(git symbolic-ref --short refs/remotes/origin/HEAD:*), Bash(ls:*), Bash(wc:*), Bash(tail:*), Bash(head:*), Bash(date:*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python3 "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*), Bash(python ${CLAUDE_PLUGIN_ROOT}/tools/archive.py:*), Bash(python "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*), ListAgents
---

@${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md
@${CLAUDE_PLUGIN_ROOT}/archetypes/X-investigate.md
@${CLAUDE_PLUGIN_ROOT}/guide/blocks/X-investigate.md

Paths: the genprompt root (read-only rules) is `${CLAUDE_PLUGIN_ROOT}`.

Step 0: the files above are in context. Read them again only if PROTOCOL's `GENPROMPT-PROTOCOL v3 LOADED` marker is absent. First Bash call, alone and unchained: `python3 "${CLAUDE_PLUGIN_ROOT}/tools/archive.py" --where`. No output or an error (exit 49: Store alias): once more with `python`, alone. Its `home` line is the absolute home for every `~/.genprompt/` path and Write. `local-rules` says `present`: Read that file. Then git and other reads, one per call.

Command `/genprompt:investigate` → archetype **X: Investigate / root cause** (§5.X): follow PROTOCOL Steps 1–7. Another archetype fits better? Say so in the lock and use it (hybrids are fine).

Request: $ARGUMENTS
