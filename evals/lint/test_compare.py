"""compare.py: --extra-baseline compares a case against its own baseline run.

    python -m unittest discover -s evals/lint
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import compare  # noqa: E402


def row(case: str, archive: str = "PASS", cites: str = "PASS") -> dict:
    return {"case": case, "control": False, "grader_version": 3, "eval_score": 1,
            "eval_cost_usd": 0.5, "usage": {},
            "eval_graders": [{"name": "lock-present", "passed": True}],
            "structural": [{"name": "archive-valid", "status": archive, "detail": "x"},
                           {"name": "cites-real", "status": cites, "detail": "x"}]}


def results(root: Path, name: str, rows: list[dict]) -> Path:
    d = root / name
    for r in rows:
        (d / r["case"] / "run1").mkdir(parents=True)
        (d / r["case"] / "run1" / "trace.jsonl").write_text("", encoding="utf-8")
    (d / "structural.json").write_text(json.dumps(rows), encoding="utf-8")
    return d


class ExtraBaseline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.base = results(root, "base", [row("slice")])
        self.extra = results(root, "cp4extra", [row("commit-finished")])
        self.cand = results(root, "cand", [row("slice"), row("commit-finished", archive="FAIL",
                                                             cites="FAIL"),
                                           row("slice-monorepo")])

    def tearDown(self):
        self.tmp.cleanup()

    def gates(self, extra):
        _, notes, gates = compare.compare(self.base, "HEAD", self.cand, "HEAD", extra)
        return notes, {name[:2]: (ok, detail) for name, ok, detail in gates}

    def test_without_extra_the_case_is_reported_not_gated(self):
        notes, g = self.gates({})
        self.assertTrue(g["G1"][0])
        self.assertTrue(any(n.startswith("commit-finished: no baseline") for n in notes))

    def test_extra_baseline_gates_the_case(self):
        notes, g = self.gates({"commit-finished": (self.extra, "HEAD")})
        self.assertFalse(g["G1"][0])
        self.assertIn("commit-finished: structural:archive-valid", g["G1"][1])
        self.assertFalse(g["G2"][0])  # cites-real went PASS -> FAIL
        self.assertTrue(any("--extra-baseline" in n for n in notes))

    def test_extra_case_stays_out_of_the_g3_median(self):
        lines, _, gates = compare.compare(self.base, "HEAD", self.cand, "HEAD",
                                          {"commit-finished": (self.extra, "HEAD")})
        self.assertEqual(sum(1 for ln in lines if ln.startswith("| commit-finished")), 1)
        g3 = next(d for n, _, d in gates if n.startswith("G3"))
        self.assertIn("median drop 0.0%", g3)  # only slice (same ref both sides) counts

    def test_extra_tagged_case_is_reported_not_gated(self):
        notes, _ = self.gates({"commit-finished": (self.extra, "HEAD")})
        self.assertTrue(any(n.startswith("slice-monorepo: no baseline") for n in notes))

    def test_parse_extra(self):
        got = compare.parse_extra(["commit-finished=evals/results/x@4fb361a"])
        self.assertEqual(got["commit-finished"], (Path("evals/results/x"), "4fb361a"))
        with self.assertRaises(SystemExit):
            compare.parse_extra(["commit-finished:evals/results/x"])

    def test_missing_case_in_extra_dir_is_an_error(self):
        with self.assertRaises(SystemExit):
            compare.compare(self.base, "HEAD", self.cand, "HEAD", {"plan": (self.extra, "HEAD")})


if __name__ == "__main__":
    unittest.main()
