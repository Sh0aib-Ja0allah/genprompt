# 5.H: Commit & push (and `--verify`, `--pr`) · `/genprompt:commit`

| | |
|---|---|
| **Use when** | Commit a completed, scoped body of work. With `--verify` (older spelling `verify+`), run a read-only verification pass first. With `--pr` (or a bare `pr`), commit on a branch, push it and open a pull request |
| **Not when** | The work is not finished → `:slice`. A release with tags and deploys → `:release` |
| **Autonomy** | N/A: commit-only. Writes are enumerated (the commits in the manifest) |
| **Baseline delta** | Unchanged: the worker re-runs the gates, and the numbers must match the last reported green |
| **Length tier** | Focused (200) |
| **Deliverable** | The commits (and the push, if authorised), with SHAs reported; with `--pr`, the PR URL |

## Generator: before emitting

- Ground the commit on real git state:
  - the current branch and the `origin` SHA
  - what is dirty (`git status --porcelain -uall`)
  - the recent commit subjects, so the message matches the repo's style
- Take the branch and push policy from the contract. If the instruction overrides it (for
  example, "commit directly to main" or "push is authorised for this task only"), say so explicitly
  in the prompt.
- Offer `--verify` when the work has not been independently checked.
- `--pr`: take the branch name and PR rules from the contract (else `<type>/<short-topic>` from
  the recent branch names), the base from the default branch, and the body from the repo's own
  `.github/pull_request_template.md` when it exists, else the PR BODY below. Each of create
  branch, push and open PR is its own §4.23 action: the worker asks before each one, because a
  push and a PR are outward-facing. You never push or open the PR yourself.
- The PR body holds only placeholders the worker fills from this repo (its diff, commits, gate
  output, the ticket id from the branch or contract): no client names, customer data, secrets
  or environment values, because a PR page is read more widely than the repo.
- Name the probe/scratch files that must NOT be swept in. `.env` is excluded; **`.env.example`
  is in scope**.

## Required blocks

- §4.5
- §4.20 commit-staging manifest
- §4.14 (gates + report)
- §4.23, with `--pr` (branch, push, PR: one approval each)

## Template

```text
<--verify only: "FIRST a READ-ONLY verification pass, THEN commit. Commit nothing until the
pass is clean and you have reported it.">

Repo: <PROFILE.path> · branch <PROFILE.branch> · <push to origin | do not push>
<Branch policy, from the contract: "<quoted rule>". <Deviation, if any, and that it is authorised for
this task only.>>

Scope: <what to include>. Exclude: <what not to include>.

BEFORE COMMITTING
1. `git fetch`, then `git pull --ff-only origin <branch>`. Always sync first.
2. Inspect `git status --porcelain -uall` and the full diff of staged and unstaged changes.
3. <Monorepo:> `git status --porcelain -uall -- . ":(exclude)<in-scope path>"` MUST print nothing.
   If it does, stop and tell me what else is dirty.
4. Read the recent commit messages, so the new ones match the repo's style.
5. Run the gates and report the actual numbers: <literal PROFILE.gates>. Never commit red.
   Expected: unchanged from <last green numbers>.
6. Tell me briefly which files you will include and exclude.

THEN
- Stage by EXPLICIT PATH. Do NOT use `git add -A` or `git add .`.
- Commit manifest:
  Commit 1: paths <…> · subject "<…>" · body must record <…, especially any breaking contract change>
  <Commit 2: …>
- Attribution: use your harness's standard trailer; do not invent one.
- <Push, or stop before pushing.>

CONSTRAINTS
- Do not change git config. No force push. Do not amend any prior commit.
- Do not commit secrets or local-only files. `.env` is excluded; `.env.example` IS in scope.
- Do not commit probe/scratch files: <named>.
- Leave unrelated dirty files untouched.
- If a pre-commit hook fails and it is clearly related to these changes, fix it and make a NEW commit.

<--pr only:
PULL REQUEST, after the commits. [INSERT §4.23 APPROVAL PER ACTION: (1) create branch
 <branch> from <base sha> (skip if already on it), (2) `git push -u origin <branch>`, (3) open the
 PR into <default branch> with `gh pr create --base <default> --head <branch> --title "<…>"
 --body-file {body file}`; no gh → show me the compare URL and stop]
PR BODY (<the repo's PR template, or this>), filled only from this repo:
  ## Summary: {what changed and why, 2–4 lines}
  ## Changes: {one line per commit: subject, short SHA}
  ## Verification: {each gate command with its actual numbers}
  ## Risk and rollback: {what could break; how to revert}
  ## Links: {ticket id from the branch or contract, or "none"}
  No client names, customer data, secrets, hostnames or environment values.
Do not merge the PR, request reviewers or change its settings unless I say so.>

After pushing: show the final commit message(s), the branch, the SHA(s), the push/remote status
and, with --pr, the PR URL.
Begin with step 1.
```
