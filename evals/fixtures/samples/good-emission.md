TARGET LOCK (printed under --go; not waiting)

```text
Repo        ledgerlite · (the eval workspace) · branch main · via cwd
Gates       npm test (script) · npm run lint (script)
Archetype   D: Slice execution · autonomy MODE
```

| | |
|---|---|
| Archetype | D: Slice execution |

````text
Repo: ledgerlite, branch main. Cut `feat/s-02-csv-export` from main first (CLAUDE.md:6).
CLAUDE.md governs and wins over this prompt.

TASK: implement slice S-02 (CSV export) from docs/ROADMAP.md:6, and nothing else.

SKEPTICISM: `npm test` is green today, yet src/invoice.js:14 starts the subtotal loop at
i = 1 and drops the first line item. test/invoice.test.js has no multi-line case, so a green
run proves nothing about totals. Check the TOTAL row by hand against examples/sample.json.

SCOPE: implement only `--csv` in src/cli.js and a new src/csv.js. Do not start S-03 or S-04.
Do not fix src/invoice.js:14 in this slice; report it.

GATES (literal, in order):
```
npm test
npm run lint
```
Baseline: 6 tests pass today; expect at least 8 after the slice. Report actual numbers.

GIT: stage by explicit path, commit with `feat:` subjects, never push.

REPORT: the gate numbers, the SHAs, and `git status --porcelain` (must be clean).
Begin with the branch.
````

Self-check: 21 PASS · 2 N/A · 0 FAIL

| # | Item | Verdict | Reason |
|---|---|---|---|
| 6 | Skepticism | N/A | example row only |
| 22 | Archived | N/A | dry run |

DRY RUN: nothing archived
