"""The chat-side self-check verdict line (PROTOCOL Step 6 item 3), checked by doctor's lint.

It is a WARN, and it only runs where a verdict-like line exists: archived files that hold only the
full table must never trigger it. Synthetic text only, built from the lint pass fixture.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import FIXTURES, ROOT, run_tool  # noqa: E402

DOCTOR = ROOT / "tools" / "doctor.py"
PASS_FILE = FIXTURES / "lint" / "2026-10-07-slice-s02-lint-pass.md"
BASE = PASS_FILE.read_text(encoding="utf-8")
EXACT = "Self-check: 1 PASS · 0 N/A · 0 FAIL (full table in the archive file)"


def load_doctor():
    spec = importlib.util.spec_from_file_location("doctor_verdict_under_test", DOCTOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DOC = load_doctor()


def emission(verdict: str, text: str = BASE) -> str:
    """The verdict line printed after the fenced prompt, as in chat."""
    return text.replace("````\n\n| # | Item |", f"````\n\n{verdict}\n\n| # | Item |", 1)


def verdict(text: str):
    res = {c: (s, d) for c, s, d in DOC.lint_prompt(text, PASS_FILE.name, DOC.cmd_map())}
    return res.get("verdict-line")


class VerdictLine(unittest.TestCase):
    def test_table_only_file_never_runs_the_check(self):
        self.assertIsNone(verdict(BASE))

    def test_exact_line_with_matching_counts_passes(self):
        status, detail = verdict(emission(EXACT))
        self.assertEqual(status, "PASS", detail)
        self.assertIn("counts match the 1-row table", detail)

    def test_dry_run_variant_passes(self):
        line = "Self-check: 1 PASS · 0 N/A · 0 FAIL (full table: --verbose)"
        self.assertEqual(verdict(emission(line))[0], "PASS")

    def test_exact_line_without_a_table_must_cover_every_checklist_row(self):
        n = DOC.checklist_rows()
        self.assertGreaterEqual(n, 22)
        good = f"Self-check: {n - 3} PASS · 3 N/A · 0 FAIL (full table in the archive file)"
        text = emission(good).split("| # | Item |")[0]          # chat form: verdict line, no table
        status, detail = verdict(text)
        self.assertEqual(status, "PASS", detail)
        self.assertIn(f"cover the {n} checklist rows", detail)

    def test_counts_short_of_the_checklist_warn_without_a_table(self):
        n = DOC.checklist_rows()
        short = f"Self-check: {n - 5} PASS · 3 N/A · 0 FAIL (full table: --verbose)"
        status, detail = verdict(emission(short).split("| # | Item |")[0])
        self.assertEqual(status, "WARN")
        self.assertIn(f"the §6 checklist has {n} rows", detail)

    def test_trailing_period_warns(self):
        self.assertEqual(verdict(emission(EXACT + "."))[0], "WARN")

    def test_counts_that_do_not_add_up_warn(self):
        status, detail = verdict(emission("Self-check: 20 PASS · 2 N/A · 0 FAIL (full table in the archive file)"))
        self.assertEqual(status, "WARN")
        self.assertIn("add up to 22, but the self-check table has 1 rows", detail)

    def test_paraphrase_warns_and_cites_the_rule(self):
        status, detail = verdict(emission("12 passed, 3 marked N/A, 0 failed."))
        self.assertEqual(status, "WARN")
        self.assertIn("PROTOCOL Step 6 item 3", detail)

    def test_reworded_self_check_line_warns(self):
        self.assertEqual(verdict(emission("Self-check passed (22 rows)."))[0], "WARN")

    def test_decorated_exact_line_warns(self):
        self.assertEqual(verdict(emission(f"**{EXACT}**"))[0], "WARN")

    def test_test_results_in_grounding_are_not_a_verdict(self):
        text = BASE.replace("Grounding:", "Grounding: the suite reported 516 passed, 2 failed (flaky).", 1)
        self.assertIsNone(verdict(text))

    def test_text_inside_the_prompt_block_is_ignored(self):
        text = BASE.replace("REPORT: start with", "REPORT: give the self-check counts (3 lines), then start with", 1)
        self.assertIsNone(verdict(text))

    def test_cli_warns_but_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / PASS_FILE.name
            f.write_text(emission("12 passed, 3 marked N/A, 0 failed."), encoding="utf-8")
            code, out = run_tool(DOCTOR, "--prompt", str(f))
        self.assertEqual(code, 0, out)
        self.assertIn("WARN  verdict-line", out)


if __name__ == "__main__":
    unittest.main()
