---
name: commit
description: genprompt commit against the ledgerlite fixture
tags: [baseline, commit]
runs: 1
max_turns: 80
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep]
---

/genprompt:commit S-02 CSV export (checkpoint B) is finished in the working tree; commit it on the current branch and do not push --go --dry-run
