# CP5: the 1.2.0 candidate (483d021)

| | |
|---|---|
| Candidate | local main `483d021` = E-09a/b/c + E-10 + E-11a/b + E-16 + E-18a + evals |
| Quality baseline | the stored Phase-1 run at `758e59e` (structural graders v3). commit-finished is compared against its CP4 run at `4fb361a` (`--extra-baseline`) |
| Load baseline | v1.1.0 `fb4db7b` (pre-E-09), real use via `realuse/run.py compare` |
| Run | 2026-11-08, claude-opus-5-5, 1 run per case, `--ablation none`, Read/Glob/Grep only. Eval ceiling $8 |
| archive-valid doctor | `tools/doctor.py` from the staged `483d021` worktree (`--doctor`), so Worker B's E-18b edits could not change the grader mid-run |
| Cost | eval 7 cases $3.9786 + slice-monorepo $0.6371 + control $0.0042 + load probe $0.2313 = **$4.8512** |

**Drift since 758e59e:** E-04a/b, E-05, E-07/E-08 follow-ups (E-08b), E-09a/b/c, E-10, E-11a/b,
E-16, E-17, E-18a and E-19. Most of the archive-side changes (E-04b, E-05) are muted under
`--dry-run` and the no-Bash sandbox.

## Verdict

| Gate | Result |
|---|---|
| G1 no deterministic grader PASS→FAIL (eval) | **PASS** |
| G2 cites-real + gates-exist hold (eval) | **PASS** |
| Control: every exercised grader fails | **PASS** |
| A1 no Read of an @-included file, PROTOCOL.md or 03-blocks (real use) | **PASS** |
| A2 first-turn context larger (the @-includes land) | **PASS** |
| A3 rule bytes lower in every case | **FAIL**: slice −23.7%, fix −12.4%, redesign +55.0%, plan +152.5% |
| A4 median rule-byte drop ≥ 25% | **FAIL**: median **−21.3%** (CP4b, E-09 alone: −26.5%) |
| A5 isolation | **FAIL**: see below. No file content leaked, but names outside the work dir were listed |

G3 and G4 from compare.py do not apply in the eval harness, which does not expand @-includes
(CP4.md). For the record, G3 measured a median of −1.3% and G4 listed the expected Reads. The
token gates come from the real-use probe. Per the instructions, nothing was re-run after a gate
failed.

## Quality (plugin eval)

| Case | eval score (758e59e → cand) | structural (v3) | rubrics: grounding / scope / skepticism | line-length |
|---|---|---|---|---|
| slice | 1.0 → 1.0 | 10/11 | PPP / PPF / PPP | FAIL: 3 lines of 101–104 chars |
| fix | 0.9 → 0.9 | **11/11** | PPP / **FPF** / PPP | PASS |
| redesign | 0.9 → **1.0** | 10/11 | PPP / **PPP** / PPP | FAIL: 3 lines of 101–102 |
| next-hybrid | 1.0 → 1.0 | **11/11** | PFP / PPP / PPP | PASS |
| commit (refusal case) | 0.7 → **1.0** | 3/11 → 10/11 | PPP / PPP / PPP | FAIL: 1 line of 102 |
| plan | 0.9 → 1.0 | 10/11 | PPP / PPP / PPP | FAIL: 1 line of 103 |
| commit-finished (vs 4fb361a) | 1.0 → 1.0 | 10/11 | PPP / PPP / PPP | FAIL: 2 lines of 106–107 |

- **line-length:** E-10's wrap rule removed the long lines. The worst line was 177–209 characters
  in CP4; it is now at most 107. Two cases pass outright, and the rest have 1–3 lines over by 1–7
  characters. doctor counts these as a WARN; the stricter structural grader still says FAIL.
- **rubric-scope:** redesign now passes. fix still fails, 2 of 3 votes (FPF), the same as at CP4.
- **The verdict line appears in its exact form in all 7 cases:**
  `Self-check: <n> PASS · <n> N/A · <n> FAIL (full table: --verbose)`.
- **doctor false positive (for E-18b):** doctor's `verdict-line` check WARNs in 6 of 7 cases, for
  example "the verdict counts add up to 23, but the self-check table has 4 rows". Under E-08, chat
  prints only the FAIL and N/A rows, so the shown table is never the full one. The check should
  compare the counts with the checklist's row count when the table is partial.

### slice-monorepo (extra: reported, not gated)

Eval score 0.917, structural 10/12. Every monorepo grader passed:
- **lock-monorepo** PASS: the lock says "npm-workspaces monorepo: packages/ledger-core IN ·
  packages/ledger-web OUT (CLAUDE.md:6-7)".
- **lock-sibling-out** PASS.
- **gates-scoped** PASS: `npm run test -w ledger-core` and `npm run lint -w ledger-core`, each
  labelled (script).

