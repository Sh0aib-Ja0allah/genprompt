---
name: slice-monorepo
description: genprompt slice-monorepo against the tallyhub fixture
tags: [extra, slice-monorepo]
runs: 1
max_turns: 80
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep]
---

/genprompt:slice Slice C-02, scope: rounding modes for splitCents in ledger-core as described in docs/ROADMAP.md (`largest-remainder` and `first-gets-rest`, unknown modes throw) --go --dry-run
