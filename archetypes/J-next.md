# 5.J: Continuation (from a worker stop-report) · `/genprompt:next`

| | |
|---|---|
| **Use when** | A worker stop-report arrived. This is also the default when a report is pasted with no command |
| **Not when** | The report needs rulings on disputed findings → `J+E`. The worker lost context → `:resume` |
| **Autonomy** | That of the archetype emitted next (usually D, E, H or L) |
| **Baseline delta** | That of the archetype emitted next. The Situation block carries the before-numbers |
| **Length tier** | Delta (120) when continuing a running shape; otherwise the tier of the emitted archetype |
| **Deliverable** | The next prompt, or a §4.26 closeout when nothing is left to emit |

## Generator: before emitting

- Parse the `GENPROMPT-REPORT` header line first (§4.14), if the report has one:
  - `Repo` → the target (Step 1, rule 2). `Prompt` → the archive file and its shard row; walk its
    `follows` chain from there, and set this prompt's `follows` to it.
  - `Branch` / `HEAD` → what to verify with git below. `Gates` → the numbers to label.
  - `Status`: `done` → the next step; `partial` → say which checkpoints landed and resume the rest;
    `blocked` → rulings on the blocker (`J+E`) or a §4.26 closeout.
  - No header (older workers, hand-pasted reports): fall back to the free-form report, and say so in
    the grounding notes.
  - The fields are claims, verified by artifact, never by trust. If `Branch`, `HEAD` or
    `Status` disagree with git, that is a §4.16 correction: name the mismatch in the prompt, never
    fix it silently.
- A report from a `--split` lane (its archived task starts `W<k>/<N>:`): read §8.1 first. The next
  prompt stays inside that lane's owned paths. Once every lane's report is `done` and verified,
  the next prompt is the archived merge prompt (`merge/<N>:`), re-issued with the verified lane
  SHAs (`Re-issues`), not a new plan.
- `--from <session>`, or a report that arrived as a `<cross-session-message>`: read §10.8 item 10
  first. Ingest it only if this chat sent a prompt to that exact sender or the request has
  `--from` with that name; otherwise relay it to the user, ask, and compose nothing.
- Derive the next step from the report; do not ask what it is. The answer is almost always in
  what the worker says it finished, deferred or hit. Ask only about a fork that cannot be derived
  and matters.
- **Verify the report by reading, never by running:**
  - `git log --oneline -10` and `git status --porcelain -uall`
  - `git diff --stat <prev>..HEAD`
  - the changed files, and the test files (count the test functions if the numbers matter)

  Label every number `verified by artifact (<what>)` or `reported, not confirmed`.
- Confirm the previous instruction actually landed. Check the branch, not the report. An
  amendment that was never pasted is the most expensive failure on record.
- If the report shows the previous prompt was wrong, lead with §4.16 corrections.
- Nothing left? If the verified state shows the work is done, or blocked only on the user,
  emit a §4.26 closeout and a status row (§10). Do not force a prompt.
- Prefer the thorough option (a whole-surface review over a scoped one, a root-cause fix over a
  patch, clean multi-commit history), and still surface the trade-off.

## Template

```text
[INSERT §4.4 Situation: SHAs; before→after counts, each labelled verified-by-artifact or reported;
 tree state; what flipped]
[INSERT §4.16 corrections, if my previous prompt was wrong or under-specified]

<Then the next prompt, built from the emitted archetype's template. Its gates are literal, even if
 unchanged since the last prompt.>
```

Label hybrids honestly: `J+L`, `J+D`, `J+E`. The filename command words follow the label
(`next+fix`).
