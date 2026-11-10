# CP8 (1.4.0, eval freeze `7af76de`): restart pending on a new candidate (02a5619 stopped at the L1 privacy grep)

| | |
|---|---|
| Spend | **$0.5083 of $11.50** |
| Status | **Shoaib ruled (a): fix now and restart CP8.** A extends LOCK-UL to "never name the user-level directory anywhere in the output, including explanations". That's shared text, so there'll be a new candidate, and the full CP8 re-runs from L1 under the same eval freeze (7af76de), rules, guards and cap. Running total carried: $0.5083. Waiting for the merged SHA. |
| 02a5619 (superseded) | L1 load PASSES every gate. The Z-1 privacy grep after L1 found **1 real-home hit** (redesign r1, final message). Q-e: any hit stops. L2, L3 and quality were not run |

## L1, card-less 5×3 (`--home empty`, dry-run): load PASS

`C:/genprompt-probe/genprompt-probe-20261110-002344/`, $0.5083, A1 PASS, A5 PASS.

| Case | per-run rule bytes | median | derive.md | L1 limit (v1.3.1 deriving + 2%; n) | result |
|---|---|---|---|---|---|
| slice | 37,640 ×3 | 37,640 | 3/3 | 38,433 (n=3) | PASS |
| fix | 38,423 ×3 | 38,423 | 3/3 | 39,231 (n=3) | PASS |
| redesign | 37,081 ×3 | 37,081 | 3/3 | 37,862 (**n=1**) | PASS |
| plan | 34,882 ×3 | 34,882 | 3/3 | 35,715 (**n=2**) | PASS; over v1.1.0's 30,615 (reported, the first-use cost) |
| investigate | 40,478 ×3 | 40,478 | 3/3 | 41,428 (n=3) | PASS; R1: over 40,000 by 478 (reported) |

- **Always derives: 15/15** card-less runs read derive.md, against 11/15 in v1.3.1. The 1.3.1
  known issue (i) is gone in this sample.
- Every median matches the plan's floor + derive.md expectation to within 3 B.

## Z-1 privacy grep after L1: **1 hit → STOP**

| Where | slice | fix | redesign | plan | investigate |
|---|---|---|---|---|---|
| parts (emitted prompts) | 0/2 | 0/1 | 0/3 | 0/2 | 0/3 |
| final messages | 0/3 | 0/3 | **1/3** | 0/3 | 0/3 |
| cards, archives, shards | none (dry-run writes none) | | | | |

- **The hit:** redesign r1's final message, line 179 of 181, outside every fence, in the closing
  notes after the prompt: `- Permission to read <REALHOME>\.claude was denied, so user-level is reported as unreadable.`
- **What 1.4.0 got right:** the lock and card slot say `unreadable`, as LOCK-UL requires. The emitted
  prompt (parts file) is clean.
- **What it missed:** the run then explains *why* in free text, naming the denied directory under the
  real home. That's the LOCK-UL class (a user-level path) in a fourth place: the closing notes.
  1.4.0's rule covers the lock, the card slot and the grounding notes.
- **Exposure:** the text is in the generator's chat to its own user. It isn't in the emitted prompt,
  isn't archived (dry-run), and isn't sent to a worker. A non-dry-run archive stores grounding notes,
  not these closing notes; L3 would show whether they're stored.
- **No remedy taken.** Per the plan, any hit stops.

## Restart on `aa96986` (02a5619 + f68a0b8, LOCK-UL in all output): L1 **FAIL A5. STOPPED**

`C:/genprompt-probe/genprompt-probe-20261110-012950/`, **$0.5181**. Running total: **$1.0264 of $11.50**.

