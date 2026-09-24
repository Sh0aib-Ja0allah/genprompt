# 5. Archetypes

**Archetypes compose.** Pick the dominant letter, name the ones folded in, and take blocks from
each. The label is honest (`J+L`, `D+H`, `P+Q`); do not force a single letter. Labels join letters with
`+` only. `B→I` in prose means two separate prompts in sequence, and is never a label. The filename
uses the command words in the same order (`next+fix`).

Letters are permanent: archived prompts reference them. New archetypes take the next letter.

## Picker: "I want to…"

| I want to… | Use | # | Autonomy | Length tier |
|---|---|---|---|---|
| understand an unfamiliar or empty repo, and draft its contract | `:onboard` | M | read-only + docs | Focused |
| assess the state against the docs, and get a ranked backlog | `:audit` | B | read-only + 1 doc | Focused |
| plan a unit or cross-repo work, without code | `:plan` | F | read-only + 1 doc | Program |
| design one decision (ADR, API contract, schema/ERD, design-system map, spike) | `:design` | N | docs (+ scratch spike) | Program |
| build a new layer after studying a reference repo | `:greenfield` | G | docs → gate → code | Program |
| start a unit over messy uncommitted WIP | `:kickoff` | C | audit → gate → code | Focused |
| build one vertical slice | `:slice` | D | MODE or gate | Slice |
| drive a whole backlog doc to done | `:roadmap` | I | MODE + exit valve | Program |
| rebuild one screen, component or module | `:redesign` | A | gate (or MODE) | Focused |
| fix a list of confirmed defects | `:fix` | L | MODE or gate | Focused |
| handle a live incident fast | `:hotfix` | U | MODE + approval per live action | Focused |
| write, repair or harden tests | `:test` | O | MODE or gate | Focused |
| review a diff, branch, PR or recent commits | `:review` | P | read-only | Focused |
| threat-model and harden security | `:security` | Q | read-only → gate → fixes | Program |
| make something faster or lighter, measured | `:perf` | R | measure → gate → change | Program |
| upgrade a framework or dependencies, or migrate an ORM, platform or data | `:upgrade` | S | staged, gate | Program |
| remove dead code, restore green, refactor with no behaviour change | `:cleanup` | V | MODE or gate | Focused |
| write or repair docs, runbooks, guides | `:docs` | W | docs only | Focused |
| commit and push finished work (optionally verify first) | `:commit` | H | commit-only | Focused |
| cut a release, deploy, hand over | `:release` | T | approval per action | Program |
| rule on findings, lock decisions, amend a running prompt | `:approve` | E | inherits | Delta |
| continue from a worker's stop-report | `:next` | J | the emitted archetype's | Delta |
| re-anchor a worker that lost its context | `:resume` | K | the resumed slice's | Focused |

## Index

| # | Archetype | Command | File |
|---|---|---|---|
| A | Single-artifact redesign | `:redesign` | `A-redesign.md` |
| B | Audit / read-only assessment | `:audit` | `B-audit.md` |
| C | Kickoff with dirty WIP | `:kickoff` | `C-kickoff.md` |
| D | Slice execution | `:slice` | `D-slice.md` |
| E | Approval / rulings / amendment | `:approve` | `E-approve.md` |
| F | Planning-only | `:plan` | `F-plan.md` |
| G | Greenfield from a reference repo | `:greenfield` | `G-greenfield.md` |
| H | Commit & push (incl. verify+commit) | `:commit` | `H-commit.md` |
| I | Roadmap / backlog execution | `:roadmap` | `I-roadmap.md` |
| J | Continuation | `:next` | `J-next.md` |
| K | Resume after compaction | `:resume` | `K-resume.md` |
| L | Defect-driven fix slice | `:fix` | `L-fix.md` |
| M | Onboard / discovery | `:onboard` | `M-onboard.md` |
| N | Design / spike / ADR | `:design` | `N-design.md` |
| O | Test engineering | `:test` | `O-test.md` |
| P | Code review | `:review` | `P-review.md` |
| Q | Security review and hardening | `:security` | `Q-security.md` |
| R | Performance | `:perf` | `R-perf.md` |
| S | Upgrade and migration | `:upgrade` | `S-upgrade.md` |
| T | Release and deploy | `:release` | `T-release.md` |
| U | Hotfix / incident | `:hotfix` | `U-hotfix.md` |
| V | Cleanup / maintenance | `:cleanup` | `V-cleanup.md` |
| W | Documentation | `:docs` | `W-docs.md` |

**Every archetype file has the same shape:**
1. a header table: use when · not when · autonomy · baseline delta · length tier · deliverable
2. generator steps before emitting
3. required blocks (§4)
4. the template (§4.0 notation)
5. traps, where they apply

**Common lifecycles** (each arrow is a new prompt):
- New repo: `onboard → plan → roadmap → review → commit → release`
- Feature: `slice → next → … → review → commit`
- Bug report: `audit or review → fix → commit`
- Incident: `hotfix → release → docs`
- Maintenance: `upgrade → test → cleanup → commit`
