## 8. Request grammar

If no target is named, the protocol resolves one (argument ▸ continuation ▸ cwd ▸ ask) and shows
it in the TARGET LOCK.

<!-- BEGIN GENERATED: tools/build_shims.py (edit the tables there, then run it) -->

### Entry

```text
/genprompt:auto       [task, or a pasted worker report, or empty for the picker]  pick the archetype from the request and emit its prompt, or offer the picker
```

### Build and change

```text
/genprompt:redesign   <file path> (<screen|dialog|component|module|controller>)  A  one artifact, senior-level rebuild
/genprompt:kickoff    <unit to start>                                 C  start work over uncommitted WIP
/genprompt:slice      Slice <ID>, scope: <bullets>                    D  one vertical slice, checkpoints
/genprompt:greenfield <layer> studying <reference repo>               G  new layer, reference studied first
/genprompt:roadmap    drive <doc> to done                             I  whole backlog, in parts
/genprompt:fix        <defect list, or the audit/report that found them>  L  confirmed defects, repro + acceptance each
/genprompt:test       <area | coverage target | flaky or vacuous tests>  O  test engineering
/genprompt:perf       <symptom or target metric>                      R  measure, then optimise
/genprompt:upgrade    <package> <from> -> <to>  |  <migration>        S  majors, ORM/data/platform migrations
/genprompt:hotfix     <symptom, since when, who is affected>          U  triage → mitigate → root cause
/genprompt:cleanup    <dead code | removal | restore-green | refactor target>  V  no behaviour change
```

### Understand, decide, document

```text
/genprompt:audit      <area to assess>                                B  read-only assessment, one doc
/genprompt:plan       <unit> <backend|frontend|cross-repo>            F  plan doc, no code
/genprompt:onboard    [repo]                                          M  map a repo, draft its contract + profile
/genprompt:design     <ADR | API contract | schema | design system | spike>: <decision>  N  design docs, no production code
/genprompt:review     <base..head | branch | PR number | last N commits>  P  code review, findings only
/genprompt:security   <area | whole app>                              Q  threat model + hardening
/genprompt:docs       <doc> for <audience>                            W  docs checked against the code
/genprompt:investigate <symptom: what happens vs expected, and how to trigger it>  X  unknown-cause bug → root cause, hand-off to :fix
```

### Ship and continue

```text
/genprompt:approve    decisions: <list>; order: <...>  |  amend <prior prompt>  E  rulings / amendment
/genprompt:commit     <work to commit> [verify+]                      H  commit & push, staged by path
/genprompt:next       <paste the worker's report, or nothing if it is already in the chat>  J  the next prompt
/genprompt:resume     <unit/slice the worker was mid-way through>     K  re-anchor after compaction
/genprompt:release    <version | environment | handover>              T  release/deploy, approval per action
```

### Utilities (they emit no worker prompt)

```text
/genprompt:help       [goal, e.g. 'I need to upgrade Laravel']  "I want to X" → which command, with flags and examples
/genprompt:history    [repo] [n]             the latest n shard rows (default 10) and the follows chain
/genprompt:doctor     [--suite | --archive | --suggest-fixes]  integrity check of the rules and the archive
/genprompt:learn      <rule or lesson>       save a lesson as a personal rule in ~/.genprompt/local-rules.md (shows the diff first)
/genprompt:profile    [repo] [--dry-run]     derive or refresh the profile card; no prompt
```

<!-- END GENERATED -->

### Modifiers (any archetype command)

| Flag | Effect |
|---|---|
| `--repo <name\|path>` | Target this repo, whatever the cwd or continuation says |
| `--go` | Skip the TARGET LOCK wait (the lock facts are still printed at the top) |
| `--attended` / `--unattended` | Force an approval gate (§4.19) or a MODE block (§4.8). Code-writing archetypes only: read-only ones (audit, plan, commit, onboard, design, review, docs) do not offer it |
| `--dry-run` | Compose and print, but write nothing: no archive file, no shard row, no profile card (for testing) |
| `--brief` | Aim for about 60% of the archetype's length budget |
| `--follows <file>` | Set the chain link explicitly, when it cannot be inferred |
| `--verbose` | Print the full self-check table in chat, not just the verdict line and the FAIL/N/A rows (the archive file always has the full table) |

Auto-go (no flag): with `auto-go: on` in `~/.genprompt/local-rules.md` (set it with
`/genprompt:learn auto-go on`), the lock skips its wait like `--go`, but only when the target came
from an explicit argument, the profile card is fresh, and nothing is unknown. Off by default.

---
