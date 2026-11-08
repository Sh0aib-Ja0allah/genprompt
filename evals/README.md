# genprompt evals

Evals for `claude plugin eval` (schema: https://code.claude.com/docs/en/plugin-evals.md). They
measure what the generator emits, so that later rewrites of PROTOCOL.md can be compared with a
baseline. They cost model tokens, so run them before a release, not on every push. They are not
in CI.

## Layout

| Path | What it is |
|---|---|
| `build_cases.py` | The one spec for every case. It generates `cases/` and `controls/`; `--check` reports drift |
| `cases/<name>/` | Generated. `prompt.md` (request and run limits), `case.yaml` (scaffold), `scaffold.sh`, `graders/*.md` |
| `controls/bad-emission/` | Generated negative control: the model echoes a broken prompt, and every grader must FAIL |
| `fixtures/ledgerlite/` | A made-up Node repo: real `npm test` / `npm run lint`, a `CLAUDE.md` with branching rules, and one planted defect at `src/invoice.js:14` |
| `fixtures/overlays/` | Files laid over the fixture for later states: S-02 checkpoint A (committed), then uncommitted work |
| `fixtures/scaffold-lib.sh` | Builds the fixture as a git repo in the eval's empty workspace, with fixed dates, so SHAs are stable |
| `fixtures/samples/` | A good and a bad emission. The unit tests and the control use them |
| `lint/structural.py` | The deterministic graders the eval CLI cannot express (it has no custom-code graders) |
| `run.py` | Runs the eval, then applies `lint/structural.py` to each run's final message and workspace |
| `BASELINE.md` | The Phase-1 baseline: scores per case and grader, cost, load sizes |
| `CP4.md` | CP4: E-09 at `4fb361a` vs the baseline; why the token gates cannot pass in this harness |
| `compare.py` | Applies the CP4 acceptance gates (G1-G4) to a candidate run vs the baseline |
| `prepare_worktree.py` | Stages another commit in a detached worktree with this `evals/` copied in |

Everything in `fixtures/` is invented. Nothing comes from `~/.genprompt` or any real repo.

## Cases

All six run with `--go --dry-run`, so the generator never waits and never writes the archive.

| Case | Request | Scaffold state | Length cap (block lines) |
|---|---|---|---|
| slice | `/genprompt:slice` S-02 CSV export | main, clean | 260 (320 with 2+ checkpoints) |
| fix | `/genprompt:fix` totals too low | main, clean | 200 |
| redesign | `/genprompt:redesign src/cli.js` | main, clean | 200 |
| next-hybrid | `/genprompt:next` + a pasted J+D stop-report | S-02 checkpoint A committed | 260 (see below) |
| commit | `/genprompt:commit` S-02 | checkpoint A + uncommitted work, a scratch file and `.env` | 200 |
| commit-finished (tag `extra`, not in the baseline) | `/genprompt:commit` S-02 | subtotal fix merged, checkpoint A, then S-02 finished and green (11 tests, `--csv` wired), plus a scratch file and `.env` that must stay out | 200 |
| plan | `/genprompt:plan` S-03 tax lines | main, clean | 350 |

The next-hybrid report says 10 tests pass, but the test files declare 9. The generator should
label that number "reported, not confirmed". Its cap is the D tier, not the 120-line Delta tier:
the temp home has no archived running prompt for the continuation to inherit.

## Graders

In the eval (per case, in `graders/`):

| Grader | Type | Fails when |
|---|---|---|
| lock-present | regex | no `TARGET LOCK` in the final message |
| no-generator-marker | regex, not_contains | a `[generator:` marker is left in |
| dry-run-declared | regex | no `DRY RUN` line |
| protocol-loaded | regex on the trace | the marker is not in the trace. It matches only a Read of PROTOCOL.md (the trace does not log @-include expansion), so it will fail once E-09b stops that double read; use the structural one from CP4 on |
| archetype-label | regex | the lock's Archetype line lacks the expected letter(s) |
| no-write / no-edit | tool_used, max 0 | the generator called Write or Edit |
| rubric-grounding | llm | a cited file or `path:line` does not exist, or a gate uses a missing script |
| rubric-scope | llm | scope is not bounded negatively, or the request is widened |
| rubric-skepticism | llm | no concrete falsifying artifact from the fixture |

After the eval (`lint/structural.py`, run by `run.py`):

| Grader | Fails when |
|---|---|
| lock-present | no `TARGET LOCK` |
| one-fence | not exactly one prompt block besides the lock, an unclosed fence, or a nested fence inside a 3-backtick outer fence |
| no-placeholders | a `<…>` placeholder in prose, or a `[generator:` marker |
| line-length | a line in the block is over 100 characters |
| length-cap | the block's counted lines exceed the archetype's cap (a long line counts `ceil(len/100)`) |
| gates-exist | a gate names an npm script that is not in the fixture's `package.json`, or there is no gate |
| cites-real | a `path:line` in the block names a missing file or a line past its end |
| self-check | neither the full checklist table (rows 1-22 present; more rows are fine, E-08 adds a 23rd) nor E-08's compact `Self-check: N PASS · N N/A · N FAIL` line is in chat |
| protocol-loaded | (v2) the marker is in neither the logged context nor a Read, and the emission has no protocol-shaped TARGET LOCK |
| no-writes | a write tool was called, or anything exists under the run's temp `~/.genprompt` |
| archive-valid | (v3) `python tools/doctor.py --prompt` FAILs the emission: there is no prompt block, the fence is unclosed or nests badly, or the block is a stub. Fenced lock blocks are removed first, and the text gets a synthetic line-1 header carrying the case's archetype, so doctor picks the right length tier. `header`, `filename-words`, `header-vocab` and `self-check` are reported but not graded, because `--dry-run` writes no archive record. doctor's WARNs are listed and do not fail |

Every grader has a case built to fail it: `fixtures/samples/bad-emission.md` (unit tests and the
control) and the variants in `lint/test_structural.py`. If the control ever reports a grader
passing, that grader is broken. Three graders are not exercised by the control, and each is shown
failing in the unit tests instead:
- no-edit, which is the same check as no-write
- length-cap, because the bad sample is short
- archive-valid, because doctor grades the bad sample's defects as WARN

**doctor --prompt and the text checks.** archive-valid calls doctor (E-04a) and uses doctor's
severities. The text checks in `lint/structural.py` (one-fence, line-length, no-placeholders,
length-cap) are stricter than doctor's: doctor counts a long line or an extra block as a WARN. They
stay as they are, so the Phase-1 baseline stays comparable. Merging them into doctor is a separate
decision.

## Running

```bash
python evals/build_cases.py --check          # cases match the spec
python -m unittest discover -s evals/lint    # graders fail on what they should
python evals/run.py --validate               # every case loads; no model spend
python evals/run.py --case slice             # one case, one run (smoke)
python evals/run.py                          # all six cases
python evals/run.py --controls               # negative control (cheap, haiku)
python evals/run.py --tag extra              # cases outside the baseline (commit-finished)
python evals/run.py --regrade evals/results/<timestamp>   # re-grade stored runs, no spend
```

**Evaluating another commit (CP4).** `claude plugin eval` reads its cases from
`<plugin>/evals/`, so the cases have to sit inside the tree under test. Run
`python evals/prepare_worktree.py <ref> ../genprompt-wt-cp4`. It adds a *detached* worktree of
`<ref>`, so no branch moves, and copies this `evals/` into it as untracked files. Then, from that
worktree, run `python evals/run.py --model claude-opus-5-5 --max-cost-usd 8 --doctor
../genprompt-wt-c/tools/doctor.py`. `--doctor` pins archive-valid to the same lint that graded the
baseline. Copy `evals/results/` back, then run `python evals/prepare_worktree.py --remove
../genprompt-wt-cp4`.

`run.py` passes `--scaffold` (it runs our own `scaffold.sh`), `--trust-plugin`, `--ablation none`
(a no-plugin arm says nothing useful about a prompt generator, and it doubles the cost) and
`--no-publish`. Results go to `evals/results/<timestamp>/`, which is gitignored.

## Sandbox facts (measured on this suite)

- Each run gets a temp HOME and an empty working directory under it. `~/.genprompt` inside a run
  is that temp home, so the real archive is never read or written.
- The scaffold runs with Git Bash on Windows. It gets git, node and python on PATH.
- **Bash and git.** The eval refuses to grant Bash on Windows (no shell sandbox), so the generator
  runs with Read, Glob and Grep only and cannot run `git log` or `git status`. On Linux or macOS
  you can add `--allow-tools "Bash(git *)"` to the eval command. Scores from the two setups are
  not comparable; BASELINE.md records which one it used.
- There is no offline validate flag. `--validate` uses a $0 cost ceiling, so cases load and no run
  starts.
