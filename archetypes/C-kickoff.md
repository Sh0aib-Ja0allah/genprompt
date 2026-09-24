# 5.C: Kickoff with dirty WIP · `/genprompt:kickoff`

| | |
|---|---|
| **Use when** | Starting a unit whose partial, uncommitted WIP is already in the tree, and whose state is unclear |
| **Not when** | The WIP is clearly a slice or a fix → `:slice` / `:fix`, with a WIP-disposition paragraph. That is usually the better fit |
| **Autonomy** | Phases 1–2 are read-only, plus one gap-audit doc. The §4.19 approval gate comes before any code |
| **Baseline delta** | N/A until implementation starts |
| **Length tier** | Focused (200) |
| **Deliverable** | A gap-audit doc with a WIP disposition per file, and a slice plan in chat |

## Generator: before emitting

- **Inspect the real working tree** (`git status --porcelain -uall`, `git diff --stat`) and put the
  real file counts in the prompt. A kickoff written against an imagined tree is worse than none.
- **Classify every change** as committed prior work / uncommitted WIP for this unit / missing work /
  unrelated tooling noise. Nothing is cleaned up, reverted or discarded unless the user asks.

## Required blocks

- §4.5, §4.6, §4.7, §4.19, §4.14 (for the later phases)

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch>)
Task: start <unit> using the usual flow: audit → concrete plan → slice by slice → verify → docs.

Current state (read by me: <N> modified, <M> untracked; <git diff --stat summary>):
- Prior work is committed. <unit> is partially in progress in the working tree.
- Do NOT assume the WIP is correct, complete or aligned with the source docs.

[INSERT §4.5 contract precedence] [INSERT §4.6 source of truth] [INSERT §4.7 skepticism]

WORKING-TREE RULES
- Classify every change as: (1) committed prior work, (2) uncommitted WIP for this unit,
  (3) missing work, (4) unrelated local/editor/tooling files.
- Do not clean up, revert or discard existing work unless I explicitly ask.

Phase 1: restate the exact scope from the docs (requirements, entities/routes/screens, dependencies
         and whether they exist, explicit deferrals).
Phase 2: audit the codebase AND the working tree. Write `<PROFILE.docnaming: gap audit>`, including
         a WIP disposition per file (keep / revise / partially discard), each with a reason.
Phase 3: present the concrete slice plan in chat.
[INSERT §4.19 approval gate]
Phase 4: implement slice by slice, with checkpoints.  Phase 5: update the docs and the report.

[INSERT §4.14 verification + report, for Phase 4]

Start now with Phase 1 and Phase 2 only. Do not edit code yet. Do not commit anything.
```
