# CSV export

`ledgerlite <invoice.json> --csv` prints the invoice as CSV on stdout.

Columns: `label,qty,unitCents,lineCents`, then a `TOTAL` row with the discounted total in cents.
Labels with commas or quotes are quoted per RFC 4180.
