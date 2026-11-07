---
name: redesign
description: genprompt redesign against the ledgerlite fixture
tags: [baseline, redesign]
runs: 1
max_turns: 80
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep]
---

/genprompt:redesign src/cli.js: split argument parsing, validation and printing into small functions; keep the CLI's output and exit codes identical --go --dry-run
