## 4. Building blocks

Copy the **wording pattern**. Take every specific from the target repo. Real instances of each
block are in `examples/worked-examples.md`: they are illustrative only, and their specifics must
never leak.

**Which blocks are core.** Every code-writing prompt carries 4.5, 4.6, 4.7 and 4.14, plus 4.8
**or** 4.19. The archetype file lists what else it requires. The rest are situational.

### 4.0 Template notation (applies to every template in `archetypes/`)

| Notation | Meaning |
|---|---|
| `<PROFILE.field>` | A value from the profile card (§2.9). The only fields are: `path branch default_branch scope stack role contract ancestors truth gates docnaming code_roots forbidden blockers` |
| `<…>` | Fill it from grounding. Every one must be filled before emitting. None may reach the user. |
| `[INSERT §x.y]` | Insert that block, adapted to this repo. |
| `[generator: …]` | An instruction to you. Strip it; it never appears in the emitted prompt. |
| `{…}` | A **worker-side** variable inside a command the worker will run (`git show {sha}:{path}`). It stays in the emitted prompt; it is not a generator placeholder. |
| `═══` banner | The only banner character. Keep one width, 79 characters. |

**Fences.** When the emitted prompt itself contains a fenced block, the outer fence is four
backticks, so the prompt stays exactly one copyable block.

### 4.1 Header (generator- and user-facing: printed in chat and saved in the archive file, never inside the worker's block)

```text
| Date | <YYYY-MM-DD> |
| Archetype | <letter(s)>: <name> (§5.<X>)<, with <Y>-style blocks folded in> |
| Target repo | <abs path> · branch <branch> · scope <scope> |
| Follows | <prior prompt filename>   (or Amends / Depends on / Re-issues / Reviews) |
```

**Order in the archive file:** line-1 HTML comment (§10) → this table → grounding (§4.2) → the
fenced prompt → the self-check (§6). `Follows`, `Amends`, `Depends on`, `Re-issues` and `Reviews`
are what make the library a chain. Never omit one that applies.

### 4.2 Grounding notes (above the block; never sent to the worker)

```text
**Grounded by:** read-only pass over <what you read>. Findings that reshaped the prompt:
- <fact> (<file:line>). <why it changes the instruction>
- <worker claim> is verified by artifact (<what you read>) | reported, not confirmed
```

If a claim has no line here, it does not belong in the prompt.

### 4.3 What the user asked for, and interpretations locked in (overridable)

```text
## What the user asked for
1. <literal restatement>

## Interpretations locked in (stated to you, overridable)
**<decision>.** <why the literal words imply it, and what the other reading would destroy>
```

The costliest failure in this workflow is silently turning "disable X" into "delete X". This
block makes a reinterpretation visible before the prompt is pasted.

### 4.4 Situation: the worker's report, ingested with hard numbers

```text
## Situation
<items> landed (<short SHAs>). <tests/assertions/other counts> (from <before>). <tree state>.
Numbers: verified by artifact (<git log / diff / files read>) | reported, not confirmed.
```

A numeric baseline is what lets the next prompt *require movement*, or require *no* movement.

### 4.5 Repo anchor and contract precedence (the first lines inside the block)

```text
Repo: <PROFILE.path>  (branch `<PROFILE.branch>`<; monorepo: <IN root> IN scope, <siblings> OUT; do not touch them>)

Read `<PROFILE.contract>` FIRST. It is the binding conventions contract. Where this prompt and it
disagree, follow the contract and tell me.<If the prompt deliberately deviates from a contract rule:
"This prompt deviates from <rule> in one way: <how>. That deviation is authorised for this task only.">
```

Mention ancestor files **only** when the scan found some: `CLAUDE.md files above this repo
(<paths>) describe other projects and do not govern it.` Never name a file the scan did not find.

### 4.6 Source of truth, with authority annotations

```text
1. `<doc>`   <- binding; outranks <what>
2. `<doc>`   <- <scope of its authority>
3. `<doc>`   <- USEFUL BUT STALE: <the concrete staleness you found>. Believe the code.
Where a doc and the code disagree, the code wins and the doc gets fixed.
```

At least one annotation must be an exclusion or a staleness warning (§2.6).

### 4.7 Current-state skepticism, with a falsifying example

```text
CURRENT-STATE SKEPTICISM
- Do NOT assume any doc is still true. <the concrete drift you found>.
- Do NOT assume prior work is correct because it builds, lints or has a passing test:
  `<test or file>` <passes/claims> <X> while <Y is actually broken> (<file:line>).
  Treat green tests as a claim to verify, not as evidence.
- <Any register of ✅ marks>: hold each item to its ORIGINAL definition, not to the tick.
```

