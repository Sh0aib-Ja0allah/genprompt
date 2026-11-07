---
name: plan
description: genprompt plan against the ledgerlite fixture
tags: [baseline, plan]
runs: 1
max_turns: 80
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep]
---

/genprompt:plan S-03 tax lines from docs/ROADMAP.md: a per-line VAT rate and a tax subtotal, totals still in integer cents --go --dry-run
