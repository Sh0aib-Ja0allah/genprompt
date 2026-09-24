## 6. Emission checklist

Run it before archiving. It is written into the archive file and printed under the prompt.

**Format:** `| # | Item | Verdict | Reason |`.
- Verdict is `PASS`, `FAIL` or `N/A`.
- **Every** row carries a reason: short for PASS, and mandatory for N/A and FAIL.
- Never write a bare `✓ passed`, and never bulk-pass rows ("2,3,5 carried from r2").
- A FAIL is fixed before emitting. Otherwise the reason says why the prompt ships anyway.
- **Read-only and commit-only archetypes** (B, F, H, M, N, P, W) meet the code-writing rows in their
  own terms; each row below says how.

| # | Item |
|---|---|
| 1 | The target is resolved, and **how** is stated (argument / continuation / cwd / ask). Any conflict is shown in the lock, or in the printed lock facts under `--go` |
| 2 | The repo anchor is absolute, with the branch. In a monorepo: the in-scope root, and the out-of-scope siblings named |
| 3 | One sharp task statement at the top |
| 4 | The conventions contract is named and given precedence, and its hard rules are pointed to (branching / deploy / push / logging). Ancestors are **scanned** (the four names in every ancestor, plus the user-level file) and the result is stated literally. No unscanned file is named |
| 5 | The source-of-truth order has authority annotations and at least one exclusion or staleness warning. Every `@ref` and path exists |
| 6 | Skepticism carries a concrete falsifying artifact from THIS repo. N/A only for a delta E/J prompt whose running prompt already carries one |
| 7 | Every load-bearing claim is grounded at `file:line` (at a named SHA when the tree is occupied or the prompt reviews a range). Unverified claims are marked `[UNVERIFIED]`. No path, script, line, SHA or count is invented |
| 8 | **Literal gates are in this prompt**, each labelled `(script)`/`(contract)`/`(derived)` (plus `no baseline` where true). `test: NONE` is stated if true, and ⚠ marks every destructive command including the contract's own. There is no "same as last time". Gates with side effects in an otherwise read-only prompt list those side effects |
| 9 | The baseline is stated with its **expected delta** (up / unchanged / down with a reason), plus the honesty clause ("report actual numbers, not 'passes'"). For read-only prompts: the reported baseline at the reviewed state, with an expected delta of unchanged |
| 10 | Scope is bounded negatively. Code-writing: "implement only…", "do not start… yet", out-of-scope named by path. Read-only: the exact range/area, what is skipped and why, and the lenses dropped |
| 11 | Autonomy is resolved: for a code-writing archetype, an approval gate **xor** a MODE block; otherwise `N/A: read-only / commit-only`, with the writes enumerated (including contract-mandated tools and gate side effects) |
| 12 | Git posture is explicit and matches the contract, or the deviation is declared. Code-writing: branch, commit cadence, staging by path, push or not. Read-only: "no git writes" with the forbidden verbs listed |
| 13 | The stop-list covers what must not be faked, each item with what it blocks and what would unblock it |
| 14 | The report spec has negative confirmations and a `git status` reconciliation (for an occupied tree: "differs only in the live session's paths") |
| 15 | A terminal imperative is present |
| 16 | Exactly one fenced block (a 4-backtick outer fence if the prompt nests fences). Every `<…>` generator placeholder is filled and every `[generator: …]` is stripped. Worker-side variables use `{…}`. The user has nothing to edit |
| 17 | Doc paths match the derived convention (§2.7), or the report is chat-only with the reason. No artifact is renamed or renumbered |
| 18 | If it follows, amends, depends on or reviews prior prompts: the relationship is in the header, and the prior instruction is **confirmed landed on the branch** (not from the report). Partially landed work is said to be partial |
| 19 | Every claimed number (from a worker report or commit messages) is re-read and labelled `verified by artifact` or `reported, not confirmed`. The generator ran nothing |
| 20 | Hygiene: no example specifics have leaked (from `examples/` or another repo). Volatile facts sit in §4.22 verify-at-start, with expected drift marked. There is no hardcoded attribution trailer and no finality claim. The occupancy check was done, and §4.27 is applied if the tree is occupied |
| 21 | The length is within the archetype's budget (§4.21, lines ≤ 100 characters), or the measured-large allowance or another reason is given here |
| 22 | Archived: line-1 header, §4.1 table, grounding, full block and this table in `~/.genprompt/generated-prompts/<key>/<file>`; a 5-field shard row appended below the last line (≤200 characters, no `\|`, `·` or em-dash). For `--dry-run`: N/A, with "dry run" as the reason, and no profile card written |

---
