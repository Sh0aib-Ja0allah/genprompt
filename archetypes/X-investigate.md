# 5.X: Investigate / root cause · `/genprompt:investigate`

| | |
|---|---|
| **Use when** | A bug has a symptom but no known cause: find the repro, trace it, name the root cause at `path:line`, and hand confirmed defects to `:fix` |
| **Not when** | The cause is already known and confirmed → `:fix`, because investigating a known defect only delays the fix. Users are affected right now → `:hotfix`, because mitigation comes before diagnosis. A broad "is this codebase healthy" question → `:audit`, because it ranks many findings against the docs, not one symptom. The bug arrived with a specific diff or PR → `:review`, because the range is already known |
| **Autonomy** | N/A: read-only, plus a scratch repro. Writes are enumerated: files under one named scratch path outside the source tree (deleted or left untracked, never committed), and at most one findings doc if the contract allows docs |
| **Baseline delta** | Unchanged: no production code or test changes. The repro's own output (failing before) goes in the report |
| **Length tier** | Focused (200) |
| **Deliverable** | The repro (command, observed vs expected), the root cause as mechanism → chain → consequence at `path:line`, the evidence that refutes the alternatives, and a hand-off list of confirmed defects in `:fix` input form, or a STOP with what is missing |

## Generator: before emitting

- Ground the symptom yourself, by reading. Find the entry point the symptom names (a CLI command,
  a route, a screen) and the code path it runs. Give the worker 2–3 hypotheses, each with the
  `file:line` that would confirm or refute it, because a guessed cause handed over as fact gets
  confirmed instead of tested.
- Name the repro you expect, as a literal command or step list from the repo's own scripts or
  examples. If none can be derived, the prompt's first step builds one in the scratch path.
- Pick the narrowing method from the evidence: "it used to work" → bisect between a known-good and
  a known-bad commit (name the known-good one if the history shows it); "only some inputs" → shrink
  the input; "only in some environments" → diff the configuration.
- Bisect never moves the user's checkout: it runs in a temporary `git worktree` under the scratch
  path and is removed at the end. In a dirty or occupied tree (§4.27), read by SHA instead.
- Set the stop conditions up front: the bug does not reproduce; reproducing it needs production
  data, credentials or a live system; the cause sits in a dependency or a service outside the repo.

## Required blocks

- §4.5, §4.6, §4.7 (the symptom report itself is the claim to falsify)
- §4.9 mechanism → chain → consequence, for the root cause
- §4.15 falsifiability: the repro fails before any change, and each hypothesis has a test that
  could refute it
- §4.13 stop-list (production data, credentials, live systems)
- §4.20 RECORD, DO NOT ACT (suspicious code that is not the cause) and STEP 0 (the repro exists)
- §4.25 findings register, for the hand-off
- §4.14 verification and report

## Template

```text
Repo: <PROFILE.path> (branch <PROFILE.branch><, scope <root>>)
[INSERT §4.5 contract precedence]

TASK: find the root cause of this symptom. Do not fix it: the fix is a separate :fix prompt.
SYMPTOM: <what happens> · EXPECTED: <what should happen> · SINCE: <when, if known> ·
  WHERE: <entry point: command / route / screen>

AUTONOMY: read-only on the source tree. You may write only under <scratch path> (a repro script,
  inputs, a bisect worktree), never commit it, and remove the worktree at the end.
[INSERT §4.15 falsifiability standard]

STEP 1: REPRO. Reproduce it with <literal command or steps>. Record the exact output, observed vs
  expected. If it does not reproduce, STOP and report what you tried (see WHAT YOU CANNOT DO).
STEP 2: NARROW by <bisect between <good sha> and <bad sha> in a temporary worktree | input
  shrinking | config diff>. Record each step.
STEP 3: TRACE from <entry point file:line> to the faulty code. Test each hypothesis:
  - H1 <hypothesis> (<file:line>): confirmed or refuted, with the evidence
  - H2 <hypothesis> (<file:line>): confirmed or refuted, with the evidence
STEP 4: ROOT CAUSE: [INSERT §4.9 mechanism → chain → consequence], at path:line, plus why the
  existing tests did not catch it.
STEP 5: HAND-OFF: each confirmed defect in :fix input form: MECHANISM (file:line), CONSEQUENCE,
  REPRO, a suggested ACCEPTANCE assertion. Suspicious code that is not the cause goes under
  [INSERT §4.20 RECORD, DO NOT ACT], in a §4.25 findings register.

OUT OF SCOPE: do not start these, do not drift into them:
- fixing the defect, or editing any file under <source and test roots>, because the fix is the
  next prompt and needs its own gates
- <roadmap items by ID>, because they are separate slices
[INSERT §4.13 WHAT YOU CANNOT DO: production data or logs, credentials, live systems; a cause
  outside the repo (dependency, external service): stop and name it]
[INSERT §4.14: literal gates, each labelled (script|contract|derived), run read-only to record
 the baseline; REPORT starting with the GENPROMPT-REPORT line]
Start with STEP 1 now.
```

## Traps

- The symptom is not the defect. The first line that looks wrong is often a downstream effect;
  the trace has to reach the first point where state diverges from what the code intends.
- A green suite proves nothing here, because the bug exists exactly where the tests miss it. Name
  the test that should have failed.
- Bisecting in the user's checkout leaves HEAD detached if the worker stops mid-way, which is why
  bisect runs in a temporary worktree.
