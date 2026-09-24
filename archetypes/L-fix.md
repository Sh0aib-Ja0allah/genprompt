# 5.L: Defect-driven fix slice · `/genprompt:fix`

| | |
|---|---|
| **Use when** | Drive a list of **confirmed** defects to closure, each with a repro and acceptance |
| **Not when** | A production incident under time pressure → `:hotfix`. Unconfirmed suspicions → `:review` or `:audit` first |
| **Autonomy** | Code-writing: §4.8 MODE or §4.19 gate |
| **Baseline delta** | Up: at least one new failing-then-passing test per defect |
| **Length tier** | Focused (200). If the defect list is long, split it |
| **Deliverable** | Each defect fixed and proven load-bearing, plus retired false positives with evidence |

## Generator: before emitting

- **Re-verify each reported defect against the code** before it goes in the prompt. Some will
  already be fixed, some misreported. Give each one MECHANISM (`file:line`), CONSEQUENCE, REPRO,
  FIX, ACCEPTANCE and TRAPS.
- **Carry a `FALSE POSITIVES / DO NOT FIX` section**, with the evidence for each. Without it, the
  worker "fixes" a non-defect and calls it done.
- **Order the defects deliberately, and say why** when order matters. A gate must land before the
  permission it protects.
- **State severity per defect.** Flag where you are reporting the worker's severity rather than
  your own.
- **Anything that needs a product decision** goes in §4.20 `RECORD, DO NOT ACT`, not into a
  widened grant.

## Required blocks

- §4.5, §4.7, §4.14
- §4.15 (this is the archetype it exists for)
- §4.20 RECORD, DO NOT ACT, when needed
- §4.8 **or** §4.19

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]

<N> confirmed defects. Fix them in the order below. <Sequencing rationale, if order matters.>
[INSERT §4.8 MODE or §4.19 gate]
[INSERT §4.15 falsifiability standard]

═══════════════════════════════════════════════════════════════════════════════
DEFECT 1: <one-line title>   [<severity>]
═══════════════════════════════════════════════════════════════════════════════
MECHANISM: <file:line>: <what the code actually does>
CONSEQUENCE: <the observable lie or failure a real user hits>
REPRO: <the exact call/state that triggers it>
FIX: <what to change, or "your call, but say why" where the design is genuinely open>
ACCEPTANCE: <the assertion that proves it; the assertion that proves the fix is load-bearing; the
            assertion that the legitimate case still succeeds>
TRAPS: <what will break a naive fix>

<repeat per defect>

FALSE POSITIVES / DO NOT FIX: <each re-checked non-defect, with the evidence>. A false positive
retired with evidence is worth as much as a defect fixed.
[INSERT §4.20 RECORD, DO NOT ACT, for decisions]

[INSERT §4.14 gates (literal) + DEFINITION OF DONE + REPORT; baseline <n> → at least <n + defects>]
<git posture: a commit per defect, or leave uncommitted for review>
Start with DEFECT 1 now.
```
