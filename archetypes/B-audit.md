# 5.B: Audit / read-only assessment · `/genprompt:audit`

| | |
|---|---|
| **Use when** | Assess state against the docs, and write ONE doc with a ranked backlog. No code |
| **Not when** | A diff or branch to review → `:review`. Security-specific → `:security`. An unfamiliar repo with no contract → `:onboard` |
| **Autonomy** | N/A: read-only. Writes are enumerated (exactly one doc) |
| **Baseline delta** | N/A (no gates run) |
| **Length tier** | Focused (200) |
| **Deliverable** | One markdown doc, named per §2.7, ending in a ranked backlog and one recommended next slice |

## Generator: before emitting

- **Enforce read-only by enumeration, not by adjective:** the §4.20 explicit tool allow-list.
- **Invert §2.5:** the worker must NOT run builds, tests or installs. List the gates only as facts
  the doc records.
- **Build a reading manifest with depth** (READ FULLY / SKIM / CONTEXT ONLY) from the real `docs/`.
- If execution is also wanted, that is a separate `:roadmap` prompt, and it hard-STOPs if this doc
  is missing. Do not fold audit and execution into one prompt.

## Required blocks

- §4.5, §4.6, §4.7, §4.25
- §4.20 explicit tool allow-list
- §4.20 reading manifest with depth

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)

You are a <PROFILE.role> and a product-minded tech lead doing a READ-ONLY assessment. You will NOT
write application code, NOT run builds/tests/installs, NOT commit and NOT create a branch. You may
ONLY read files (Read/Glob/Grep), inspect git history (read-only git), and at the very end WRITE ONE
markdown file: `<PROFILE.docnaming: assessment doc path>`. The contract's mandated tools (<e.g. its
logging step>) are also allowed. Nothing else gets written.

Read <PROFILE.contract> FIRST. Your recommendations must respect it. When the code violates it,
call that out.

READ, grouped by depth:
  READ FULLY:  <the plan/roadmap docs>
  SKIM:        <specs, for intent and scope>
  CONTEXT:     <archive/history>
As you read, keep a running list of everything the docs say is PLANNED, DEFERRED or UNFINISHED.

[INSERT §4.7 skepticism, with a real falsifying artifact from this repo]

STEP 1: <scope> inventory against the docs.
STEP 2: source-control forensics: `git log --oneline --graph --decorate -50`, `git shortlog -sn -20`.
        Known state to confirm, not assume: <…>.
STEP 3: classify every requirement as done / partial / missing / incorrect / placeholder-only /
        out-of-scope-present / blocked. Cite `path:line` for every claim. Invent no findings. Flag
        anything material you could not determine read-only.
STEP 4: write the doc, with this TOC:
        1. executive summary  2. current state by area  3. traceability matrix
        4. findings (§4.25 register)  5. blockers (what each blocks, what would unblock it)
        6. RANKED BACKLOG: {id, item, area, why it matters, effort S/M/L, source doc, dependencies}
        7. the recommended next slice (ONE pick). Describe it; do NOT build it.

Do not create commits. Be critical; a comfortable audit is a useless one.
Start with STEP 1 now.
```
