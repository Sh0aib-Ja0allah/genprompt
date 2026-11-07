"""Every structural grader must fail on a sample built to fail it, or it measures nothing.

    python -m unittest discover -s evals/lint
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build_cases  # noqa: E402
import structural as s  # noqa: E402

SAMPLES = HERE.parent / "fixtures" / "samples"
SCRIPTS = {"test", "lint", "start"}
FILES = build_cases.fixture_files("base")


def by_name(results):
    return {r.name: r for r in results}


def grade(text, cap=260, **kw):
    kw.setdefault("scripts", SCRIPTS)
    kw.setdefault("files", FILES)
    return by_name(s.grade(text, cap=cap, **kw))


class GoodSample(unittest.TestCase):
    def test_good_sample_passes_every_text_grader(self):
        r = grade((SAMPLES / "good-emission.md").read_text(encoding="utf-8"), tool_uses=[])
        for name in ("lock-present", "one-fence", "no-placeholders", "line-length",
                     "length-cap", "gates-exist", "cites-real", "self-check", "no-writes"):
            self.assertEqual(r[name].status, s.PASS, f"{name}: {r[name].detail}")

    def test_archive_grader_is_skipped_not_passed(self):
        r = grade((SAMPLES / "good-emission.md").read_text(encoding="utf-8"))
        self.assertEqual(r["archive-valid"].status, s.SKIPPED)
        self.assertIn("needs tools/archive.py (E-04)", r["archive-valid"].detail)


class BadSample(unittest.TestCase):
    """bad-emission.md is also echoed by the control case, so the in-eval graders see it too."""

    @classmethod
    def setUpClass(cls):
        cls.r = grade((SAMPLES / "bad-emission.md").read_text(encoding="utf-8"),
                      tool_uses=["Read", "Write"])

    def test_each_grader_fails(self):
        for name in ("lock-present", "one-fence", "no-placeholders", "line-length",
                     "gates-exist", "cites-real", "self-check", "no-writes"):
            self.assertEqual(self.r[name].status, s.FAIL, f"{name}: {self.r[name].detail}")

    def test_details_name_the_defect(self):
        self.assertIn("<branch>", self.r["no-placeholders"].detail)
        self.assertIn("[generator:", self.r["no-placeholders"].detail)
        self.assertIn("build", self.r["gates-exist"].detail)
        self.assertIn("src/invoice.js:99", self.r["cites-real"].detail)
        self.assertIn("src/totals.js", self.r["cites-real"].detail)


class Variants(unittest.TestCase):
    GOOD = (SAMPLES / "good-emission.md").read_text(encoding="utf-8")

    def test_length_cap_fails_when_over(self):
        self.assertEqual(grade(self.GOOD, cap=10)["length-cap"].status, s.FAIL)

    def test_long_line_counts_double(self):
        self.assertEqual(s.block_cost(["x" * 150, ""]), 3)

    def test_nested_fence_in_three_backticks_fails(self):
        text = self.GOOD.replace("````", "```")
        self.assertEqual(grade(text)["one-fence"].status, s.FAIL)

    def test_no_gate_at_all_fails(self):
        text = self.GOOD.replace("npm test", "run the tests").replace("npm run lint", "lint it")
        self.assertEqual(grade(text)["gates-exist"].status, s.FAIL)

    def test_quoted_code_is_not_a_placeholder(self):
        text = self.GOOD.replace("Begin with the branch.",
                                 "Keep `usage: ledgerlite <invoice.json>` as is. Begin.")
        self.assertEqual(grade(text)["no-placeholders"].status, s.PASS)

    @staticmethod
    def table(rows):
        return "| # | Item | Verdict | Reason |\n|---|---|---|---|\n" + "".join(
            f"| {n} | item {n} | PASS | ok |\n" for n in rows)

    def test_full_table_22_or_more_rows_passes(self):
        for rows in (range(1, 23), range(1, 24)):  # 22 rows today, 23 after E-08
            self.assertEqual(s.check_self_check(self.table(rows)).status, s.PASS)

    def test_table_missing_a_row_fails(self):
        r = s.check_self_check(self.table([n for n in range(1, 23) if n != 16]))
        self.assertEqual(r.status, s.FAIL)
        self.assertIn("16", r.detail)

    def test_compact_verdict_passes_and_none_fails(self):
        self.assertEqual(s.check_self_check("Self-check: 20 PASS · 3 N/A · 0 FAIL").status, s.PASS)
        self.assertEqual(s.check_self_check("Self-check: looks fine").status, s.FAIL)

    def test_v2_unique_basename_resolves_and_bad_line_still_fails(self):
        ok = self.GOOD.replace("docs/ROADMAP.md:6", "ROADMAP.md:6")
        self.assertEqual(grade(ok)["cites-real"].status, s.PASS)
        bad = self.GOOD.replace("docs/ROADMAP.md:6", "ROADMAP.md:60")
        self.assertEqual(grade(bad)["cites-real"].status, s.FAIL)

    def test_v2_path_pattern_quote_is_not_a_placeholder_but_bare_one_is(self):
        quoted = self.GOOD.replace("Begin with the branch.",
                                   'Branches are feat/<slug>; errors say "cannot read <file>".')
        self.assertEqual(grade(quoted)["no-placeholders"].status, s.PASS)
        bare = self.GOOD.replace("Begin with the branch.", "Begin with <branch>.")
        self.assertEqual(grade(bare)["no-placeholders"].status, s.FAIL)

    def test_v2_protocol_loaded_paths(self):
        marker = s.PROTOCOL_MARKER
        ctx = [{"type": "user", "message": {"content": f"x {marker} y"}}]
        read = [{"type": "user", "message": {"content": [
            {"type": "tool_result", "content": f"1\t# genprompt\n3\t`{marker}`"}]}}]
        none = [{"type": "system", "subtype": "init", "slash_commands": ["genprompt:slice"]}]
        self.assertIn("initial context", s.check_protocol_loaded(ctx).detail)
        self.assertIn("Read", s.check_protocol_loaded(read).detail)
        self.assertEqual(s.check_protocol_loaded(none).status, s.FAIL)
        lock = "TARGET LOCK\nArchetype   D: Slice execution\n"
        self.assertIn("inferred", s.check_protocol_loaded(none, lock).detail)
        self.assertEqual(s.check_protocol_loaded(none, "no lock here").status, s.FAIL)
        self.assertEqual(s.check_protocol_loaded(None).status, s.SKIPPED)

    def test_dry_run_archive_write_fails(self):
        with tempfile.TemporaryDirectory() as home:
            p = Path(home) / ".genprompt" / "generated-prompts" / "x.md"
            p.parent.mkdir(parents=True)
            p.write_text("x", encoding="utf-8")
            self.assertEqual(s.check_writes([], Path(home)).status, s.FAIL)

    def test_missing_inputs_are_skipped_not_passed(self):
        r = by_name(s.grade(self.GOOD, cap=260))
        self.assertEqual(r["gates-exist"].status, s.SKIPPED)
        self.assertEqual(r["cites-real"].status, s.SKIPPED)
        self.assertEqual(r["no-writes"].status, s.SKIPPED)


if __name__ == "__main__":
    unittest.main()
