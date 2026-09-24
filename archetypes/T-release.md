# 5.T: Release and deploy · `/genprompt:release`

| | |
|---|---|
| **Use when** | Cut a release (version, changelog, tag), prepare or execute a deploy (staging/production, app-store build), write a deploy runbook, or run a handover of credentials and environments |
| **Not when** | Just committing work → `:commit`. Writing handover docs only → `:docs` |
| **Autonomy** | **§4.23 approval per action for every outward-facing or irreversible step, without exception.** Everything up to the action may run under §4.8 |
| **Baseline delta** | Unchanged. The release candidate is exactly what was verified |
| **Length tier** | Program (350) |
| **Deliverable** | A release checklist doc/runbook, the prepared artifacts, and per-action logs of what was executed after approval |

## Generator: before emitting

- **The repo's deploy rules are absolute.** Quote them in one line and follow them. For example, a
  contract saying "never deploy without an explicit order" means **every** step in §4.23, with no
  standing approval, even if the user asked for "the deploy".
- **Inventory from the repo:** the version source (manifest, tags, app config), the changelog
  convention, the environments and their config (`.env.example` keys, not values), the deploy
  mechanism (CI job, script, Envoy/Forge, EAS, Docker), migrations pending, and smoke tests.
- **Secrets and credentials** are never put in the prompt, the repo or the chat. The prompt names
  *which* keys are needed and where they are set (an action for the user).
- **Rollback is written before deploy.** No rollback path means no deploy.

## Required blocks

- §4.5, §4.6, §4.14
- §4.22 (the environment state at start)
- §4.23 (mandatory)
- §4.13 (credentials, DNS, stores)
- §4.20 structure table

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch>)
[INSERT §4.5 contract precedence. Quote the deploy rule: "<contract rule>"]
Task: <release vX.Y.Z | deploy <commit> to <environment> | prepare the deploy runbook | handover>.

[INSERT §4.22 VERIFY BEFORE STARTING: branch/sha, tree clean, CI status, pending migrations, env keys present]

PART A: PREPARE (no outward action):
  A1 run the gates on the exact candidate: <literal>; must equal <last green numbers>.
  A2 version bump per <convention> in <files>; changelog entry per <convention>.
  A3 environment checklist: every key from <.env.example / config> needed in <env>. Name each key;
     never print a value. Mark each one present / missing for me to set.
  A4 migrations pending: <list>. The dry-run output, if the stack supports it.
  A5 ROLLBACK PLAN written in `<PROFILE.docnaming: runbook>`: how to go back, and the data implications.
  A6 smoke plan: the exact URLs/flows/commands that prove the release works.

[INSERT §4.23 APPROVAL PER ACTION: each of the following needs my "yes" at the moment you run it:
 - tag + push the tag   - push to the deploy branch / trigger the pipeline   - run migrations on <env>
 - cache/config/queue commands on <env>   - store submission   - DNS/SSL changes   - admin user creation]

PART B: EXECUTE: one approved action at a time, then its verification, then the next approval request.
PART C: SMOKE + REPORT: run the smoke plan and report the results; state the rollback trigger if it fails.

[INSERT §4.13 WHAT YOU CANNOT DO: credentials, DNS, store accounts: list what I must do]
REPORT: each action with its approval, its command, its output summary and its verification. Final state.
Start with Part A now. Do not take any action from the approval list until I say yes to that action.
```