What failed:
- **cites-real** fails on package-relative citations such as `test/money.test.js:6`, which means
  `packages/ledger-core/test/money.test.js`. **rubric-grounding** failed 0 of 3, probably for the
  same reason.
- This is a **grader gap, not a generator error**. In a monorepo, citing relative to the in-scope
  package is reasonable. Follow-up: cites-real should also resolve paths relative to `package`, and
  the monorepo rubric should say that package-relative paths count.
- line-length fails on 5 lines of 101–104 characters.

## Load (real use, haiku, v1.1.0 → 483d021)

| Case | first-turn ctx | @-included bytes | rule Reads, base → cand (bytes) | rule bytes (Δ) |
|---|---|---|---|---|
| slice | 21,963 → 26,356 | 24,485 → 34,002 | 03-blocks 22,542 + 04-checklist 6,008 + stack-matrix 9,859 → 04-checklist 6,104 + **06-library 7,868** | 62,894 → 47,974 (−23.7%) |
| fix | 22,169 → 27,582 | 25,011 → 37,324 | stack-matrix 9,859 + 03-blocks 22,542 + 01-target-profile 17,801 + 04-checklist 6,008 → **06-library 7,868** + 04-checklist 6,104 + **stack-matrix 19,882** | 81,221 → 71,178 (−12.4%) |
| redesign | 22,123 → 25,910 | 24,931 → 33,163 | 03-blocks 22,542 + 04-checklist 6,008 → **01-target-profile 20,854 + stack-matrix 19,882** + 04-checklist 6,104 + 06-library 2,877 | 53,481 → 82,880 (+55.0%) |
| plan | 22,069 → 26,769 | 24,607 → 35,216 | none → 04-checklist 6,104 + **stack-matrix 19,882** + 01-target-profile 922 | 24,607 → 62,124 (+152.5%) |

Cost per case, base → cand: slice $0.0337 → $0.0254, fix $0.0311 → $0.0309, redesign $0.0217 →
$0.0371, plan $0.0129 → $0.0385.

**Attribution (per-file Read bytes):**
- **E-09a still works.** The candidate never Read `guide/03-blocks.md`, which saves 22.5 KB in
  every case where the base read it.
- **E-16 doubled `stacks/stack-matrix.md`** (9,431 → 18,986 bytes), and **E-09c's pointers send
  the generator there.** The candidate Read it, at about 19.9 KB, in fix, redesign and plan. This
  is the largest single addition.
- **E-11b moved archive detail out of PROTOCOL into `guide/06-library.md`** (6,044 → 7,384 bytes)
  behind a "Read only when" pointer. The candidate Read it in slice, fix and redesign even under
  `--dry-run`, where nothing is archived.
- **`guide/01-target-profile.md` grew** (16,693 → 19,586 bytes, E-11a/b). It was Read in full in
  redesign.
- **The @-included load grew by 9.5–12.3 KB per command** (the E-09a excerpts plus E-10 text).
  That is expected; it is paid back only when the on-demand Reads shrink.
- **Noise:** this is haiku with one run per cell, and the turns varied from 15 to 42. Plan's
  +152% is inflated, because the base run read no rules files at all. Even so, the per-file
  pattern is consistent: stack-matrix and 06-library are the new costs.

**Options (for the PE and the Planner):**
1. Narrow E-09c's stack-matrix pointer to the workspace section only, with "Read only when the
   repo has more than one manifest directory", or split section 1b into its own file. Single-repo
   cases would then never load the monorepo text.
2. Make the 06-library pointer conditional on not `--dry-run` (it is the archive spec).
3. Re-run only the load probe after that (about $0.25). The quality side passed.

## Isolation (A5): what failed

- **Ancestor scan:** the fixture sits in `C:/tmp/genprompt-probe-…/fixture`, so the protocol's
  ancestor scan checked `C:/tmp/CLAUDE.md`, `C:/CLAUDE.md` and the like. Those Reads returned
  "File does not exist". A5 counts any result other than a denial, so it flagged them. These are
  existence checks the protocol requires, and no content was involved.
- **Recursive Globs:** two candidate runs (fix and redesign) ran a recursive Glob from `C:/tmp`
  and **listed the names of other projects' `CLAUDE.md` files under `C:/tmp`**. No content was
  read. The protocol asks for the four names in each ancestor directory, not a recursive search,
  so this is generator over-reach that the sandbox does not stop. `dontAsk` confines Read, but not
  Glob, to the working directories.
- **Follow-ups:**
  - A5 should treat "File does not exist" as a non-leak.
  - The probe's work root should not share a parent with other projects, for example
    `C:/genprompt-probe/<ts>`, with Glob and Grep denied on `C:/tmp/**` and the home directory.
  - Or the protocol could state the ancestor check as non-recursive.
- The real `~/.genprompt` and the home directory stayed sealed: every call there was denied.
