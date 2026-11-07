"""doctor.py against fixture archives: it must pass the good case and FAIL on each known-bad case.

The fixtures live in tools/tests/fixtures/ and are reached through GENPROMPT_HOME, so the tests
never read the real ~/.genprompt archive.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import FIXTURES, ROOT, error_lines, run_tool  # noqa: E402

DOCTOR = ROOT / "tools" / "doctor.py"
GOOD = FIXTURES / "good"
BAD = FIXTURES / "bad"


class GoodArchive(unittest.TestCase):
    def test_good_archive_passes(self):
        code, out = run_tool(DOCTOR, "--archive", home=GOOD)
        self.assertEqual(error_lines(out), [], out)
        self.assertIn("Summary: 0 ERROR, 0 WARN", out)
        self.assertEqual(code, 0, out)

    def test_missing_archive_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_tool(DOCTOR, "--archive", home=Path(tmp))
        self.assertEqual(code, 0, out)
        self.assertIn("no archive yet", out)


class BadArchive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code, cls.out = run_tool(DOCTOR, "--archive", "--verbose", home=BAD)
        cls.errors = error_lines(cls.out)

    def errors_for(self, name: str) -> list[str]:
        return [ln for ln in self.errors if name in ln]

    def test_bad_archive_exits_1(self):
        self.assertEqual(self.code, 1, self.out)

    def test_legacy_rows_are_info_not_error(self):
        self.assertEqual(self.errors_for("beta"), [], self.out)
        self.assertIn("INFO   [archive] em-dash or middle dot in row: beta.tsv:4", self.out)

    def test_tab_separated_row_parses(self):
        self.assertEqual(self.errors_for("gamma"), [], self.out)

    def test_shifted_columns_are_flagged(self):
        errs = self.errors_for("delta")
        self.assertTrue(any("archetype label 's01-shifted-row'" in e for e in errs), self.out)
        self.assertTrue(any("slug 'D' is not lowercase kebab-case" in e for e in errs), self.out)

    def test_truncated_prompt_is_flagged(self):
        errs = self.errors_for("epsilon/2026-10-05-slice-s01-truncated.md")
        self.assertTrue(any("the full prompt is missing" in e for e in errs), self.out)
        self.assertTrue(any("no self-check table" in e for e in errs), self.out)


class Suite(unittest.TestCase):
    def test_suite_passes_on_this_repo(self):
        code, out = run_tool(DOCTOR, "--suite")
        self.assertEqual(error_lines(out), [], out)
        self.assertEqual(code, 0, out)

    def test_unknown_argument_exits_2(self):
        code, _out = run_tool(DOCTOR, "--nope")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
