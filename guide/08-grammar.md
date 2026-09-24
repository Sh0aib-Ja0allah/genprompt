## 8. Request grammar

If no target is named, the protocol resolves one (argument ▸ continuation ▸ cwd ▸ ask) and shows
it in the TARGET LOCK.

### Build and change

```text
/genprompt:slice      Slice <ID>, scope: <bullets>                    D  one vertical slice, checkpoints
/genprompt:fix        <defect list | the audit/report that found them> L  confirmed defects, repro + acceptance each
/genprompt:roadmap    drive <doc> to done                             I  whole backlog, in parts
/genprompt:redesign   <file> (<screen|dialog|section|component|module>) A one artifact, senior-level rebuild
/genprompt:greenfield <layer> studying <reference repo>               G  new layer, reference studied first
/genprompt:kickoff    <unit>, dirty WIP present                       C  start work over uncommitted WIP
/genprompt:test       <area | coverage target | flaky/vacuous tests>  O  test engineering
/genprompt:perf       <symptom or target metric>                      R  measure, then optimise
/genprompt:upgrade    <package/framework> <from> -> <to> | <migration> S majors, ORM/data/platform migrations
/genprompt:hotfix     <incident: symptom, since when, blast radius>   U  triage → mitigate → root cause
/genprompt:cleanup    <dead code | removal | restore-green | refactor> V no behaviour change
```

### Understand, decide, document

```text
/genprompt:onboard    [repo]                                          M  map a repo, draft its contract + profile
/genprompt:audit      <area>                                          B  read-only assessment, one doc
/genprompt:plan       <unit> <backend|frontend|cross-repo>            F  plan doc, no code
/genprompt:design     <ADR | API contract | schema/ERD | design system | spike> N  design docs, no production code
/genprompt:review     <diff | branch | PR # | last N commits>         P  code review, findings only
/genprompt:security   <area | whole app>                              Q  threat model + hardening
/genprompt:docs       <README | API docs | runbook | admin/handover guide> W docs checked against the code
```

### Ship and continue

```text
/genprompt:commit     <work to commit>   (also: verify+commit)         H  commit & push, staged by path
/genprompt:release    <version | environment>                         T  release/deploy, approval per action
/genprompt:approve    decisions: <list>; order: <…> | amend <prior prompt>  E  rulings / amendment
/genprompt:next       <paste the worker's stop-report, or just paste it>    J  the next prompt
/genprompt:resume     <unit>, worker compacted mid-slice              K  re-anchor after compaction
```

### Utilities (they emit no worker prompt)

```text
/genprompt:auto       [task]      pick the archetype from the request, or offer the picker
/genprompt:help       [goal]      "I want to X" → which command, with flags and examples
/genprompt:history    [repo] [n]  the latest n shard rows (default 10) and the follows chain
/genprompt:doctor     [--suite|--archive]  integrity check of the rules and the archive
/genprompt:profile    [repo]      derive or refresh the profile card; no prompt
/genprompt:learn      <rule or lesson>     save a lesson as a personal rule in ~/.genprompt/local-rules.md (shows the diff first)
```

### Modifiers (any archetype command)

| Flag | Effect |
|---|---|
| `--repo <name\|path>` | Target this repo, whatever the cwd or continuation says |
| `--go` | Skip the TARGET LOCK wait (the lock facts are still printed at the top) |
| `--attended` / `--unattended` | Force an approval gate (§4.19) or a MODE block (§4.8) |
| `--dry-run` | Compose and print, but write nothing: no archive file, no shard row, no profile card (for testing) |
| `--brief` | Aim for about 60% of the archetype's length budget |
| `--follows <file>` | Set the chain link explicitly, when it cannot be inferred |

---
