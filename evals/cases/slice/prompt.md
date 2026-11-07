---
name: slice
description: genprompt slice against the ledgerlite fixture
tags: [baseline, slice]
runs: 1
max_turns: 80
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep]
---

/genprompt:slice Slice S-02, scope: CSV export as described in docs/ROADMAP.md (a --csv flag, RFC 4180 quoting, one row per line item plus a TOTAL row) --go --dry-run