### 4.8 MODE FOR THIS SESSION (the autonomy contract, unattended)

```text
MODE FOR THIS SESSION
- You have STANDING APPROVAL for everything in <Parts A–F>. Do not wait for me between parts.
- Git: <the contract's branching rule, quoted or pointed to>. <commit cadence>. <push: yes, per
  <unit> | no>.
- Report at each boundary, then CONTINUE without waiting.
- Stop and ask ONLY for something in WHAT YOU CANNOT DO, or something that contradicts this prompt
  or the contract.
```

Use this **or** the §4.19 approval gate in a code-writing prompt, never neither and never both.
Read-only and commit-only archetypes state `Autonomy: N/A` in the lock instead.

### 4.9 The defect: mechanism, chain, consequence

```text
THE DEFECT: <file:line> <does X>. <causal step> (<file:line>) → <causal step> (<file:line>) →
<what the user actually sees or suffers>.
```

This replaces bare scope bullets. A bullet admits a dozen implementations, most of which miss the
point.

### 4.10 Decisions already made: do not re-litigate

```text
DECISIONS ALREADY MADE: implement exactly these, do not re-litigate:
- <AREA>: <decision> (<source: doc:line or ruling>).
- <AREA>: do NOT <tempting alternative>, because <mechanism> (<file:line>).
```

Include the **negative** decisions and the reason for each. An unattended worker meeting an open
question either stalls or guesses.

### 4.11 ⚠ TRAPS: per-item landmines

```text
TRAPS: each of these will break a naive implementation:
• <trap> (<file:line>): <what breaks, and how to avoid it>
```

### 4.12 Copy the right pattern: choosing a pattern by what it avoids

```text
COPY THE RIGHT PATTERN. This is the trap: the MAJORITY of <things> (<file:lines>) <do the defective
thing>. Copying that reproduces the bug you are fixing. Copy instead <the correct instance>
(<file:lines>). Use <the majority instance> only for <harmless detail>.
```

"Follow existing patterns" *causes* the bug when the majority pattern is the defective one.

### 4.13 WHAT YOU CANNOT DO: the stop-list

```text
WHAT YOU CANNOT DO: do not attempt, do not fake, do not stub as if live.
These need something only I can supply. Build to the boundary, label it, and list exactly what you need:
- <item>: <what is missing>. Blocks <what>. Would be unblocked by <what>.
Keep this list current, and do not let it silently shrink.
```

### 4.14 Verification, DO/DON'T, DEFINITION OF DONE, REPORT

```text
VERIFICATION: run before every commit. Never commit red.
    <literal gate 1>
    <literal gate 2>     <- <note: what CI runs / known-red gate / ⚠ destructive, needs my yes>
Report the actual numbers, never just "passes". Baseline: <numbers>. Expected delta: <up | unchanged | down because …>.
<environment facts the worker will hit: tools not on PATH, memory flags> (§11)

DO: <the 3–6 things most likely to be done wrong, stated positively>
DON'T: <the forbidden moves: dependencies, flipping live, weakening tests, touching OUT paths, …>

DEFINITION OF DONE: <gates green with the baseline moved as stated> + <the observable behaviour,
with the assertion that proves it> + <negative conditions: nothing added, flipped or touched outside scope>.

REPORT: per checkpoint: what you built; the decisions this prompt did not cover; the file list
reconciled against `git status`; the gate numbers; any existing test you touched and why; and
explicit confirmation of each DON'T.
```

### 4.15 Falsifiability standard

```text
- Reproduce with a failing test FIRST, then fix, then keep the test.
- Prove the fix is load-bearing: stash it and confirm that exactly the right cases go red. A fix
  whose absence does not fail a test is not proven.
- Adding a check where none existed → a positive control suffices. REPLACING one check with another
  → compare the admitted sets in both directions and test the delta, because a widening passes
  every existing test.
- Assert the legitimate case still succeeds before concluding a rule works.
```

### 4.16 Corrections to my previous prompt (the generator conceding an error)

```text
<n>. YOUR DEVIATION IS RIGHT: my instruction was <under-specified | wrong>.
I told you to <X> without checking <Y>. <What is actually true>. Keep <your version>, and record
the reasoning in <place>, because the next reader will see it diverge and assume it is a mistake.
```

This prevents two failures: a worker that deviated correctly re-applying the bad instruction next
turn, and a worker learning that deviations are unwelcome.

### 4.17 Quote the worker, and quote the source, verbatim

Quote the worker's exact sentence before ruling on it; a paraphrase silently widens or narrows the
claim. Quote the governing spec line with `path:line`, then do the arithmetic in the open:
*"RULE <n> VERBATIM (<path:line>): '<text>'. <N> required. <M> exist. Exactly <N−M> are missing:
<names>. Build those."*

