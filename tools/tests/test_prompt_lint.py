"""doctor's per-file lint (doctor --prompt, shared with tools/archive.py).

One passing fixture file, plus one failing case per check, built by mutating that file in memory.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import FIXTURES, ROOT, run_tool  # noqa: E402

DOCTOR = ROOT / "tools" / "doctor.py"
PASS_FILE = FIXTURES / "lint" / "2026-10-07-slice-s02-lint-pass.md"


def load_doctor():
    spec = importlib.util.spec_from_file_location("doctor_lint_under_test", DOCTOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DOC = load_doctor()
CMDS = DOC.cmd_map()
BASE = PASS_FILE.read_text(encoding="utf-8")


def lint(text: str, name: str = PASS_FILE.name) -> dict[str, tuple[bool, str]]:
    return {c: (ok, d) for c, ok, d in DOC.lint_prompt(text, name, CMDS)}


def in_block(text: str, line: str) -> str:
    """Insert a line just after the NOW: line inside the block."""
    return text.replace("NOW: Slice S02, add the settings page.\n",
                        f"NOW: Slice S02, add the settings page.\n{line}\n", 1)


class PassingFile(unittest.TestCase):
    def test_fixture_passes_every_check(self):
        res = lint(BASE)
        self.assertEqual([c for c, (ok, _d) in res.items() if not ok], [], res)
        self.assertEqual(set(res), {"header", "one-fence", "placeholders", "line-width", "length",
                                    "terminal-imperative", "gates-labelled", "self-check"})

    def test_optional_header_fields_are_accepted(self):
        text = BASE.replace("follows=- -->", "follows=- | flags=--go | via=cwd | lock=go -->", 1)
        self.assertTrue(lint(text)["header"][0], lint(text)["header"])

    def test_code_in_angle_brackets_is_not_a_placeholder(self):
        text = in_block(BASE, 'Keep Map<String, Int> and <div class="x"> and a <= b as they are.')
        self.assertTrue(lint(text)["placeholders"][0], lint(text)["placeholders"])


class FailingChecks(unittest.TestCase):
    def assertFails(self, text: str, check: str, name: str = PASS_FILE.name):
        ok, detail = lint(text, name)[check]
        self.assertFalse(ok, f"{check} should FAIL: {detail}")

    def test_header_invalid(self):
        self.assertFails(BASE.replace("archetype=D", "archetype=slice", 1), "header")

    def test_header_optional_fields_out_of_order(self):
        self.assertFails(BASE.replace("follows=- -->", "follows=- | lock=go | flags=--go -->", 1), "header")

    def test_header_filename_mismatch(self):
        self.assertFails(BASE, "header", name="2026-10-07-fix-s02-lint-pass.md")

    def test_two_fenced_blocks(self):
        self.assertFails(BASE.replace("Grounding:", "```text\nstray\n```\nGrounding:", 1), "one-fence")

    def test_unclosed_fence(self):
        self.assertFails(BASE.split("Start with CHECKPOINT A now.")[0], "one-fence")

    def test_nested_fence_needs_four_backticks(self):
        self.assertFails(BASE.replace("````", "```"), "one-fence")

    def test_leftover_placeholder(self):
        self.assertFails(in_block(BASE, "Scope: <area to assess>"), "placeholders")

    def test_leftover_generator_note(self):
        self.assertFails(in_block(BASE, "[generator: drop this line]"), "placeholders")

    def test_line_over_100_chars(self):
        self.assertFails(in_block(BASE, "x" * 101), "line-width")

    def test_length_over_tier_cap(self):
        self.assertFails(in_block(BASE, "\n".join(f"filler {i}" for i in range(260))), "length")

    def test_terminal_imperative_missing(self):
        self.assertFails(BASE.replace("Start with CHECKPOINT A now.", "Thanks for reading."), "terminal-imperative")

    def test_gates_unlabelled(self):
        self.assertFails(BASE.replace("(script)", ""), "gates-labelled")

    def test_self_check_missing(self):
        self.assertFails(BASE.split("| # | Item |")[0], "self-check")


class TierCaps(unittest.TestCase):
    def body(self, n: int, checkpoints: int = 0) -> list[str]:
        return [f"CHECKPOINT {c}" for c in "AB"[:checkpoints]] + ["x"] * n

    def test_slice_with_several_checkpoints_gets_320(self):
        self.assertEqual(DOC.tier_cap(["D"], self.body(10, 2), "")[0], 320)
        self.assertEqual(DOC.tier_cap(["D"], self.body(10, 1), "")[0], 260)

    def test_hybrid_takes_the_largest_tier(self):
        self.assertEqual(DOC.tier_cap(["J", "D"], self.body(10), "")[0], 260)

    def test_measured_large_only_when_row_21_says_so(self):
        row = "| 21 | Length | PASS | measured-large: 5 commits |"
        self.assertEqual(DOC.tier_cap(["P"], self.body(10), row)[0], 240)
        self.assertEqual(DOC.tier_cap(["P"], self.body(10), "| 21 | Length | PASS | fine |")[0], 200)

    def test_tier_map_matches_guide(self):
        DOC.findings.clear()
        DOC.check_tiers()
        self.assertEqual([f for f in DOC.findings if f[0] == "ERROR"], [])

    def test_tier_drift_in_guide_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "guide").mkdir()
            src = (ROOT / "guide" / "03-blocks.md").read_text(encoding="utf-8")
            (root / "guide" / "03-blocks.md").write_text(src.replace("| Delta | 120 |", "| Delta | 130 |"),
                                                        encoding="utf-8")
            DOC.findings.clear()
            DOC.check_tiers(root)
        self.assertTrue(any("Delta cap 130" in f[2] for f in DOC.findings), DOC.findings)


class Cli(unittest.TestCase):
    def test_prompt_mode_passes_on_fixture(self):
        code, out = run_tool(DOCTOR, "--prompt", str(PASS_FILE))
        self.assertEqual(code, 0, out)
        self.assertIn("Prompt lint: 8 PASS, 0 FAIL", out)

    def test_prompt_mode_fails_and_names_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / PASS_FILE.name
            shutil.copy2(PASS_FILE, bad)
            bad.write_text(BASE.replace("Start with CHECKPOINT A now.", "Thanks."), encoding="utf-8")
            code, out = run_tool(DOCTOR, "--prompt", str(bad))
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL  terminal-imperative", out)

    def test_prompt_mode_needs_a_file(self):
        code, _out = run_tool(DOCTOR, "--prompt")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