| Case | per-run rule bytes | median | derive.md | L1 limit (n) | load |
|---|---|---|---|---|---|
| slice | 37,679 ×3 | 37,679 | 3/3 | 38,433 (3) | PASS |
| fix | 38,462 ×3 | 38,462 | 3/3 | 39,231 (3) | PASS |
| redesign | 37,120 ×3 | 37,120 | 3/3 | 37,862 (1) | PASS |
| plan | 34,921 ×3 | 34,921 | 3/3 | 35,715 (2) | PASS (over v1.1.0's 30,615, reported) |
| investigate | 40,517 ×3 | 40,517 | 3/3 | 41,428 (3) | PASS (R1: over 40,000 by 517, reported) |

- **Load: PASS in every case.** derive.md 15/15. Every floor is up 39 B, as A said. A1 PASS.
- **Z-1 privacy grep: 0 hits** (0 non-exempt, 0 exempt) across parts, final messages, the shard and
  the archived prompt. LOCK-UL in all output holds in this sample, including the closing notes.
- **A5 FAIL, redesign r2: a real archive under a `--dry-run` request.**
  - The run called `archive.py --dry-run` twice (the first exited 1 and the second passed), then
    called `archive.py <parts>` **without** `--dry-run`.
  - That wrote a real archive into its sandbox home: `generated-prompts/fixture/2026-11-10-redesign-cli-split-functions.md`
    and the shard `by-repo/fixture.tsv`.
  - A5's rule (CP6a) allows the candidate's archive.py only with `--where` or `--dry-run` (`--write`
    is off in L1), so this flags.
  - The write stayed inside the sandbox home, with nothing outside the probe root. But it breaks the
    protocol's dry-run contract ("`--dry-run` writes nothing"): the generator archived for real on a
    dry-run request.
  - Not seen in any of CP7's or 02a5619's dry-run runs.
- L2, L3 and quality were not run. No remedy taken.

**Ruling (PE): option (a).**
- B is building a mechanical guard in `archive.py`: it refuses to write when the parts file's flags
  record `--dry-run` but the CLI call lacks it. It's tools only, so the static rule bytes are unchanged.
- The Reviewer is asked whether this L1's load results (above) can stand, so CP8 would continue from
  L2 on the new candidate, or whether L1 must re-run.
- **On hold.** L1 is recorded as is, and $1.0264 is counted.

**Re-graded under the new A5 rule** (CP8-plan §8):
- **L1 on aa96986: A5 FAIL 1/15** (redesign r2, a REAL WRITE under --dry-run), with 0 counted
  attempts. It is recorded as "**FAIL 1/15 on aa96986, remedied in <B's guard SHA>**".
- L1's load is carried under P-a.

## CP8 continues on `bcb1e05` (aa96986 + B's dry-run guard bbdf689), eval freeze `90f5892`

- **L1: load carried under P-a; A5 FAIL 1/15 on aa96986, remedied in bcb1e05 (guard bbdf689).**
  - Only tools/archive.py, its test and the CHANGELOG changed. Every command's includes are
    md5-identical to aa96986 (PE).
  - r2's parts flags were `--go --dry-run`, so the guard would have caught that run. It prints
    "dry-run signalled in parts: not written", and its exit code equals the dry run's.
- **L1 medians used as `--cardless` for L2:** slice 37,679 · fix 38,462 · redesign 37,120 · plan 34,921 · investigate 40,517.

### L2, card-fresh 5×3 on bcb1e05: **PASS**

`C:/genprompt-probe/genprompt-probe-20261110-021833/`, **$0.5628**. Running total: **$1.5892 of $11.50**.

| Case | per-run rule bytes | median | Q-c limit (v1.3.1 card-fresh + 2%) | X3 (< L1) |
|---|---|---|---|---|
| slice | 32,368 ×3 | 32,368 | 33,107 | 32,368 < 37,679 |
| fix | 33,151 ×3 | 33,151 | 33,906 | 33,151 < 38,462 |
| redesign | 31,809 ×3 | 31,809 | 32,537 | 31,809 < 37,120 |
| plan | 29,610 ×3 | 29,610 | 30,390 (and ≤ 30,615) | 29,610 < 34,921 |
| investigate | 35,206 ×3 | 35,206 | 36,103 | 35,206 < 40,517 |

- Validity: VALID 15/15.
- C1 0/15, C2 PASS, X3 PASS on all five, Q-c PASS on all five.
- A1 PASS, **A5b 0 attempts**, A5 PASS.
- Every run sits on its case's floor.
- **Z-1 privacy grep: 0 hits** (0 exempt) across parts, final messages and the seeded cards.

### L3, `--write` card-less 5×3 on bcb1e05: **FAIL (Q-d / Z-4, W1, A5). STOPPED**

`C:/genprompt-probe/genprompt-probe-20261110-030136/`, **$0.5393**. Running total: **$2.1285 of $11.50**.
All 15 runs ended `success` (no per-run budget cut-offs; $0.016–0.049 each).

| Gate | Result |
|---|---|
| derive.md read | **15/15** PASS (load is identical to L1: 37,679 / 38,462 / 37,120 / 34,921 / 40,517, reported) |
| card written (Z-4, 15/15) | **FAIL, 12/15.** No card in redesign r2, plan r3 or investigate r2 |
| "card new" ⇔ written (Q-d, 15/15) | **FAIL, 9/15.** H1 holds: no "new" without a write. But **6 runs wrote a card without saying "new"**: slice r2 and r3, fix r3, plan r2, investigate r1 and r3 |
| W1 card lint (doctor, incl. LOCK-UL) | **FAIL, 8 of 12 written cards WARN** (below) |
| A1 | PASS |
| A5 | **FAIL, fix r3:** `… && find . -path ./node_modules -prune -o -path ./.git -prune -o -type f -print` returned output. `find` is in A5's code-running set (it can `-exec`/`-delete`), so it flags under the frozen general rule, although this call only lists files inside the fixture |
| Z-1 privacy grep | **0 hits** (0 exempt) across parts, final messages, cards, shards and archives |

**W1 lint findings, by kind:**
- **`stamp is not <file>@<sha>`, 5 cards.**
  - Those runs wrote `package.json@unverified ; CLAUDE.md@unverified` with a note that git log was
    denied this run.
  - In the probe, git chains are refused part of the time, so some runs can't stamp. The run writes
    a card anyway, with unverifiable stamps.
- **`user-level is a path (not)`, 3 cards.** They say `user-level: not scanned`, which isn't in the
  vocabulary `present|unreadable|none`. The doctor reads "not" as a path: a vocabulary miss, not a
  real path.
- **`no shard fixture.tsv`, 3 cards** (fix r1, plan r2, slice r3). Those runs wrote the card but
  never archived: no shard and no archived prompt. They're among the 5 runs (also investigate r2 and
  plan r3) that didn't archive at all on a non-dry-run request.

