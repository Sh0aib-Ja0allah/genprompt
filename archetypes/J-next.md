# 5.J: Continuation (from a worker stop-report) · `/genprompt:next`

| | |
|---|---|
| **Use when** | A worker stop-report arrived. This is also the default when a report is pasted with no command |
| **Not when** | The report needs rulings on disputed findings → `J+E`. The worker lost context → `:resume` |
| **Autonomy** | That of the archetype emitted next (usually D, E, H or L) |
| **Baseline delta** | That of the archetype emitted next. The Situation block carries the before-numbers |
| **Length tier** | Delta (120) when continuing a running shape; otherwise the tier of the emitted archetype |
| **Deliverable** | The next prompt, **or** a §4.26 closeout when nothing is left to emit |

## Generator: before emitting

- **Derive the next step from the report; do not ask what it is.** The answer is almost always in
  what the worker says it finished, deferred or hit. Ask only about a fork that cannot be derived
  and matters.
- **Verify the report by reading, never by running:**
  - `git log --oneline -10` and `git status --porcelain -uall`
  - `git diff --stat <prev>..HEAD`
  - the changed files, and the test files (count the test functions if the numbers matter)

  Label every number `verified by artifact (<what>)` or `reported, not confirmed`.
- **Confirm the previous instruction actually landed.** Check the branch, not the report. An
  amendment that was never pasted is the most expensive failure on record.
- **If the report shows the previous prompt was wrong**, lead with §4.16 corrections.
- **Nothing left?** If the verified state shows the work is done, or blocked only on the user,
  emit a §4.26 closeout and a status row (§10). Do not force a prompt.
- **Prefer the thorough option** (a whole-surface review over a scoped one, a root-cause fix over a
  patch, clean multi-commit history), and still surface the trade-off.

## Template

```text
[INSERT §4.4 Situation: SHAs; before→after counts, each labelled verified-by-artifact or reported;
 tree state; what flipped]
[INSERT §4.16 corrections, if my previous prompt was wrong or under-specified]

<Then the next prompt, built from the emitted archetype's template. Its gates are literal, even if
 unchanged since the last prompt.>
```

**Label hybrids honestly:** `J+L`, `J+D`, `J+E`. The filename command words follow the label
(`next+fix`).
