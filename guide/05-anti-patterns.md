## 7. Anti-patterns

### 7.1 Never put these in a generated prompt (worker-facing)

- ❌ Vague tasks ("improve the app") with no file or scope anchor.
- ❌ "Create the needed pages/screens/tests" without listing the actual ones.
- ❌ Implementation before the approval gate, in attended mode.
- ❌ A whole sprint in one pass instead of reviewable vertical slices.
- ❌ "Just make it build", or any success criterion that isn't honest and numeric.
- ❌ Commits, new packages or new env vars permitted by default.
- ❌ Crossing the layer boundary (backend during a frontend slice, a sibling app in a monorepo) without a stop-and-ask.
- ❌ Large code listings in chat instead of durable docs.
- ❌ Trusting prior work because it builds.
- ❌ `git add -A` / `git add .`, especially in a monorepo. Stage by explicit path.
- ❌ A flat `.env` ban that also excludes `.env.example`, which is a committed template.
- ❌ Shell regex (`sed`, `perl -pi`, `php -r`) to edit source files. A regex edit once truncated a source file to 0 bytes, and the linter reported "no syntax errors" on the empty file. Use Edit/Write.
- ❌ A prompt with no falsifiable success criterion.
- ❌ **Gates by reference.** "Same arithmetic as last time" or "run the usual gates". Every prompt carries its literal commands.
- ❌ **Unqualified "must go up".** Commits, refactors, cleanup and docs should leave the count unchanged. State the expected delta.
- ❌ **A hardcoded attribution trailer** (`Co-Authored-By: <model>`). Tell the worker to use its own harness's attribution. A pasted trailer goes stale and differs between prompts.
- ❌ **Restating the repo's standing rules at length.** Point to the contract in one line ("`CLAUDE.md`'s deployment and branching rules are in force"). State only the deviations this prompt authorises.

### 7.2 Never do these as the generator

- ❌ **Build on an instruction whose delivery was never confirmed.** Verify it on the branch, not from the report. This is the most expensive failure on record.
- ❌ **Take the worker's gate numbers on trust, or re-run them yourself.** Re-read the artifacts (commits, diffs, test files) and label each number `verified by artifact` or `reported, not confirmed`. The generator never runs a gate.
- ❌ **Silently reinterpret the ask** ("disable" → "delete"). State interpretations as overridable.
- ❌ **Copy a gate or predicate from an adjacent field without checking they share an audience.** Two fields can look alike while one is staff-only financial data and the other is intake data a partner must type in.
- ❌ **Make a safety argument on the wrong axis.** Global scopes bound *rows*; nothing bounds *columns*. An export inherits the row boundary automatically and the column boundary not at all.
- ❌ **Accept an assertion that admits a second cause.** A test that proves concealment by asserting 404 cannot tell "concealed" from "absent". It stays green when the route is unregistered.
- ❌ **Accept a mechanism that is invoked but never configured.** A rule called at the right entrance, whose defaults were never registered, silently falls back to the framework's weaker default.
- ❌ **Treat one overturn from a reviewer you told to refute as proof.** A biased instruction produces biased findings; require an independent reproduction.
- ❌ **Let a doc and the code conceal each other.** A documented key that differs from the one the code reads means the wrong key is ignored and the missing one is silently accepted: two errors, each hiding the other.
- ❌ **Derive a false blocker from a missing tool.** Check for the binary or phar (see §11) before declaring something uninstalled.
- ❌ **Print an unfalsifiable `✓ passed`**, or bulk-pass checklist rows. That is the same unfalsifiable claim §7.1 forbids workers to make.
- ❌ **Ask for something already derivable** from the repo, the docs or the pasted report. Decide it, state it as overridable, and move on.
- ❌ **Claim finality** ("this is the last defect", "nothing left a grep can find"). State coverage and method instead. Claims like these have preceded many more prompts.
- ❌ **Assert a volatile fact bare** (a quota, a SHA the prompt builds on, a count that moves daily). Put it in §4.22 verify-at-start, with the command that re-checks it.
- ❌ **Name a file you did not find.** An ancestor `CLAUDE.md`, a helper, a doc: if you did not read it this turn, it does not go in the prompt.
- ❌ **Archive a stub.** An archive file that says "see the transcript" breaks the chain. The file holds the full prompt.
- ❌ **Leak example specifics.** Anything copied from `examples/` or from another repo's prompt (test counts, `apps/mobile`, a doc prefix) is a fabricated fact in this repo.

---
