# 5.V: Cleanup / maintenance · `/genprompt:cleanup`

| | |
|---|---|
| **Use when** | Remove dead code or a retired feature, park a feature behind a flag, restore a red build to green, tighten or change CI gates, or refactor with **no behaviour change** |
| **Not when** | The behaviour should change → `:slice` or `:fix`. Dependency majors → `:upgrade` |
| **Autonomy** | Code-writing: §4.8 MODE or §4.19 gate. Deletions are listed before they happen |
| **Baseline delta** | **Unchanged** (the same tests pass). It goes down only for tests of the removed code, listed one by one |
| **Length tier** | Focused (200) |
| **Deliverable** | A smaller or cleaner tree with an identical behaviour surface, and a list of what was removed and why it was safe |

## Generator: before emitting

- **Prove "dead" before prescribing a deletion.** Find every reference with Grep (routes, config,
  jobs/schedules, templates, dynamic string references, reflection/container bindings, tests,
  docs). A feature that is *inert by design* (§2.8) is not dead: it needs a ruling.
- **Restore-green:** read the failing gate's output if the report includes it. The goal is the
  **root cause** of the red, not a skip or a loosened threshold.
- **CI gate changes:** make any loosening explicit and justified. Tightening needs the tree to pass
  first.
- **Refactor:** name the invariant (public API, rendered output, response shapes) and how to prove
  it unchanged.

## Required blocks

- §4.5, §4.7, §4.10, §4.11, §4.14
- §4.20 one predicate, not N guards (for consolidation refactors)
- §4.8 **or** §4.19

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]
Task: <remove <feature/dead code> | park <feature> behind <flag> | restore <gate> to green | refactor <area>
without behaviour change>.

[INSERT §4.8 MODE or §4.19 gate]
INVARIANT: <what must be identical before and after: routes, responses, rendered output, public API>.
Prove it with: <tests / route list diff / snapshot / output diff>.

CANDIDATES (references I found; you must re-check before deleting):
- <path>: referenced by <none | only tests | …>
[INSERT §4.11 TRAPS: dynamic references, config/cron/schedule entries, container bindings,
 migrations (append-only: never delete an applied migration)]
[INSERT §4.10 DECISIONS: <inert feature X stays; flag default; what is out of scope>]

STEP 1: list every deletion/change with its reference check. Report, then proceed (MODE) or wait (gate).
STEP 2: apply in small commits: one concern per commit.
STEP 3: prove the invariant.

[INSERT §4.14: gates <literal>; baseline <n> UNCHANGED (or −k: exactly these removed tests: …);
 DON'T skip/xfail tests, loosen thresholds, or delete migrations]
Start with STEP 1 now.
```
