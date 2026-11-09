# CP8 (1.4.0, candidate `02a5619`, eval freeze `7af76de`): **STOPPED at the L1 privacy grep (Q-e)**

| | |
|---|---|
| Spend | **$0.5083 of $11.50** |
| Status | L1 load PASSES every gate. The Z-1 privacy grep after L1 found **1 real-home hit** (redesign r1, final message). Q-e: any hit stops. L2, L3 and quality were not run |

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
