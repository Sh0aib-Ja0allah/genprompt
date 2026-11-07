---
name: fix
description: genprompt fix against the ledgerlite fixture
tags: [baseline, fix]
runs: 1
max_turns: 80
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep]
---

/genprompt:fix invoice totals are too low: `npm start -- examples/sample.json` prints TOTAL 40.50 EUR, but 2x12.50 + 40.00 + 5.00 = 70.00 minus 10% is 63.00 EUR --go --dry-run