### 4.18 The doc is wrong: follow the code

```text
⚠️ <DOC> IS WRONG ABOUT <AREA>. Follow the CODE:
- <doc> says <X>. <X> DOES NOT EXIST / is not what the code does. The real <thing> is <Y> (<file:line>).
```

### 4.19 Approval gate (attended mode only)

```text
Do not start coding until I approve the plan, unless I explicitly say "continue immediately".
```

### 4.20 Situational blocks (with wording to copy)

| Block | Use when | Wording to copy |
|---|---|---|
| **THE CENTRAL PROBLEM TO SOLVE** | Planning or long prompts. Without a priority signal they optimise breadth | `THE CENTRAL PROBLEM TO SOLVE: <the single defect or gap everything else sits on>, corroborated by <evidence A> and <evidence B>. Every workstream is ranked by how much it moves this.` |
| **Structure and its reasoning** | Ordering carries safety semantics | `Part \| Content \| Why here` table, then: `Do not reorder parts; the order is what makes <guarantee> hold.` |
| **Sequencing with rationale** | One ordering of two changes ships a disclosure or a break | `<A> lands before <B>, because <B> without <A> <exposes/breaks X> for every commit in between.` |
| **Oracle / predicate framing** | Fixes generalise badly, predicates generalise well | `The property that must hold: <predicate>. Test the predicate, not the fix.` |
| **One predicate, not N guards** | A fix with several call sites will drift | `Put the rule in ONE place (<where>) and route every call site through it.` |
| **RECORD, DO NOT ACT** | A finding needs a *decision*, not a fix | `RECORD, DO NOT ACT: <finding>. Write it to <doc> with the evidence. Do not change <code/grant> to "fix" it; that needs my ruling.` |
| **Epistemics / bias check** | The evidence is weak because of how it was gathered, or the task itself biases the worker | `This evidence came from <method>, which biases toward <X>. Treat it as a lead; reproduce independently before acting.` For reviews and audits: `You were asked to find problems, so you will be tempted to find some. Evidence at file:line is what separates a finding from a suspicion.` |
| **STOP / DEFER with revert** | Long unattended runs | `If an item cannot be made green: revert that item, log it DEFERRED with the reason, and move on. It is CORRECT to finish most items cleanly and defer the risky ones. NEVER leave a gate red. Never let one stuck item block the rest.` |
| **Tree-integrity guard** | After every edit batch in long runs | `After each batch: no 0-byte source file; no git diff --numstat row with deletions and zero additions. Edit source with Edit/Write, never with shell regex.` |
| **Explicit tool allow-list** | Read-only assessments | `You may ONLY Read/Glob/Grep, run read-only git, <run these gates under this condition: …>, <use the contract-mandated tools: …>, and at the very end WRITE ONE markdown file: <path> (or: report in chat only). The gates' side effects (<build output, caches, test DB>) are the only other permitted writes.` |
| **Reading manifest with depth** | A large `docs/` | `READ FULLY: <…>  SKIM: <…>  CONTEXT ONLY: <…>` |
| **Deliverable TOC with an ID scheme** | Planning outputs | `Stable ids (<scheme>). No item may say "improve X" without naming files.` |
| **Commit-staging manifest** | Commit prompts | `Commit <n>: paths <…> · subject "<…>" · body must record <…> · must NOT include <…>` |
| **Write it up as method** | A finding generalises | `Record the rule in <methodology doc>. Propose, do not edit, the conventions contract.` |
| **STANDING RULES** | Long runs that cross context windows | `STANDING RULES (re-read at every part boundary): 1. <rule and its reason> 2. …` |
| **STEP 0 dependency check** | The prompt needs a prior artifact | `STEP 0: confirm <artifact> exists at <path>. If it does NOT, STOP immediately and report. Do nothing else.` |

### 4.21 Shape and length budget

- **Three zones in the archive file:** preamble (grounding, interpretations) · **exactly one
  fenced block**, which is the whole prompt · footers (self-check, caveats, the transferable rule).
- **Banner-delimited ALL-CAPS parts:** `PART A…F` / `STEP 1…4` / `CHECKPOINT A…C`, under `═`
  rules.
- **Canonical order inside the block:**
  1. anchor, role, contract precedence
  2. mode/autonomy
  3. verification (hoisted early for unattended runs) and environment facts
  4. verify-at-start (§4.22)
  5. source of truth
  6. skepticism, or the central problem
  7. parts: goal, defect, decisions, build list, traps, gate, commit
  8. WHAT YOU CANNOT DO
  9. standing rules
  10. DO/DON'T
  11. definition of done
  12. report spec
  13. terminal imperative
