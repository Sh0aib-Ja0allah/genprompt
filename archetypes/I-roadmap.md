# 5.I: Roadmap / backlog execution · `/genprompt:roadmap`

| | |
|---|---|
| **Use when** | Drive a whole backlog or roadmap doc to done, in parts and slices |
| **Not when** | One slice → `:slice`. No backlog doc exists yet → `:audit` or `:plan` first |
| **Autonomy** | Usually §4.8 MODE, **plus** an exit valve (§4.13 or §4.20 STOP/DEFER). `--attended` gives a gate per part |
| **Baseline delta** | Up overall. Stated per part |
| **Length tier** | Program (350) |
| **Deliverable** | Every item id with its final state, plus a report of what the user must supply, ranked |

## Generator: before emitting

- **Find the backlog doc from the source-of-truth order** (§2.6: roadmap docs, task sheets).
  Don't assume a filename.
- **If the backlog depends on a prior artifact** (an audit doc), open with a §4.20 STEP 0 check
  that hard-STOPs.
- **Do not assume the backlog's own claims are still true.** Each item is verified against current
  code; if it is already resolved, it is marked done and skipped.

## Required blocks

- §4.5, §4.6, §4.7, §4.14 (hoisted, with environment facts)
- §4.8 plus an exit valve
- §4.20: structure table, tree-integrity guard, STANDING RULES
- §4.13 or §4.20 STOP/DEFER

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]
<[INSERT §4.20 STEP 0 dependency check], if a prior artifact is required>

Read `<backlog doc>` and implement it fully, every item across its workstreams, in priority order,
as reviewable vertical slices, until it is done or genuinely blocked on something only I can provide.

[INSERT §4.8 MODE FOR THIS SESSION]
[INSERT §4.14 VERIFICATION, hoisted here with environment facts] [INSERT §4.20 tree-integrity guard]
[INSERT §4.6 source of truth]
[INSERT §4.7 skepticism: "do NOT assume the backlog's audit claims are still true; verify each against
 current code; if one is already resolved, mark it done and move on"]

[INSERT §4.20 Structure and its reasoning: Part | Content | Why here]

═══════════════════════════════════════════════════════════════════════════════
PART A: <goal, stated as an end state>   (reserve one part for VERIFYING WHAT ALREADY EXISTS)
═══════════════════════════════════════════════════════════════════════════════
A1 … An, each with defect / decisions / build / traps / gate / commit.

<PART B … the same way. Reserve one part for RECONCILING THE BACKLOG DOC ITSELF where it is wrong.>

[INSERT §4.13 WHAT YOU CANNOT DO] [INSERT §4.20 STOP/DEFER with revert]
[INSERT §4.20 STANDING RULES]
[INSERT §4.14 DO/DON'T + DEFINITION OF DONE + REPORT]

FINAL DELIVERABLE: `<PROFILE.docnaming: report>`: every item id with its final state, what was fixed
where, every deviation and why, everything I must supply RANKED BY HOW MUCH EACH UNBLOCKS, and the
final verification output.

Start with Part A now.
```
