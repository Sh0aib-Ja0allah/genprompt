# 5.F: Planning-only · `/genprompt:plan`

| | |
|---|---|
| **Use when** | Produce a plan or roadmap doc, with no code |
| **Not when** | The design of one decision (ADR, schema, API contract) → `:design`. Executing an existing plan → `:roadmap` |
| **Autonomy** | N/A: read-only until the plan doc is written. If an execution phase is included, it sits behind a §4.19 gate |
| **Baseline delta** | N/A. State the gates for later slices without running them |
| **Length tier** | Program (350) |
| **Deliverable** | Exactly one plan doc (§2.7 naming) with stable item ids, then the ordered slice plan in chat |

## Generator: before emitting

- **Forbid code changes and commits** during planning. If the prompt also carries execution, make
  the boundary a phase gate with write access, not a blanket ban.
- **Write the `WHAT THIS REPO IS` inventory block** from real counts, so the worker does not burn a
  phase re-deriving it.
- **Cross-repo plans:**
  - anchor both repos, each with its own branch, gates and commit permissions
  - carry the paired-change rule (§1)

## Required blocks

- §4.5, §4.6, §4.7
- §4.20 THE CENTRAL PROBLEM TO SOLVE
- §4.20 deliverable TOC with an ID scheme

## Template

```text
Repo(s): <PROFILE.path> (branch <…>)  [+ the secondary repo, its branch and its own permissions]

Prepare <unit>: planning only. Do not implement code.
You have full read access. <If write access exists: "You still edit nothing before the approval gate
in Phase 4. Phases 1–3 are audit and planning only.">

WHAT THIS REPO IS: <inventory from real counts: N controllers, N models, N routes, N screens, N tests>

READ, in authority order:
[INSERT §4.6, with annotations and at least one explicit exclusion]
[INSERT §4.7 skepticism]
[INSERT §4.20 THE CENTRAL PROBLEM TO SOLVE]

Phase 1: audit by dimension (<a: API surface / b: UX / c: performance / d: architecture>).
Phase 2: <the second repo or second axis, same shape>.
Phase 3: author ONE doc, `<PROFILE.docnaming: plan doc>`, with this TOC:
  1. Executive summary and recommended scope
  2. <Contract/traceability matrix: one row per endpoint or requirement. The centrepiece.>
  3. Workstreams with EXACTLY these ids: WS-A … WS-<n>
  4. Every item: a stable id (`A-03`), priority P0/P1/P2, a one-line problem, the exact files or
     routes, acceptance criteria, dependencies. No item may say "improve X" without naming files.
  5. Explicit deferrals, with reasons
  6. Slice-by-slice implementation order
  7. `## Decisions log`, seeded with the decisions you made during the audit
  8. Only the open questions that truly need my decision

Verification profile for later slices (state it, don't run it): <PROFILE.gates>
Constraints: no code changes, no commits, <out-of-scope areas>.
Then present the ordered slice plan in chat, and stop.
START NOW with Phase 1 only. Do not edit any code.
```
