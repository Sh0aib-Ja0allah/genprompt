# 5.N: Design / spike / ADR · `/genprompt:design`

| | |
|---|---|
| **Use when** | A decision must be designed before it is built: an architecture decision (ADR), an API contract, a DB schema/ERD, a design-system or Figma-to-code mapping, or a throwaway spike to de-risk an unknown |
| **Not when** | A multi-workstream plan → `:plan`. The design is settled and needs building → `:slice` |
| **Autonomy** | N/A: design docs only. A spike runs in a named scratch path and is never merged |
| **Baseline delta** | Unchanged. Production code is untouched; a spike's own numbers go in the doc |
| **Length tier** | Program (350) |
| **Deliverable** | One design doc (ADR / contract / schema / mapping), named per §2.7, with the options considered, the recommendation and the consequences |

## Generator: before emitting

- **Name the decision precisely,** and the constraints that bind it (the contract, the stack, the
  client docs, the existing schema). Read the parts of the code the decision touches.
- **Set the output format for the decision type:**
  - **ADR:** Context · Options (at least 2, with trade-offs) · Decision · Consequences ·
    Reversibility
  - **API contract:** endpoints/methods, request/response shapes, status codes, errors, auth,
    versioning, and example payloads
  - **Schema/ERD:** entities, fields and types, keys, indexes, relations, migrations order, data
    backfill, and a mermaid ERD
  - **Design-system mapping:** tokens → code, components → files, gaps, `[NOT DESIGNED]` markers
    for anything missing
  - **Spike:** a question, a time box, a scratch path, the result, and a keep/discard verdict
- **Anything that needs the user's taste or authority** goes in a `[DECIDE]` list, not into a
  silent choice.

## Required blocks

- §4.5, §4.6, §4.7
- §4.20 THE CENTRAL PROBLEM TO SOLVE
- §4.10 (constraints already decided)
- §4.20 explicit tool allow-list

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]
Task: design <decision>. You write ONE doc: `<PROFILE.docnaming: design doc>`.
<Spike only: "You may create throwaway code ONLY under `<scratch path>`. It is never imported by
production code and never committed unless I say so.">
No production code changes. No dependency changes. <git posture: commit only the doc | no commits>.
The contract's mandated tools (<e.g. logging>) are allowed.

[INSERT §4.20 THE CENTRAL PROBLEM TO SOLVE: <the decision, and why it matters now>]
[INSERT §4.10 CONSTRAINTS ALREADY DECIDED: <stack/contract/client rulings that bound the options>]
[INSERT §4.6 source of truth] [INSERT §4.7 skepticism]

STEP 1: read the code the decision touches (<paths>) and state today's behaviour with path:line.
STEP 2: generate at least 2 real options. For each: how it works here, cost, risk, reversibility,
        and what it does to <the central problem>.
STEP 3: recommend one. State the consequences, including what becomes harder.
STEP 4: write the doc in the <ADR | API contract | schema/ERD | mapping | spike> format:
        <the format sections from above>
STEP 5: list the [DECIDE] items, each with your recommendation.

REPORT: the doc path, the recommendation in one line, the [DECIDE] list. Confirm that no
production file changed (`git status`).
Start with STEP 1 now.
```
