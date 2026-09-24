# 5.K: Resume after compaction · `/genprompt:resume`

| | |
|---|---|
| **Use when** | The worker lost context mid-slice (compaction, crash, a new chat) and must re-anchor |
| **Not when** | The worker finished and reported → `:next` |
| **Autonomy** | That of the slice being resumed. Restate it |
| **Baseline delta** | That of the slice being resumed. Restate the numbers |
| **Length tier** | Focused (200) |
| **Deliverable** | A state reconstruction (done / in progress / not started / inconsistent), then the remaining scope |

## Generator: before emitting

- **Ground the actual mid-flight state yourself:** `git status --porcelain -uall`,
  `git log --oneline -10`, `git diff --stat`. Put the real numbers in the prompt, so the worker's
  reconstruction can be checked.
- **Name the authoritative resume-state doc first** (the one that records done / remaining /
  decisions per slice), then the work list, then the audit/traceability docs.
- **Restate the LOCKED DECISIONS still in force, each with its reason:** stack choices, boundaries,
  rulings. These are exactly what compaction loses, and a re-decision forks the codebase.
- **Restate the gates.** The worker may not remember those either.

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch>)

Continue <unit>. You are RESUMING AFTER A CONTEXT COMPACTION, mid-<slice>.
State as I read it: <N> files modified, <M> untracked; last commit <sha> "<subject>"; <diff --stat summary>.

STEP 0: re-anchor before writing any code. Do NOT trust the compacted summary alone.
Re-read, in order, and reconstruct exactly where you stopped:
1. `<the authoritative resume-state doc>`   <- done / remaining / decisions per slice
2. `<the work list>`                         <- deliverables and definition of done
3. `<the audit / traceability doc>`
Then state, before doing anything else: what is DONE, what is IN PROGRESS and how far, what is NOT
STARTED, and any file you find in an inconsistent state. Reconcile that against the state above.

LOCKED DECISIONS still in force (they must survive compaction):
- <decision>: <the reason it was made>
- <decision>: <the reason it was made>

[INSERT §4.8 MODE or §4.19 gate, as the resumed slice had it]
[INSERT §4.14 verification: literal gates, baseline <numbers>, expected delta]
<Then the remaining scope, as a normal §5.D slice.>
Do not re-decide anything in the locked list. If you believe one is wrong, say so and stop.
Start with STEP 0 now.
```
