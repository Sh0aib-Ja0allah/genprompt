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
/genprompt:commit     <work to commit>                                H  commit & push, staged by path
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
| `--send <session>` | Opt-in: also send the archived prompt to that Claude session (the exact name from ListAgents, byte for byte; quote a name with spaces: `--send "genprompt : Worker B"`). Adds a `Send to` lock row and asks yes/no before sending, even under `--go`; a project mismatch is named. Copy/paste stays the default (§10.8) |
| `--verbose` | Print the full self-check table in chat, not just the verdict line and the FAIL/N/A rows (the archive file always has the full table) |

### Per-command modifiers

Each is offered only by the commands named (their argument-hint lists it).

| Flag | Commands | Effect |
|---|---|---|
| `--split <N>` | `:plan`, `:roadmap` | N parallel lane prompts with disjoint file ownership, plus one merge prompt (§8.1) |
| `--chat-only` | `:review` | The findings register is reported in chat; no review doc is written |
| `--verify` | `:commit` | A read-only verification pass first; commit only once it is clean (the older bare `verify+` means the same) |
| `--pr` | `:commit` | After the commits: create the branch, push it and open a PR with a body template, each step a separate approval (§4.23, §8.2). The worker runs them; the generator never pushes (a bare `pr` means the same) |
| `--readonly-phase` | `:security`, `:perf` | Emit only the read-only first phase: security's Phase 1 (threat model and findings), perf's measurement and plan. The prompt stops there and changes no code |
| `--from <session>` | `:next` | Take the stop-report from the latest cross-session message that session sent here (the worker pushes it, §10.8); none yet → paste it |

Auto-go (no flag): with `auto-go: on` in `~/.genprompt/local-rules.md` (set it with
`/genprompt:learn auto-go on`), the lock skips its wait like `--go`, but only when the target came
from an explicit argument, the profile card is fresh, and nothing is unknown. Off by default.


### 8.1 `--split <N>`: parallel lanes for `:plan` and `:roadmap`

Read this only when the request carries `--split`. The run emits N lane prompts and one merge
prompt instead of one prompt; everything else (Steps 1–4, one TARGET LOCK) is unchanged. N is 2–4.

**Partition first, by files, from what you read.**
- List the work items (plan: the audit dimensions or workstreams; roadmap: the backlog item ids)
  and, for each, the paths it will touch, grounded by `file:line` or `git grep`.
- Group them into N lanes whose path sets are disjoint. A path two lanes need (a lockfile, a
  route or DI registry, a migrations index, `CHANGELOG.md`) belongs to no lane: the merge prompt
  owns it, and any item that must edit it moves to the merge prompt.
- If the items do not split into N disjoint lanes, use the largest N that does and say so under
  Interpretations; if none does (N < 2), emit the normal single prompt and say why.
- `:roadmap` only: if the contract forbids extra branches or worktrees, don't split; say so in the
  lock's Unknown section.

**The workspace.** One folder outside the repo, next to it: `<repo>-split-<slug>/` holding
`findings/` and, for `:roadmap`, the lane worktrees `w1/` … `wN/`.
- Roadmap lanes each work in `git worktree add <folder>/w<k> -b <branch>-w<k> <base sha>`, all from
  the same base SHA (a §4.22 verify-at-start entry). They commit on their own branch only and
  never push or merge.
- Plan lanes stay read-only on the repo; each writes only `findings/W<k>.md`.
- `findings/` is shared: each lane writes only its own `findings/W<k>.md` and may read the others.
  A need in another lane's paths is recorded there (§4.20 RECORD, DO NOT ACT), never acted on.

**Each lane prompt** follows the archetype's template, cut to its lane, and adds:
- an ownership table, `Lane | Owns (paths/globs) | Items`, one row per lane, with its own row
  marked, and the rule: touch only your Owns paths; the other lanes run in parallel right now
- the §4.27 block, adapted: the other lanes are the live sessions, and their worktrees and branches
  are out of scope
- its tier is the archetype's, over its share of the items; `:plan` lane ids are prefixed by lane
  (`W1-A-03`) so the merged doc's ids stay unique and stable
- a REPORT whose `GENPROMPT-REPORT` line names its own lane prompt file

**The merge prompt** (Focused tier, emitted last, run after every lane reports `done`):
- STEP 0: every lane branch (roadmap) or `findings/W<k>.md` (plan) exists; otherwise STOP
- for each lane, `git diff --name-only <base sha>..<branch>-w<k>` lists only that lane's Owns paths;
  any other path is a STOP, named, never merged
- roadmap: merge the lanes in the stated order with the contract's git posture, apply the
  merge-owned items, and run the literal gates after each merge; plan: author the ONE plan doc
  (the archetype's TOC) from the lane files
- dispose of every `findings/` entry (done here, deferred with a reason, or a new item)
- remove the worktrees (`git worktree remove`) and the workspace folder last, and report

**Archive and print.**
- N + 1 prompts, each its own parts file and `archive.py` run, each with its own §6 self-check.
- All share one `follows` (the parent this run follows, or `-`), the archetype letters and the
  slug base: slugs `<slug>-w1` … `<slug>-wN`, `<slug>-merge`; tasks start `W<k>/<N>:` and
  `merge/<N>:`, which is how `:next` recognises a lane report (§5.J).
- `flags` includes `--split` (without its N).
- In chat, print each prompt in lane order, then the merge prompt, each followed by its verdict
  line and its FAIL/N/A rows; then one header table, the grounding notes, and every saved path.


### 8.2 `--pr`: the pull-request step for `:commit`

Read this only when a `:commit` request carries `--pr` (or a bare `pr`), and read §4.23 in
`guide/03-blocks.md` with it; name both in the grounding notes.

- Take the branch name and PR rules from the contract (else `<type>/<short-topic>` from the
  recent branch names), the base from the default branch, and the body from the repo's own
  `.github/pull_request_template.md` when it exists, else the PR BODY below.
- Create branch, push and open PR are three §4.23 actions: the worker asks before each one,
  because a push and a PR are outward-facing. You never push or open the PR yourself.
- The PR body holds only placeholders the worker fills from this repo (its diff, commits, gate
  output, the ticket id from the branch or contract): no client names, customer data, secrets
  or environment values, because a PR page is read more widely than the repo.
- Add this section after the template's CONSTRAINTS, and add the PR URL to its final report
  line:

```text
PULL REQUEST, after the commits. [INSERT §4.23 APPROVAL PER ACTION: (1) create branch
 <branch> from <base sha> (skip if already on it), (2) `git push -u origin <branch>`, (3) open the
 PR into <default branch> with `gh pr create --base <default> --head <branch> --title "<…>"
 --body-file {body file}`; no gh → show me the compare URL and stop]
PR BODY (<the repo's PR template, or this>), filled only from this repo:
  ## Summary: {what changed and why, 2–4 lines}
  ## Changes: {one line per commit: subject, short SHA}
  ## Verification: {each gate command with its actual numbers}
  ## Risk and rollback: {what could break; how to revert}
  ## Links: {ticket id from the branch or contract, or "none"}
  No client names, customer data, secrets, hostnames or environment values.
Do not merge the PR, request reviewers or change its settings unless I say so.
```

---
