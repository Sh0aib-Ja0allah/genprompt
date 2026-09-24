# 5.G: Greenfield from a reference repo · `/genprompt:greenfield`

| | |
|---|---|
| **Use when** | Build a new layer or app after studying a reference repo |
| **Not when** | The repo is empty and has no reference → `:onboard`, then `:plan`. Most greenfield work is best done as `F+G+I` (plan, then drive the plan) |
| **Autonomy** | Phases 1–3 write docs only. §4.19 gate before Phase 4 |
| **Baseline delta** | Up from zero. The first gates may be `test: NONE`; say so |
| **Length tier** | Program (350) |
| **Deliverable** | A rules doc from the reference, a target blueprint, then the implementation and its report |

## Generator: before emitting

- **The reference repo is an argument, not a constant.** Ask for it if it is not given. Derive a
  profile for the reference too: its stack decides how much transfers.
- **Name the specific reason cloning is wrong here** (a different framework major, routing model or
  conventions). "Reference, not template" is only credible with a concrete reason.
- **Name the three docs by §2.7** (the repo's convention, or N6 with a declared new convention).
  Never use a filename left over from another project.
- **Take Phase 1's study list from the reference's stack** (`stacks/stack-matrix.md`), not from a
  React-shaped default.

## Required blocks

- §4.5, §4.6, §4.19, §4.14
- §4.20 THE CENTRAL PROBLEM TO SOLVE, if the target has one

## Template

```text
Repo: <PROFILE.path>
Reference repo to study (READ-ONLY): <reference abs path> (<reference stack>)

Study the reference deeply, compare it to our docs, define the target architecture and rules, then
build what this repo needs. Use it as a STRUCTURAL reference, not something to clone: <the specific
reason cloning is wrong here>. Be repo-specific; give no generic advice.

Phase 1: extract rules. Study the reference's <stack-appropriate list: e.g. routing, layouts,
  shared/feature components, state, data layer, auth, forms/validation, error/loading/empty states,
  theming, naming | or: modules, controllers, policies, jobs, migrations, API resources>.
  Write `<docs path per §2.7: reference analysis rules>`: overview, structure, inventory, shared
  patterns, OUR rules, Do/Avoid, and a per-unit checklist.
Phase 2: write `<docs path per §2.7: target blueprint>`, defining the FULL target: architecture,
  folder layout, route/screen/module map, reusable parts, auth flow, patterns, implementation order,
  risks. **List the ACTUAL pages/components/modules. Never "create the needed pages".**
Phase 3: present the concrete file/folder plan.
[INSERT §4.19 approval gate]
Phase 4: implement in logical slices, then write `<docs path per §2.7: implementation report>`.

[INSERT §4.14 verification + report]
Start with Phase 1 now.
```
