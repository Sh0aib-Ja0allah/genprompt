---
name: investigate
description: genprompt investigate against the ledgerlite fixture
tags: [extra, investigate]
runs: 1
max_turns: 80
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep]
---

/genprompt:investigate `npm start -- examples/sample.json --lines` prints each line's amount as expected (25.00, 40.00 and 5.00 EUR) but TOTAL 40.50 EUR, where 63.00 EUR (70.00 less the 10% discount) is expected; the cause is unknown --go --dry-run
