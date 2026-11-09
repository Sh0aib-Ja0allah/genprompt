# Feature request: store each LLM-judge vote's rationale in `claude plugin eval` results

To submit it, paste the text between the lines into `/feedback` in Claude Code.

---

**`claude plugin eval`: please record the judge's rationale for each `llm` grader vote**

For an `llm` grader, the result JSON (`--json`) and the HTML report give the votes and the graded
text, but not *why* the judge voted that way. Today a grader result holds `passed`,
`judgeVotes: [true, false, true]`, `explanation: "judge votes: PASS FAIL PASS"` and `evidence` (the
input that was graded). `--debug-file` with `--verbose` logs only `source=plugin_eval_judge`
request IDs, with no request or reply text. The docs list no grader key, flag or output field for
the reasoning.

**Why it matters.** We gate plugin releases on LLM rubric verdicts, with an opus judge and majority
of three. When a verdict is FAIL, or the votes split, we have to know which line of the output and
which rubric clause decided it. That tells us whether we're looking at a real defect, a rubric
ambiguity or judge variance. Right now the only way to find out is a separate `claude -p` call that
re-applies the rubric. That costs extra, isn't the same judgment the harness made, and can disagree
with it.

**What would solve it.**
1. Per vote, store the judge's short rationale, for example in
   `graders[i].judgeRationales: ["…", "…", "…"]` next to `judgeVotes`. Show it in the HTML report
   under each vote.
2. Ideally, capture it from the same judge call that produces the verdict, with no extra call and
   no change to the rubric text. A verdict-plus-reason output format that the harness owns would keep
   verdicts comparable across suites and versions. That matters to us: putting "give a reason" into
   the rubric body changes the judge's prompt, so it breaks comparison with earlier baselines.
3. If it adds cost, make it opt-in (`--judge-rationale` or a grader key), or limit it to FAIL votes
   and split votes.
4. Document the reply format the harness parses for `llm` graders, so rubric authors know what text
   is safe to include.

**Environment:** Claude Code 2.1.318 on Windows 11. `claude plugin eval` with `--judge-model
claude-opus-5-5`, `--runs 1`, `.md` graders with `type: llm`.

---
