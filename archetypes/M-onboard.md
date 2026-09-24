# 5.M: Onboard / discovery · `/genprompt:onboard`

| | |
|---|---|
| **Use when** | A repo is unfamiliar, has no (or a thin) conventions contract, or is empty. Map it before any other prompt |
| **Not when** | The contract is solid and you want a gap analysis → `:audit` |
| **Autonomy** | N/A: read-only, plus exactly the enumerated docs |
| **Baseline delta** | N/A. The deliverable *records* the gates and baseline counts; the worker may run the non-⚠ gates **once** to record them, but not if the contract forbids it |
| **Length tier** | Focused (200) |
| **Deliverable** | A draft conventions contract (`CLAUDE.md`, or `CLAUDE.draft.md` if one exists), a repo map doc, and the gate list with baseline numbers |

## Generator: before emitting

- **Derive what you can first** (stack, manifests, scripts, CI, docs), so the worker confirms
  rather than rediscovers.
- **If a `CLAUDE.md` exists,** the worker must NOT overwrite it. It writes `CLAUDE.draft.md` and a
  diff summary; the user merges.
- **Empty repo** (no manifest): the deliverable is a bootstrap decision list (stack, structure,
  gates, conventions) for the user to rule on. It feeds `:plan` or `:greenfield`, not code.
- **Whether gates may run** is a question for the lock when the repo has ⚠ gates or a
  database-touching test suite.

## Required blocks

- §4.5 (with "none in-repo" where true), §4.6, §4.7
- §4.20 explicit tool allow-list (enumerated writes)
- §4.13

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch>)
Task: map this repository and draft the conventions contract every later prompt will rely on.
You may read anything. You may WRITE ONLY: <contract path: CLAUDE.md | CLAUDE.draft.md>,
`<PROFILE.docnaming: repo map doc>`, plus the contract's mandated tools (<e.g. logging>), if any.
No code changes, no installs, no commits.
<If allowed: "You may run these gates ONCE to record baselines: <non-⚠ gates>. Never run: <⚠ gates>.">

What I already derived (confirm or correct each; do not re-derive blindly):
- Stack: <PROFILE.stack> · code roots: <PROFILE.code_roots> · branch default: <…>
- Scripts: <manifest script keys> · CI: <workflow files and their steps | none>
- Docs: <docs found, with dates>

STEP 1: architecture map: entry points, routing, data layer, auth, background jobs, integrations,
        tests (where, what kind, count). Cite path:line.
STEP 2: hazards: destructive commands, env/secrets handling, generated/vendored trees, inert
        features, anything that looks dangerous to a newcomer.
STEP 3: the conventions actually in use (naming, structure, patterns), each with an example path.
        Where the code is inconsistent, say which pattern is the majority and which looks correct.
STEP 4: write the contract draft with these sections: What this is · Stack (versions) · Commands
        (literal) · Architecture · Conventions · Hazards / never-do · Source of truth · Git
        workflow (ASK me: mark "[DECIDE]" where you cannot know my preference).
STEP 5: write the repo map doc: the STEP 1–3 findings, the gate list with the baselines you
        recorded, and the open questions for me, ranked.

[INSERT §4.13: what only I can supply: <credentials, branch policy, deploy rules>]
REPORT: the files written, the gate baselines, and the [DECIDE] items. Confirm that no code
changed and nothing was committed.
Start with STEP 1 now.
```

## Traps

- **A worker writing a confident contract** out of one reading bakes guesses in as rules. Every
  rule needs an example path, or a `[DECIDE]` marker.
- **Overwriting an existing `CLAUDE.md`** destroys the owner's rules. Draft beside it.
