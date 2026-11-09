# 1.4.0 item 5: the judge's reasoning without a separate `--explain` call (investigation, no spend)

| | |
|---|---|
| Question | Can `claude plugin eval` record why the opus judge voted PASS or FAIL, so a gated FAIL or a split doesn't need the separate `--explain` call? |
| Answer | **Not with the current harness.** It offers no documented or observed way to get the judge's reasoning. The only route is a rubric change. That route is unproven, and it would make verdicts incomparable with the CP7 re-baselines. |
| Recommendation | Keep `--explain` as the source of reasoning; optionally (opt. 5) run it automatically on a gated FAIL or split. Ask for the feature (opt. 6). Don't change any gated rubric text without a ruling and a re-baseline. |

## What the harness gives today

- **Observed in CP7** (`evals/results/2026-11-09T20-41-44Z/aggregate.json`). An `llm` grader result
  holds `name`, `passed`, `weight`, `explanation`, `withOnly`, `scored`, `judgeVotes` and `evidence`.
  - `explanation` is only `"judge votes: PASS PASS PASS"`.
  - `judgeVotes` is `[true, true, true]`.
  - `evidence` is the text that was graded (the generator's last message), not the judge's reply.
- **Debug log** (`--debug-file` with `--verbose`, J5 in CP7): only
  `[API REQUEST] /v1/messages … source=plugin_eval_judge` request ids, with no request or reply text.
- **Docs** ([Test plugins with evals](https://code.claude.com/docs/en/plugin-evals.md)):
  - The HTML report shows "the judge's votes and the evidence it was shown".
  - The JSON holds "per-run grader results with explanations and evidence".
  - The verdict rule is "PASS on the rubric in at least two of three votes".
  - The docs name **no** frontmatter key, flag, environment variable or output field for the judge's
    rationale.
  - The documented `llm` grader keys are `type`, `weight`, `arm`, `criteria` and `focus`, and an unknown
    key in prompt.md is an error.
  - The reply format the harness parses is not documented.

## Options

| # | Option | Possible? | Effect on verdict comparability |
|---|---|---|---|
| 1 | **An eval flag** (`--verbose`, `--report`, `--json`) | **No.** None stores the judge's reply; checked in CP7 and the docs. | None. |
| 2 | **A grader key** such as `explain:` or `reasoning:` | **No.** It isn't a documented key, and unknown keys are rejected in prompt.md; graders are likely the same. | None. |
| 3 | **A rubric change**: append "after your verdict, give a one-line reason" to the grader body | **Unproven, and probably useless.** The parsed reply format is undocumented, so an extra line could change how the verdict is parsed. Even if it parses, nothing shows the reply is *stored*: `explanation` is synthesised from the votes, and `evidence` is the input. | **Breaks comparability.** The judge's prompt changes, so the grader is new. J4's regressions are defined against the re-baselined v1.3.0 and v1.2.0, graded with the *old* text, so every gated case would need re-baselining (about $4.6 at CP7 actuals). The reason line could also shift votes, because asking for a rationale is known to move LLM judgments. **Not to be done on a gated grader without a ruling.** |
| 3b | Option 3 trialled on the **non-gated** `rubric-skepticism` only | Possible as an experiment, about $0.25–0.30 for one opus-judged case. | It would show whether a reason appears anywhere in the JSON or HTML, without touching a gated verdict. skepticism isn't in R4 or J4, so its comparability doesn't gate. **Needs Shoaib's OK (spend).** |
| 4 | **Read the reasoning off the harness JSON** in another field | **No.** `aggregate.json` and `structural.json` have no such field (CP7 runs). | None. |
| 5 | **Fold `--explain` into the run**: evals/run.py calls it automatically for a gated FAIL or split under its own `--explain-max-total` cap (today it's a separate opt-in flag) | **Yes, offline** (code only). | **None.** `--explain` never changes a verdict (J5). It's still a separate model call, at about $0.15–0.45 per explained grader, but no separate step. |
| 6 | **Feature request** (`/feedback`): store each judge vote's rationale in the grader result | Yes. | None until it ships. Then the reasoning would come for free, with the rubric text unchanged. |

## Recommendation

- **No-spend default:** option 5 (auto-explain on a gated FAIL or split, capped), plus option 6.
  Verdicts stay exactly comparable, because no rubric text changes.
- **If Shoaib wants evidence for option 3:** run option 3b on `rubric-skepticism` alone, one case, about
  $0.30.
  - If no reason shows up in the output, option 3 is dead.
  - If it does show up, a gated rollout still needs a ruling and a full re-baseline. Comparisons
    across the rubric change are invalid.
- Nothing in this item changes a grader. `evals/build_cases.py` and the generated `graders/*.md` are
  untouched.
