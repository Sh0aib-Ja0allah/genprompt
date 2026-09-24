# 5.U: Hotfix / incident · `/genprompt:hotfix`

| | |
|---|---|
| **Use when** | Something is broken for real users now (a lockout, a crash, data exposure, a failing critical flow) and time matters |
| **Not when** | Known defects with no urgency → `:fix` |
| **Autonomy** | §4.8 MODE for triage and the local fix. §4.23 approval per action for anything that touches a live system (deploy, data repair, config change) |
| **Baseline delta** | Up by at least one regression test that reproduces the incident |
| **Length tier** | Focused (200) |
| **Deliverable** | Mitigation, a minimal root-cause fix with a regression test, and a short postmortem note |

## Generator: before emitting

- **Capture the incident facts:** the symptom, since when, who is affected, error text/logs the
  user has, recent deploys/commits (`git log --since`). Mark each as known or `[UNVERIFIED]`.
- **Separate the steps:**
  1. **mitigate** (stop the bleeding: a flag off, a revert, a config change); approval if live
  2. **root cause**
  3. **minimal fix**
  4. **regression test**
  5. **postmortem**

  Mitigation may come before the root cause.
- **Minimal diff.** No refactors, no opportunistic cleanup. Anything else found goes in the
  postmortem as follow-ups.
- **Revert** is a legitimate mitigation. Name the candidate commit if the timing points at one.

## Required blocks

- §4.5, §4.7, §4.9, §4.14, §4.15
- §4.23 (anything live)
- §4.8
- §4.26-style follow-ups in the postmortem

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch>)
[INSERT §4.5 contract precedence]
INCIDENT: <symptom>, since <when>, affecting <who>. Evidence: <errors/logs/screens>. Suspects: <commits
since <date>: sha subject>, <…>.

[INSERT §4.8 MODE: standing approval for local triage and the local fix only]
[INSERT §4.23 APPROVAL PER ACTION: revert/deploy/data repair/config on <env>]

STEP 1: TRIAGE: reproduce locally (the exact steps/data). If you cannot reproduce it, say so and list
        what you need from me.
STEP 2: MITIGATE: propose the fastest safe mitigation (flag, revert <sha>, config). Prepare it; ask
        before any live action.
STEP 3: ROOT CAUSE: [INSERT §4.9 mechanism → chain → consequence], with path:line.
STEP 4: FIX: minimal diff. [INSERT §4.15: a failing regression test first; prove it load-bearing;
        the legitimate case still works]
STEP 5: POSTMORTEM, in `<PROFILE.docnaming: incident note>`: timeline, root cause, why tests/CI did
        not catch it, the fix, follow-ups (not done now).

[INSERT §4.14: gates <literal>; baseline <n> → at least <n+1>; DON'T refactor or widen scope]
Start with STEP 1 now.
```
