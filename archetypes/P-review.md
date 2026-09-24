# 5.P: Code review · `/genprompt:review`

| | |
|---|---|
| **Use when** | Review a diff, a branch, a PR or the last N commits before building on them or shipping them |
| **Not when** | A whole-repo assessment → `:audit`. Security-focused → `:security` (or `P+Q`). Proving tests are load-bearing (mutation) → `:test` |
| **Autonomy** | N/A: read-only. Writes are enumerated: one review doc, or none (chat-only), plus contract-mandated tools and gate side effects |
| **Baseline delta** | The **reported** baseline at the range head, labelled verified/reported; expected delta **unchanged**. Gates run only when HEAD equals the head SHA and the tree is clean |
| **Length tier** | Focused (200); measured-large allowance +20% for more than 3 commits or 50 files (§4.21) |
| **Deliverable** | A severity-ranked findings register (§4.25) with per-commit attribution, a FALSE POSITIVES table, a verdict (ship / fix first / rethink), and a hand-off list for `:fix` |

## Generator: before emitting

- **Pin the range by SHA:** `<base_sha>..<head_sha>`, never `HEAD~N`. A live repo moves, and a
  relative range slides under the reviewer. Read `git diff --stat <base>..<head>`. Name the 5–8
  files that matter most, and the bulk to skip (generated assets, lockfiles, captures).
- **Compare the range with the working tree:** `git diff --name-only <base> <head>` against
  `git status --porcelain -uall`. If they overlap, or the tree is occupied (PROTOCOL Step 4), the
  prompt carries the **HOW TO READ** block and §4.27. The reviewer reads committed content by SHA
  and cites `file:line@<head>`.
- **Build the CLAIMS block:** one line per commit (`<sha> <what it claims>`), from
  `git log -1 --format=%B <sha>`. Include claimed numbers (test counts, "N mutations killed"). A
  claimed mutation result can never be confirmed read-only: label it reported.
