# 5.A: Single-artifact redesign · `/genprompt:redesign`

| | |
|---|---|
| **Use when** | One screen, dialog, component, module or controller needs a senior-level rebuild |
| **Not when** | Several files share the problem → `:slice`. A behaviour defect with a repro → `:fix` |
| **Autonomy** | Code-writing: an approval gate by default (show the plan first), a MODE block if `--unattended` |
| **Baseline delta** | Tests unchanged or up. No existing test may be weakened |
| **Length tier** | Focused (200) |
| **Deliverable** | The rebuilt artifact, plus a summary of its decisions |

## Generator: before emitting

- Read the target file. The prompt names what is actually wrong with it (`file:line`), not
  generic advice.
- Take the role from the NEAREST manifest to the file (not the git root), and keep
  one stack per role, because a blended role advises for neither. If the contract states a persona,
  use it verbatim.
- Pull the contract's rules for this kind of artifact: design-system components, tokens,
  typing, RTL, accessibility, naming.
- Decide UI versus non-UI. A UI artifact gets the UI/UX step. A module or controller gets the
  API-surface / error-handling / boundaries step instead.

## Required blocks

- §4.5, §4.6 (short), §4.7 (a falsifying artifact about this file), §4.14
- §4.19 or §4.8

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
Read <PROFILE.contract> first. It is the binding conventions contract, and for this artifact it
requires: <the contract's relevant rules, e.g. design-system components, tokens, typing, RTL>.

Act as a <PROFILE.role>. Rebuild `<target file>` (<screen|dialog|component|module|controller>)
to a senior standard.

WHAT IS WRONG WITH IT TODAY (grounded):
- <file:line>: <problem and its consequence>
- <file:line>: <problem and its consequence>

1. Analyse the current implementation before changing anything; state what it does today.
2. <UI: redesign layout, spacing, hierarchy, states (loading/empty/error), accessibility>
   <non-UI: tighten error handling, boundaries and naming. Keep the public surface (exports, CLI
   flags, messages, exit codes) exactly as it is>
3. Refactor: structure, naming, state handling, separation of concerns. Extract sub-parts only
   where it earns its keep.
4. Preserve the artifact's observable behaviour exactly: outputs, errors, exit codes and public
   exports. If a change seems worth making, propose it in the plan and wait for my yes; do not make it.
5. Remove weak patterns and needless complexity. Do not over-engineer.
6. Touch nothing outside this file and the pieces you extract from it.

OUT OF SCOPE: do not start these, do not drift into them:
- <sibling files by path>, because <their behaviour is what this rebuild must keep>
- <roadmap items by ID>, because <they are separate slices>

[INSERT §4.19 approval gate, or §4.8 MODE if unattended]
Constraints: <PROFILE.contract> wins over this prompt. No new packages, no new env vars.
<git posture>. Out of bounds: <PROFILE.forbidden>.

[INSERT §4.14: literal gates, each labelled (script|contract|derived); baseline unchanged or up;
 REPORT starting with the GENPROMPT-REPORT line]
Summarise: UI/UX (or API) improvements, structural improvements, logic changes, the key decisions,
and what you deliberately left alone and why.
<terminal imperative>
```

## Traps

- Generic "modernise it" advice yields a restyle that ignores the real defect. Name the
  defects.
- A role blended from two stacks ("React/Laravel engineer") produces advice for neither.
