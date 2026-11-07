# ledgerlite

A tiny invoice calculator. Made up for genprompt's evals; it is not a real project.

```
npm test          # node's built-in test runner
npm run lint      # scripts/lint.js
npm start -- examples/sample.json --lines
```

Invoices are JSON: `{ "lines": [{ "label", "qty", "unitCents" }], "discountPct" }`.
See `docs/ROADMAP.md` for planned slices.