- **Map each commit to the prompt that produced it** (§10.4: shard rows by date and subject, or the
  brief's HEAD anchor). Point the reviewer at those briefs by path, and at their "do not fake" or
  acceptance lists as review criteria. A commit with no brief is labelled "no brief".
- **Choose the lenses for this change:** correctness, contract compliance, tests (would they fail
  if the change were reverted?), security, performance, data/migrations, UX/RTL/a11y, docs drift.
  Drop the lenses that cannot apply, and say why.
- **Gates:** the full derived list (§2.5), run only under the HEAD-and-clean condition, with their
  side effects listed. Never run a suite that shares a test database with a live session.
- **Report destination:** a review doc named per §2.7 (default `code-review-<date>` in the repo's
  case style), **or chat-only** when the tree is occupied or a doc would land in someone else's
  commit.
- **The worker never edits.** Fixes are a separate `:fix` prompt that consumes this register.

## Required blocks

- §4.5, §4.6, §4.7
- §4.22 (with expected drift marked)
- §4.25 (with Commit column and `@<head>` citations for a range)
- §4.13, §4.14 (gates + report)
- §4.20 explicit tool allow-list
- §4.20 epistemics (review wording)
- §4.27 when occupied

## Template

````text
Repo: <PROFILE.path>  (branch `<PROFILE.branch>`; <scope>)
Role: <PROFILE.role>, acting as a code reviewer.
[INSERT §4.5 contract precedence: point to the hard rules by line; say this review needs none of the permissions they reserve]

TASK: review <base_sha>..<head_sha> (<N> commits, <F> files, +<a>/-<d>; <bulk to skip>). Deliver a
severity-ranked findings register and a verdict. You change nothing.

[INSERT §4.22 VERIFY BEFORE STARTING: HEAD and base SHAs (HEAD moving is EXPECTED drift: keep the
 range pinned); the tree state (expected drift if occupied)]
[INSERT §4.27 OCCUPIED TREE, if the occupancy check fired]

WHAT THE RANGE CLAIMS. Read each full message (`git log -1 --format=%B {sha}`) and hold the code to it:
- <sha>  <claim, with any claimed numbers>                    (brief: <file> | no brief)
- <sha>  <claim>
Briefs are read-only context: <archive paths>. Hold <commit(s)> to <brief>'s "<do not fake / acceptance>" list.

═══════════════════════════════ HOW TO READ THE RANGE ════════════════════════════════
[generator: include this banner only if the range and the working tree overlap, or the tree is occupied]
The working tree is NOT the range: <n> of the range's files are modified on disk. Never Read or Grep a
range file from the working tree.
- Committed content: `git show {head}:{path}`. Search: `git grep -n {pattern} {head} -- {path}`.
- Change per commit: `git show {sha} -- {path}`. Whole range: `git diff {base} {head} -- {path}`.
- Cite `path:line` as the line in `git show {head}:{path}`, and say so in the register header.

Start with the files that matter most:
1. <path>: <what to check there, and why it matters>
2. <path>: <…>
Skip: <bulk>, except <the one check that needs it>.

LENSES: <kept lenses, each with the repo-specific thing to check>. Dropped: <lens: reason>.
Tests: decide whether a key test would fail on revert by READING its assertion. Watch for the
vacuity shapes this repo has shipped before: <shapes, if any>.

[INSERT §4.6 SOURCE OF TRUTH: contract > requirements > architecture (mark stale) > commit messages
 and briefs = CLAIMS, never evidence]
[INSERT §4.7 SKEPTICISM: a falsifying artifact from this repo; claimed numbers labelled]

[INSERT §4.25 FINDINGS register, with the Commit column and file:line@<head>]
[INSERT §4.20 epistemics: "You were asked to find problems, so you will be tempted to find some.
 Evidence at file:line is what separates a finding from a suspicion." Retire leads in FALSE POSITIVES]

GATES: run them ONLY if HEAD is <head_sha> and the tree is clean. Otherwise write "not run: {reason}".
    <literal gate>   <- (script|contract|derived[, no baseline]) <source>
    <literal gate>
Side effects (the only writes they may make): <build output, caches, test DB>.
⚠ NEVER RUN: <destructive commands, including the contract's own warnings>.
Baseline (reported at <head_sha>): <numbers>. Expected delta: unchanged, because a review changes
nothing. Report actual numbers, never just "passes".

READ-ONLY. You may ONLY: Read/Glob/Grep (not on dirty range files); run read-only git (log, show, diff,
status, rev-parse, ls-files, grep); run the gates above under their condition; use <contract-mandated
tools>; and <write `<review doc path>` | report in chat only>. Do not edit, stage, stash, commit, branch,
create a worktree, push, or start a server.

[INSERT §4.13 WHAT YOU CANNOT DO: e.g. confirm mutation claims (needs edits → a :test prompt); checks that
 need a running server; gates while the tree is occupied]

VERDICT: ship / fix first (list the ids) / rethink (why).
HAND-OFF: the FIX-NOW ids, ordered, each with file:line, ready for a `:fix` prompt. Flag any that touch
a file with uncommitted changes.

REPORT: the range (SHAs); the files read in full, as diff only, or skipped, with reasons; the lenses
applied and dropped; the register and FALSE POSITIVES; the gate numbers or "not run" and why; every
numeric claim in the messages, labelled verified by artifact / reported, not confirmed / contradicted
(<id>); the verdict and hand-off.
Negative confirmations: no file edited, created, staged or stashed; no commit, branch, worktree or push;
no server started; no ⚠ command run; `git status --porcelain -uall` at the end differs from the start
only in <the live session's paths | nothing>.

Begin with the VERIFY block, then <the first file>.
````

## Traps

- **Reviewing the working tree instead of the range** when another session is editing it. You get
  citations from someone else's work in progress.
- **Taking "N mutations killed" as evidence.** It needs an edit to confirm; that belongs to `:test`.
- **Gates on a dirty or shared tree** measure someone else's work, and can break their test run.
- **A review doc in `docs/` during a live phase** gets swept into the other worker's commit. Use
  chat-only.
