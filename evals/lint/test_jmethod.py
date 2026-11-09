"""evals/run.py J-method (1.3.1, option D): judge-model pass-through, the debug log, the
escalation rule (a gated FAIL gets 2 more generations, majority of 3) and --explain targets.
No model spend: subprocess and the eval runs are stubbed.

    python -m unittest discover -s evals/lint
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

EVALS = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("evals_run", EVALS / "run.py")
er = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(er)  # a distinct name: realuse/run.py is imported as `run` elsewhere


def args(**kw):
    base = dict(case="fix", runs=1, model="claude-opus-5-5", max_cost_usd=0.77, validate=False,
                judge_model="claude-opus-5-5", no_debug=False, keep=False, escalate=True,
                escalate_max_cost_usd=1.5, tag="baseline")
    base.update(kw)
    return argparse.Namespace(**base)


def row(case="fix", run=1, fail=(), cost=0.45):
    """A post_grade row; the graders named in `fail` FAIL, every other gated grader PASSES."""
    ev = [{"name": g, "passed": g not in fail, "explanation": ""}
          for g in ("rubric-scope", "rubric-grounding", "rubric-skepticism")]
    st = [{"name": g, "status": "FAIL" if g in fail else "PASS", "detail": ""}
          for g in ("cites-real", "gates-exist", "line-length")]
    return {"case": case, "run": run, "control": False, "eval_score": 1,
            "eval_cost_usd": cost, "judge_cost_usd": 0.05, "error": None,
            "eval_graders": ev, "structural": st}


class EvalCmdTest(unittest.TestCase):
    def test_judge_model_and_debug_file(self):
        with mock.patch.object(er, "claude", return_value="claude"):
            out = Path("C:/r")
            cmd = er.eval_cmd(args(), out, "baseline")
        self.assertEqual(cmd[:3], ["claude", "--debug-file", str(out / "eval-debug.log")])
        self.assertEqual(cmd[3:5], ["plugin", "eval"])   # the global flag precedes the subcommand
        i = cmd.index("--judge-model")
        self.assertEqual(cmd[i + 1], "claude-opus-5-5")
        self.assertIn("--verbose", cmd)

    def test_validate_and_no_debug_skip_the_log(self):
        with mock.patch.object(er, "claude", return_value="claude"):
            for a in (args(validate=True), args(no_debug=True)):
                cmd = er.eval_cmd(a, Path("C:/r"), "baseline")
                self.assertNotIn("--debug-file", cmd)
                self.assertNotIn("--verbose", cmd)

    def test_default_judge_is_not_passed(self):
        with mock.patch.object(er, "claude", return_value="claude"):
            cmd = er.eval_cmd(args(judge_model=None), Path("C:/r"), "baseline")
        self.assertNotIn("--judge-model", cmd)


class MajorityTest(unittest.TestCase):
    def test_all_pass_needs_no_escalation(self):
        self.assertFalse(er.needs_escalation([row()]))

    def test_any_gated_fail_escalates_ungated_does_not(self):
        for g in er.GATED:
            self.assertTrue(er.needs_escalation([row(fail=(g,))]), g)
        self.assertFalse(er.needs_escalation([row(fail=("rubric-skepticism", "line-length"))]))

    def test_missing_gated_grader_counts_as_fail(self):
        r = row()
        r["structural"] = [g for g in r["structural"] if g["name"] != "gates-exist"]
        self.assertTrue(er.needs_escalation([r]))

    def test_majority_of_three(self):
        m = er.majority([row(fail=("rubric-grounding",)), row(), row()])
        self.assertEqual(m["rubric-grounding"], {"runs": ["FAIL", "PASS", "PASS"],
                                                 "verdict": "PASS"})
        m = er.majority([row(fail=("rubric-scope",)), row(fail=("rubric-scope",)), row()])
        self.assertEqual(m["rubric-scope"]["verdict"], "FAIL")
        self.assertEqual(m["cites-real"]["verdict"], "PASS")

    def test_single_run_majority_is_its_verdict(self):
        self.assertEqual(er.majority([row(fail=("gates-exist",))])["gates-exist"]["verdict"],
                         "FAIL")


class EscalateTest(unittest.TestCase):
    def run_escalate(self, first, more, a=None):
        a = a or args()
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(er, "run_once", return_value=(more, {})) as ro, \
                mock.patch.object(er, "claude", return_value="claude"):
            er.escalate(a, Path(d), "baseline", first, {})
            rep = json.loads((Path(d) / "escalation.json").read_text(encoding="utf-8"))
        return rep, ro

    def test_pass_is_not_escalated(self):
        rep, ro = self.run_escalate([row()], [])
        ro.assert_not_called()
        self.assertFalse(rep["cases"]["fix"]["escalated"])
        self.assertEqual(rep["cases"]["fix"]["flipped_to_pass"], [])

    def test_fail_escalates_with_two_runs_its_own_cap_and_records_flips(self):
        rep, ro = self.run_escalate([row(fail=("rubric-grounding",))],
                                    [row(run=1), row(run=2)])
        sargs = ro.call_args.args[2]
        self.assertEqual((sargs.case, sargs.runs, sargs.max_cost_usd), ("fix", 2, 1.5))
        e = rep["cases"]["fix"]
        self.assertTrue(e["escalated"])
        self.assertEqual(e["runs"]["rubric-grounding"], ["FAIL", "PASS", "PASS"])
        self.assertEqual(e["final"]["rubric-grounding"], "PASS")
        self.assertEqual(e["flipped_to_pass"], ["rubric-grounding"])   # O1: counted, reported
        self.assertAlmostEqual(rep["escalation_cost_usd"], 0.9)

    def test_x2_pass_to_fail_flip_is_recorded(self):
        # run 1 fails grounding (so it escalates) but passes scope; runs 2-3 fail scope
        rep, _ = self.run_escalate([row(fail=("rubric-grounding",))],
                                   [row(fail=("rubric-scope",)), row(fail=("rubric-scope",))])
        e = rep["cases"]["fix"]
        self.assertEqual(e["flipped_to_fail"], ["rubric-scope"])
        self.assertEqual(e["flipped_to_pass"], ["rubric-grounding"])

    def test_fail_that_holds_stays_fail(self):
        rep, _ = self.run_escalate([row(fail=("rubric-scope",))],
                                   [row(fail=("rubric-scope",)), row()])
        self.assertEqual(rep["cases"]["fix"]["final"]["rubric-scope"], "FAIL")
        self.assertEqual(rep["cases"]["fix"]["flipped_to_pass"], [])

    def test_incomplete_escalation_is_flagged(self):
        rep, _ = self.run_escalate([row(fail=("cites-real",))], [row()])
        self.assertIn("incomplete", rep["cases"]["fix"]["error"])

    def test_no_budget_left_does_not_run(self):
        rep, ro = self.run_escalate([row(fail=("cites-real",))], [],
                                    args(escalate_max_cost_usd=0))
        ro.assert_not_called()
        self.assertIn("no --escalate-max-cost-usd", rep["cases"]["fix"]["error"])
        self.assertEqual(rep["cases"]["fix"]["final"]["cites-real"], "FAIL")


class ExplainTest(unittest.TestCase):
    AGG = {"cases": [{"name": "redesign",
                      "graders": [{"name": "rubric-grounding", "graderMarkdown": "R-G"},
                                  {"name": "rubric-scope", "graderMarkdown": "R-S"},
                                  {"name": "rubric-skepticism", "graderMarkdown": "R-K"}],
                      "arms": {"with": [{"graders": [
                          {"name": "rubric-grounding", "passed": False,
                           "judgeVotes": [False, False, True]},
                          {"name": "rubric-scope", "passed": True,
                           "judgeVotes": [True, False, True]},
                          {"name": "rubric-skepticism", "passed": False,
                           "judgeVotes": [False, False, False]}]}]}}]}

    def test_targets_are_gated_llm_fails_and_splits_only(self):
        t = er.explain_targets(self.AGG)
        self.assertEqual([(c, r, g) for c, r, g, _ in t],
                         [("redesign", 1, "rubric-grounding"), ("redesign", 1, "rubric-scope")])
        self.assertEqual(t[0][3], "R-G")

    def test_unanimous_pass_is_not_explained(self):
        agg = json.loads(json.dumps(self.AGG))
        for g in agg["cases"][0]["arms"]["with"][0]["graders"]:
            g["passed"], g["judgeVotes"] = True, [True, True, True]
        self.assertEqual(er.explain_targets(agg), [])

    def test_prompt_and_command(self):
        p = er.explain_prompt("RUBRIC TEXT", "THE RESPONSE")
        self.assertIn("RUBRIC TEXT", p)
        self.assertIn("THE RESPONSE", p)
        self.assertIn('"verdict"', p)
        with mock.patch.object(er, "claude", return_value="claude"):
            cmd = er.explain_cmd("claude-opus-5-5", 0.3, p)
        self.assertEqual(cmd[cmd.index("--model") + 1], "claude-opus-5-5")
        self.assertEqual(cmd[cmd.index("--max-budget-usd") + 1], "0.30")
        for t in ("Read", "Bash", "Write"):
            self.assertIn(t, cmd[cmd.index("--disallowedTools"):])
        self.assertEqual(cmd[-1], p)

    def test_explain_respects_the_total_cap_and_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "aggregate.json").write_text(json.dumps(self.AGG), encoding="utf-8")
            (d / "redesign" / "run1").mkdir(parents=True)
            (d / "redesign" / "run1" / "final.txt").write_text("out", encoding="utf-8")
            fake = mock.Mock(stdout=json.dumps({"result": '{"verdict":"FAIL"}',
                                                "total_cost_usd": 0.2}))
            with mock.patch.object(er.subprocess, "run", return_value=fake) as sp, \
                    mock.patch.object(er, "claude", return_value="claude"):
                er.explain(d, "claude-opus-5-5", 0.3, 0.45)
            notes = json.loads((d / "explain.json").read_text(encoding="utf-8"))
        self.assertEqual(sp.call_count, 1)              # 0.2 spent + 0.3 cap > 0.45: stop
        self.assertEqual(notes[0]["answer"], '{"verdict":"FAIL"}')
        self.assertIn("skipped", notes[1]["error"])


if __name__ == "__main__":
    unittest.main()