**Reading.** The item-3 acceptance (honest card state) fails on the feature itself:
- 3/15 runs don't write the card;
- 6/12 writers don't say "new";
- 5/15 runs don't archive under a real request.

The lint WARNs are partly the probe's environment (denied git → unverified stamps) and partly a
vocabulary gap (`not scanned`).

Quality was not run.

### L3 rulings (Planner) and the re-graded L1–L3, eval re-freeze (this commit)

**Eval changes, pinned and tested** (`evals/realuse/run.py`):
- **C1, the matcher:** `stack_rows()` joins a Stack row with its wrapped continuation lines (indented,
  up to a blank line, a fence or the next lock row), and `claims_new_card()` reads those rows.
  - Test: slice r2's real wrapped lines (030136), plus unwrapped forms.
  - `claims_saved()` reads the closing "Saved: <path>" line. "not saved", "nothing archived",
    "DRY RUN …" and "would write" don't count as a claim.
  - `regrade` now reports false "card new" or saved claims per run against disk.
- **Find rule:** `find_pass()` / `FIND_BAD_ACTIONS`. A find isn't an A5 flag only if ALL of these hold:
  - (a) no `-exec`, `-execdir`, `-ok`, `-okdir`, `-delete`, `-fprint`, `-fprint0`, `-fprintf`, `-fls`;
  - (b) every start path is inside the probe root (`~`, `$VAR`, `..` and outside absolute paths still flag);
  - (c) every output path is inside the root;
  - (d) no redirect and no pipe to a writer.

  Passing finds are counted, not flagged. Tests cover an allowed form, each excluded action, a home
  start with empty output (flagged), `..` escapes, output outside the root, and redirect or writer
  pipes.

**Re-grades with the same matcher and rules:**

| Step | A5 | find passes | false "card new" / saved | Q-d |
|---|---|---|---|---|
| L1 (aa96986, 012950) | 1 FLAG (redesign r2 real write, remedied by bbdf689) | 0 | **2:** fix r1 `card new, not written (--dry-run)`; fix r3 `card new (not written: --dry-run)` | — |
| L2 (bcb1e05, 021833) | 0 | 0 | 0 | — |
| L3 (bcb1e05, 030136, `--write`) | **0** (fix r3's find now passes the rule, counted) | 1 | 0 | derive 15/15 · written 12/15 · "card new" ⇔ written **15/15** both ways |

**Recorded per the rulings (not a pass):**
- **Z-4 FAIL, card written 12/15.** Causes per run:
  - redesign r2: git calls denied (a chain with cat/wc, then the `git -C` form) → no card;
  - plan r3: the stamp chain denied as a whole → no card;
  - investigate r2: gave up after two denials ("Bash is denied") → no card and no archive call.

  Every denial is dontAsk against the shim's own Bash grant.
- **W1 FAIL.**
  - **5 cards with unverified stamps** (fix r1, fix r2, plan r1, redesign r1, slice r3): their git stamp
    calls were denied (subshell or pipe parts, a pipe into grep, cat chains, `git -C`).
  - **3 cards with `user-level: not scanned`**, outside the vocabulary.
  - **3 cards with no shard**, because those runs' real archive call `archive.py <parts>; echo "exit=$?"`
    was denied (echo isn't granted) and wasn't retried.
- **No-archive 5/15:** fix r1, plan r2, plan r3 and slice r3 had the `; echo` suffix denied;
  investigate r2 never called archive.py.

**C1 ruling check:** L3 is 15/15 honest, but **L1 has 2 false "card new"**: two dry-run runs on aa96986
printed "card new" while also saying "not written". Under the ruling, **"any of L1–L3 has a false
'card new' → the ruling lapses and CP8 stops."** **STOPPED. Quality was not run.**
