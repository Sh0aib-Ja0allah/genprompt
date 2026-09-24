# 5.E: Approval, rulings, amendment · `/genprompt:approve`

| | |
|---|---|
| **Use when** | Lock decisions, rule on the worker's findings, approve a plan, or amend a prompt that is already running |
| **Not when** | A fresh report with no rulings needed → `:next` |
| **Autonomy** | Inherits the running prompt's mode. State only what changes |
| **Baseline delta** | As the ruling implies. State it if code changes follow |
| **Length tier** | Delta (120) |
| **Deliverable** | Numbered rulings the worker applies, then continues |

## Generator: before emitting

- **Quote the worker's own sentence verbatim before ruling on it** (§4.17). A paraphrase resizes
  the claim.
- **Where the worker was right** and the previous instruction was not, say so plainly (§4.16). A
  worker never told "you were right" learns to suppress deviations.
- **A mid-session E inherits the running prompt's constraints.** State only the **deltas**. But if
  code changes follow, **restate the literal gates** (principle 9): never "same as before".
- **Sequencing decisions carry their rationale** (§4.20). Order is load-bearing when one ordering
  ships a disclosure.
- **Amendment mode** (a prompt is already running):
  - set the header's `| Amends | <prior prompt filename>: insert before Part <X> |` (§4.1, the
    archive file, not the block)
  - open the block with an unmissable STOP AND INSERT
  - verify on the branch that the prior prompt actually reached the worker
- **Anything that needs a decision rather than a fix** goes in §4.20 `RECORD, DO NOT ACT`.

## Template

```text
<One-line disposition: "Three corrections accepted, one ruling amended, one decision. Then continue.">

<AMENDMENT ONLY, first and unmissable:
STOP AND INSERT THIS BEFORE PART <X>. <what changed, and why the running plan is now wrong.>>

[INSERT §4.4 Situation: the worker's numbers, labelled verified-by-artifact or reported]

1. <ALL-CAPS VERDICT HEADLINE>
   "<the worker's sentence, verbatim>"
   <rationale> → <the code consequence> → record it in <doc>.

2. [INSERT §4.16 CORRECTIONS TO MY PREVIOUS PROMPT, when the worker was right]

3. <DECISION>: <option chosen>. <one-line rationale>.
   <Sequencing constraint and its rationale, if order matters (§4.20)>

[INSERT §4.15 falsifiability standard, if this rules on a fix]
[INSERT §4.20 RECORD, DO NOT ACT, for anything that needs a decision rather than a fix]
GATES for the work this unlocks: <literal commands>. Expected delta: <…>.

Then continue with <ordering>. <What stays deferred, and why.>
```