- **Length budget: a hard cap, counted in lines inside the block.** Keep lines at or under 100
  characters; a longer line counts as `ceil(length / 100)` lines. The archetype file names its
  tier. `--brief` means about 60% of the cap.
  - A **measured-large scope** may use up to +20%: a review of more than 3 commits or 50 files, or
    a plan or roadmap of more than 20 items. Row 21 of the self-check names the measure.
  - Any other overrun needs a one-line reason in the self-check.

| Tier | Cap | Archetypes |
|---|---|---|
| Delta | 120 | E, J (a mid-session ruling or continuation that inherits a running prompt's constraints) |
| Focused | 200 | A, B, C, H, K, L, M, O, P, U, V, W |
| Slice | 260 | D (320 for a multi-checkpoint slice) |
| Program | 350 | F, G, I, N, Q, R, S, T |

- **Compression pass, before archiving:**
  - cut context the worker already holds
  - replace restated contract rules with a one-line pointer to the contract
  - drop praise and narrative closings
  - merge repeated DO/DON'T lines
  - keep every gate, file:line and stop-list item

### 4.22 Verify-at-start (volatile facts)

```text
VERIFY BEFORE STARTING. These were true when this prompt was written (<date/time>) and may not be now:
- <fact>: check with `<read-only command>`, expect `<value>`.
- <fact that is EXPECTED to drift>: check with `<command>`, expect `<value>`; if it differs, <what to
  do instead>. This is not a stop.
If any other entry differs, STOP and report the difference. Do not adapt silently.
```

Use it for SHAs the prompt builds on, quotas, counts that change daily, and whether a remote or
service is reachable. **Never assert such a fact bare.**

### 4.23 Approval per action (release, deploy, destructive and outward-facing work)

```text
APPROVAL PER ACTION. Each action below needs my explicit "yes" in this chat AT THE MOMENT you are
about to run it. Approval for one is not approval for the next, and not approval for a re-run:
- <deploy / publish / push / migrate on non-local / DNS / credentials / store submission>
Prepare everything up to the action, show me the exact command and what it will change, then wait.
```

### 4.24 Measurement protocol (perf, tests, coverage)

```text
MEASURE FIRST. Before changing anything, record the baseline with the exact command and environment:
| Metric | Command | Baseline | After | Delta |
No optimisation or claim without a before/after row. Run each measurement <n> times and report the
median. Name the machine and build mode.
```

### 4.25 Findings register (review, security, audit)

```text
Findings: one row each, ranked by severity:
| ID | Severity (critical/high/medium/low/info) | file:line<@sha> | <Commit> | Evidence (quoted) | Repro | Recommendation | FIX-NOW or RECORD |
Rules: every finding has evidence at file:line. There are no speculative findings. A false positive
you checked and retired goes in a FALSE POSITIVES table with its evidence.
```

For a multi-commit review, cite lines **at the range head** (`file:line@<sha>`) and add the Commit
column. For a single state, drop both.

### 4.26 Closeout note (no prompt emitted)

Printed in chat when the verified state shows nothing left to emit, or the work is parked:

```text
CLOSEOUT <repo> <date>
Verified: <what was re-read and how>. State: <SHAs, counts, tree>.
Nothing emitted because: <reason>.
Open for the user: <decisions/content/credentials only you can supply, ranked by what each unblocks>.
Coverage: <what was checked>. Not checked: <what was not>. (Never "there is nothing left".)
```

Archive it as a status row (§10), with no prompt file.

### 4.27 Occupied tree (another session is working in the repo)

Use this when PROTOCOL Step 4's occupancy check fires: recently modified dirty or untracked files,
files matching the latest prompt's plan, or a running MODE/roadmap prompt with no closeout.

```text
OCCUPIED TREE. Another session is working in this repository right now (<evidence>). Its work is
out of scope: do not touch it, stage it, stash it or review it.
- Read COMMITTED content by SHA, never the working tree, for any file under review:
  `git show {sha}:{path}`, `git grep -n {pattern} {sha} -- {path}`, `git diff {base} {head} -- {path}`.
- Run gates ONLY if the tree is clean and HEAD is <sha>. Otherwise write "not run: <reason>".
  Never run a suite that shares <test database> with the live session.
- Write no new file into the repo while it is occupied. Report in chat (or in the doc path I name
  outside the repo).
- Drift in docs that the live session's plan owns is RECORD, not FIX-NOW.
- In any hand-off, flag items that touch a file the live session has dirty.
- The final `git status` may differ from the start ONLY in the live session's paths; list any other
  difference.
```

It pairs with §4.22 verify-at-start: HEAD moving and the dirty count growing are **expected drift**
in an occupied tree, not a stop.
