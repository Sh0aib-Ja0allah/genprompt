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
