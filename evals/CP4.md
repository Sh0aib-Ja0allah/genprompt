# CP4: E-09 (block excerpts + Step 0) against the Phase-1 baseline

| | |
|---|---|
| Candidate | `4fb361a` (enh/E-09a-excerpts, rebased on main `c3fa3ee`; contains E-09b `0d2dda8`) |
| Baseline | the stored Phase-1 run on `758e59e` (BASELINE.md), structural graders v3 |
| Run date | 2026-11-08 |
| Model and setup | claude-opus-5-5, eval CLI from Claude Code 2.1.318, 1 run per case, `--ablation none`, Read/Glob/Grep only (no Bash on Windows) |
| Grading | the same graders as the baseline. archive-valid is pinned to the doctor at `77699ec` (`--doctor`) |
| Cost | **$3.3323** for the six cases, plus $0.5814 for the extra commit-finished case. **Total $3.9137** |

**Known drift from the baseline.** Besides E-09, the candidate contains E-04a/b, E-05, E-17 and
E-19. These are mostly muted here: `--dry-run` writes no archive, and the sandbox has no Bash, so
archive.py never runs. Their PROTOCOL and shim text does differ, though.

## Acceptance (`python evals/compare.py`)

| Gate | Result |
|---|---|
| G1 no deterministic grader PASS→FAIL | **PASS** (commit's archive-valid exempt, per the Planner) |
| G2 cites-real + gates-exist hold | **PASS** |
| G3 rule bytes drop ≥25% at the median | **FAIL**: median **−8%** (bytes rose) |
| G4 no Read of PROTOCOL / an @-included archetype / 03-blocks | **FAIL**: every case Read PROTOCOL.md, its archetype and its new `guide/blocks/<X>.md` |

| Case | rule bytes base → cand (Δ) | rule Reads (cand) | cache write base → cand | cache read base → cand | output base → cand | $ base → cand |
|---|---|---|---|---|---|---|
| slice | 86,635 → 72,877 (−16%) | PROTOCOL.md, archetypes/D-slice.md, guide/blocks/D-slice.md | 48,499 → 32,341 | 163,619 → 112,060 | 12,879 → 10,874 | 0.686 → 0.507 |
| fix | 41,910 → 84,347 (+101%) | PROTOCOL.md, archetypes/L-fix.md, guide/blocks/L-fix.md, guide/04-checklist.md | 24,794 → 33,427 | 194,849 → 114,938 | 6,446 → 7,720 | 0.379 → 0.452 |
| redesign | 88,016 → 75,955 (−14%) | PROTOCOL.md, archetypes/A-redesign.md, guide/blocks/A-redesign.md, guide/04-checklist.md | 25,207 → 36,864 | 98,649 → 179,830 | 8,417 → 11,920 | 0.786 → 0.577 |
| next-hybrid | 77,698 → 77,302 (−1%) | PROTOCOL.md, archetypes/J-next.md, guide/blocks/J-next.md, guide/04-checklist.md | 42,416 → 40,796 | 175,358 → 227,556 | 13,257 → 14,798 | 0.648 → 0.675 |
| commit | 69,834 → 81,399 (+17%) | PROTOCOL.md, archetypes/H-commit.md, guide/blocks/H-commit.md, guide/04-checklist.md | 37,363 → 36,550 | 194,678 → 224,659 | 6,991 → 9,641 | 0.482 → 0.537 |
| plan | 46,729 → 80,972 (+73%) | PROTOCOL.md, archetypes/F-plan.md, guide/blocks/F-plan.md, guide/04-checklist.md | 25,757 → 38,777 | 139,938 → 221,477 | 8,147 → 10,674 | 0.404 → 0.584 |

## Why G3 and G4 fail: the eval does not expand @-includes

The failure comes from the test harness, not from E-09. Inside `claude plugin eval`, the shim's
`@${CLAUDE_PLUGIN_ROOT}/…` lines are **not** expanded:
- In every case, the generator's first message says the marker is absent. Slice's first message,
  verbatim: "The protocol files aren't actually in my context (no `GENPROMPT-PROTOCOL v3 LOADED`
  marker), so I'll read them". Step 0 at `4fb361a` tells it to Read only in exactly that
  situation, so it is following the rules.
- The first-turn context is the same size in both runs: slice 12,898 → 12,914 tokens, fix
  12,934 → 13,087, plan 12,865 → 13,018. Yet the @-included bytes grew from about 21 KB to about
  36–39 KB. If they were expanded, the candidate would start about 4,000 tokens larger. The delta
  matches only the Step 0 text change.
- The eval docs say the prompt body is sent as written, and that `@path` mentions are not
  expanded (https://code.claude.com/docs/en/plugin-evals.md).

So in this harness, the generator must Read its rules. E-09a adds one more file per command (the
excerpt), so the bytes go up. The baseline's Reads were not double loads here either; they are
double loads only in real use, where the E-09b probe showed the @-includes do expand. **CP4 cannot
measure E-09's token saving.** It can only measure quality, and on quality nothing regressed.

The fallback run (E-09b alone at `0d2dda8`) was **not** done. It exists to say which commit caused
a regression. The two gates that failed would fail for E-09b too, for the same harness reason. The
quality gates passed. Running it would spend about $3.4 and teach us nothing.

## Quality: candidate vs baseline

| Case | eval score base → cand | structural v3 base → cand | rubrics, cand (grounding / scope / skepticism votes) |
|---|---|---|---|
| slice | 1.0 → 1.0 | 10/11 → 10/11 | PPP / PPP / PPP |
| fix | 0.9 → 0.9 | 9/11 → 10/11 | PPP / FFP / PPP |
| redesign | 0.9 → **1.0** | 10/11 → 10/11 | PPP / PPP / PPP |
| next-hybrid | 1.0 → 1.0 | 10/11 → 10/11 | PFP / PPP / PPP |
| commit | 0.7 → **1.0** | 3/11 → **10/11** | PPP / PPP / PPP |
| plan | 0.9 → **1.0** | 10/11 → 10/11 | PPP / PPP / PPP |

- **commit:** the baseline refused to write a commit prompt. This time the generator wrote an
  H prompt "run as verify+commit". It names the two contradictions in the unfinished work (the
  documented `--csv` flag does not exist, and the test pins `TOTAL,,,0`) and gates the commit on
  fixing them. That is better than a bare refusal.
- **rubric-scope** now passes on redesign and plan. On fix it still fails, but no longer
  unanimously (2 of 3 judges voted FAIL; in the baseline all 3 did).
- **line-length** still fails in every case. Each prompt has one line of 177–209 characters,
  which looks like the same long line in each.
- **The fix prompt's missing GENPROMPT-REPORT line and missing gate labels are fixed:** archive-
  valid's doctor reports only line-width now.
- With one run per case, single-vote changes are noise.

## Extra case: commit-finished (not part of the baseline)

The work in this case is finished and green. Score 1.0, 10/11 structural (line-length fails),
archive-valid PASS, all rubrics PPP. Cost $0.5814, 24 turns, cache write 35,327, cache read
215,202, output 12,407.

## The real ~/.genprompt

In both runs the generator worked out the real user home and tried to Glob or Read
`~/.genprompt` there: 5 attempts in CP4 and 9 in the baseline. **The eval sandbox denied every
one** ("Permission to use Glob/Read has been denied … don't ask mode"), so nothing in the real
archive was read.

## What would measure E-09's saving

A harness that expands @-includes, such as an interactive session or a plain `claude -p
"/genprompt:slice …"` with the plugin loaded. Count the rule-file Reads and the first-turn
context there. It is not covered by `claude plugin eval` in Claude Code 2.1.318.
