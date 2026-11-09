# J-method: how R4 and R3 judge quality from 1.3.1 on (design, nothing run)

| | |
|---|---|
| Status | Proposal for Shoaib. No spend. Rule changes apply only after his OK and before any results |
| Why | CP6 showed the quality gate swinging on the judge, not the prompt. The judge is `claude plugin eval`'s default **haiku**, with 3 votes per rubric and no stored reasoning. Redesign's grounding votes ran PPP (CP5), PPP (CP6a-2), FPF (run 6), FFP (run 7). A hand check of run 7 found every citation and claim correct, yet it is recorded as an R4 FAIL. Earlier fails did have real causes (`tools/archive.py`, a dropped §4.13), so the method has to keep catching those |
| Baselines | v1.2.0 = CP5's quality run (`2026-11-08T19-07-58Z`, candidate 483d021). v1.3.0 = `502a723`; its outputs are CP6 runs 5–7 (`…14-08-53Z` fix, `…14-34-55Z` plan, `…15-08-23Z` redesign, `…15-23-02Z` slice, `…15-27-13Z` investigate), whose include sets are md5-identical to 502a723's |

## 1. The options

Cost basis is CP6's actual opus generator runs:

| Case | generator cost |
|---|---|
| fix | $0.43 |
| plan | $0.47 |
| redesign | $0.48–0.56 |
| slice | $0.76 |
| investigate | $0.45 |
| **one pass of all 5** | **about $2.62** |
| one pass of v1.2.0's 4 cases (no investigate) | about $2.35 (CP5's $0.53, $0.51, $0.57, $0.77) |

The haiku judge costs about $0.006–0.010 per case (9 votes), and an opus judge about 5× that,
about $0.05 per case. Judge cost is noise next to generation.

| Option | What changes | Fixes | CP7 (5 cases) | Re-baseline v1.3.0 + v1.2.0 | Total |
|---|---|---|---|---|---|
| **A. opus judge** | `--judge-model claude-opus-5-5` (`evals/run.py` passes it through), 1 generation per case, 3 votes | judge noise | ≈ $2.9 | ≈ $2.9 + $2.6 = $5.5 | **≈ $8.4** |
| B. n-sample, haiku | 3 generations per case, majority of the 3 per-run verdicts | generator variance; judge noise only partly | ≈ $7.9 | ≈ $15.0 | ≈ $22.9 |
| C. opus + n-sample | both | both | ≈ $8.6 | ≈ $16.3 | ≈ $24.9 |
| **D. opus + escalate on fail** (recommended) | A, and a case that fails a gated grader gets 2 more generations; its verdict per grader is the majority of 3 runs. The baseline follows the same rule | judge noise; generator variance where it matters | ≈ $2.9 + about $1.0 per failing case | ≈ $5.5 + about $1.0 per failing baseline case | **≈ $8.4–10.4** (1 escalation each side expected) |

- **Re-baselining is required for A, C and D.** Today's baselines were judged by haiku, and R4
  must compare like with like (CP6's J1 check). So v1.2.0 (tag, 4 cases) and v1.3.0 (502a723,
  5 cases) each get one fresh run under the new judge, with no reuse of haiku verdicts.
  investigate has no v1.2.0 case, so R3 (absolute) stays its gate.
- **Re-grading stored outputs would be cheaper, but the harness can't do it.** `claude plugin
  eval` has no judge-only mode. A replica judge (`claude -p` with the rubric plus the stored
  final message) isn't the harness's judge, so verdicts from it can't be mixed with harness
  verdicts in one gate. A replica would only be cheaper if *every* side, baseline and candidate,
  were judged by the replica. That's possible but untested (see §2).
- Why not B alone: haiku's variance stays in each per-run verdict, and it triples the cost.

## 2. Storing the judge's reasoning

| Way | Cost | Status |
|---|---|---|
| 1. `claude plugin eval --verbose --debug-file <path>` | free on any real run | **Untested** whether the judge's text is logged. Add it to CP7's first case and check; if it is, keep the file next to the results |
| 2. Replica "explain" call: `evals/run.py --explain <results>` re-asks the judge model (via `claude -p`, rubric plus the stored final message) for a verdict and a one-paragraph reason, **only for gated graders that FAILED or split** | opus: about $0.05–0.15 per vote through `claude -p` (the CLI's system prompt dominates), so about $0.15–0.45 per explained grader (3 votes) | An explanation, not a verdict: the gate stays on the harness votes |
| 3. Harness change (store `judgeReasoning` in aggregate.json) | — | Not ours (Claude Code). Worth a feature request |

**Recommendation:** 1 always (free), and 2 when 1 doesn't capture the reasoning. In CP6 that
would have named the `tools/archive.py` trigger directly and settled redesign run 7.

## 3. Recommendation: option D

1. Offline (no spend): `evals/run.py --judge-model <m>`, which passes the flag through and
   records the judge model in structural.json. Add `--debug-file` per case. Add the escalation
   loop: on a gated FAIL, run 2 more and take the majority.
2. Write the rule into the CP7 plan before results: "R4/R3 votes are the harness's, with an
   opus judge. A gated FAIL triggers 2 more generations; per grader, the verdict is the majority
   of the 3 runs' verdicts. The baselines are re-run under the same rule."
3. Re-baseline v1.2.0 and v1.3.0 (about $5.5 plus escalations), then run CP7 (about $2.9 plus
   escalations). **Cap request: $11** (about 10% headroom over the $10.4 upper case).

## 4. G-ph: no-placeholders on worker-side slots (proposal; tests added, no grader change)

- **What happened.** Two CP6 alarms came from emitted prompts that hand the *worker* a template
  written with generator-slot notation:
  - investigate run 7 ("THE DEFECT: <file:line> <does X>. <step> (<file:line>) → …"), copied
    from §4.9's generator template;
  - CP6a-2's plan ("Stable ids (<WS letter>-<two digits>)").
- Guide §4.0 already separates the two: `<…>` means "fill from grounding before emitting; none
  may reach the user", and `{…}` is "a worker-side variable … it stays in the prompt".
- The grader already exempts `{…}`, inline code and nested fenced blocks. New tests in
  `evals/lint/test_structural.py` pin each of these, and pin that the two CP6 lines as written
  still FAIL.
- **Why not loosen the grader.** Exempting "label: <slot>" lines, or slot runs like `<a>-<b>`,
  would also pass a genuinely unfilled template ("Repo: <PROFILE.path>", or a filename pattern
  the generator forgot to fill). A test pins that case as FAIL.
- **Proposed fix, generator side (A's lane, for Shoaib):**
  - when a prompt hands the worker a fill-in line (an investigate root-cause line, an id
    format), write its slots as `{…}` or give a concrete example (`WS-01`);
  - one sentence in X's template next to the root-cause line, and F's id rule as "e.g. WS-01".
  - Floor cost about 30–60 B, against plan's 556 B margin. No gate change is needed.
