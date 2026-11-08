# Roadmap

| ID | Package | Slice | Status |
|---|---|---|---|
| C-01 | ledger-core | `addCents` and `splitCents` | done |
| C-02 | ledger-core | Rounding modes for `splitCents`: `largest-remainder` (today) and `first-gets-rest` | next |
| W-05 | ledger-web | Dark theme for the invoice table | next (web team) |

## C-02 notes
- `splitCents(total, parts, mode)` keeps the sum exact in both modes.
- Unknown modes throw a `RangeError`.
