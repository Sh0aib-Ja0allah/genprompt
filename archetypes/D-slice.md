# 5.D: Slice execution · `/genprompt:slice`

| | |
|---|---|
| **Use when** | Drive one vertical slice (a feature or change set) through checkpoints |
| **Not when** | The scope is a list of confirmed defects → `:fix`. A whole backlog → `:roadmap` |
| **Autonomy** | Code-writing: §4.8 MODE (unattended) **or** §4.19 gate (attended), never neither |
| **Baseline delta** | Up (new behaviour needs new tests); state the expected numbers |
| **Length tier** | Slice (260; 320 with several checkpoints) |
| **Deliverable** | The slice, green at every checkpoint, with a report |

## Generator: before emitting

- **Scope items are mechanisms, not bullets:** a §4.9 defect with `file:line`, the causal chain
  and the consequence. Ground each one.
- **If this follows a prior slice,** put the relationship in the header, and confirm the prior
  instruction landed on the branch.

## Required blocks

- §4.5, §4.6, §4.7, §4.9, §4.10 (including the negative decisions), §4.11, §4.14
- §4.12 wherever the majority pattern is the trap
- §4.13 if anything is blocked
- §4.8 **or** §4.19

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]

<Prior-slice disposition, if any: "<prior> approved and closed. Carried forward: FIRST …, SECOND …">
NOW: <slice id>, which <what it closes>.

[INSERT §4.8 MODE, or §4.19 approval gate: one of them, never neither]
[INSERT §4.22 verify-at-start, if the prompt builds on volatile facts]

═══════════════════════════════════════════════════════════════════════════════
<SLICE ID>: <NAME>
═══════════════════════════════════════════════════════════════════════════════
[INSERT §4.9 THE DEFECT: mechanism, chain, consequence]
[INSERT §4.10 DECISIONS ALREADY MADE]
BUILD:
  1. <exact file>: <exact change>
  2. <exact file>: <exact change>
[INSERT §4.12 COPY THE RIGHT PATTERN, if a majority pattern is the trap]
[INSERT §4.11 TRAPS]
GATE: <literal commands>. All green before you continue. Baseline <n> → expected <n+k>.

<repeat the banner for each checkpoint>

OUT OF SCOPE: do not start these, do not drift into them: <named items, by path>.
[INSERT §4.13 WHAT YOU CANNOT DO, if anything is blocked]
[INSERT §4.14 DO/DON'T + DEFINITION OF DONE + REPORT]

<Terminal imperative: "Start with checkpoint A now." | "Do not start the next slice; report and wait.">
```
