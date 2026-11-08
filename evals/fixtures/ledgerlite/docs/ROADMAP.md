# Roadmap

| ID | Slice | Status |
|---|---|---|
| S-01 | Line totals, discount and the CLI | done |
| S-02 | CSV export: `--csv` writes one row per line item plus a TOTAL row | next |
| S-03 | Tax lines: per-line VAT rate, a tax subtotal, totals still integer cents | later |
| S-04 | Multi-currency: refuse to sum lines in different currencies | later |

## S-02 notes
- Output goes to stdout. Columns: label, qty, unitCents, lineCents.
- Labels containing commas or quotes must be quoted per RFC 4180.
- Reuse `lineTotal` from `src/invoice.js`; no new dependencies.
