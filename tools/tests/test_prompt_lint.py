"""doctor's per-file lint (doctor --prompt, shared with tools/archive.py).

One passing fixture file; every other case is built by mutating it in memory. Severities follow
the calibration on the real archive: FAIL only for a broken record (header, fence, stub block,
self-check table), WARN for advisory or heuristic checks.
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
ALL_CHECKS = {"header", "filename-words", "one-fence", "placeholders", "line-width", "length",
              "terminal-imperative", "gates-labelled", "header-vocab", "report-line", "self-check"}


def lint(text: str, name: str = PASS_FILE.name) -> dict[str, tuple[str, str]]:
    return {c: (s, d) for c, s, d in DOC.lint_prompt(text, name, CMDS)}


def in_block(text: str, line: str) -> str:
    """Insert a line just after the NOW: line inside the block."""
    return text.replace("NOW: Slice S02, add the settings page.\n",
                        f"NOW: Slice S02, add the settings page.\n{line}\n", 1)


def self_check_table(rows: int) -> str:
    return "| # | Item | Verdict | Reason |\n|---|---|---|---|\n" + "".join(
        f"| {n} | item {n} | PASS | reason {n} |\n" for n in range(1, rows + 1))


class Base(unittest.TestCase):
    def assertStatus(self, text: str, check: str, status: str, name: str = PASS_FILE.name):
        got, detail = lint(text, name)[check]
        self.assertEqual(got, status, f"{check}: {detail}")


class PassingFile(Base):
    def test_fixture_passes_every_check(self):
        res = lint(BASE)
        self.assertEqual({c: s for c, (s, _d) in res.items() if s != "PASS"}, {}, res)
        self.assertEqual(set(res), ALL_CHECKS)

    def test_header_without_the_e05_fields_is_still_valid(self):
        # files archived before E-05 lack flags/via/lock: the header stays PASS, the vocab only WARNs
        old = BASE.replace(" | flags=- | via=cwd | lock=accepted", "", 1)
        self.assertStatus(old, "header", "PASS")
        self.assertStatus(old, "header-vocab", "WARN")

    def test_lock_auto_is_a_valid_value(self):
        # E-11b: opt-in auto-go archives lock=auto
        self.assertStatus(BASE.replace("lock=accepted", "lock=auto", 1), "header-vocab", "PASS")

    def test_full_vocabulary_passes(self):
        text = BASE.replace("flags=- | via=cwd | lock=accepted", "flags=--go --brief | via=argument | lock=go", 1)
        self.assertStatus(text, "header-vocab", "PASS")

    def test_22_row_self_check_table_passes(self):
        text = BASE.split("| # | Item |")[0] + self_check_table(22)
        self.assertStatus(text, "self-check", "PASS")

    def test_23_row_self_check_table_passes(self):
        text = BASE.split("| # | Item |")[0] + self_check_table(23)
        self.assertStatus(text, "self-check", "PASS")


class Failures(Base):
    """A broken record: FAIL, exit 1."""

    def test_header_invalid(self):
        self.assertStatus(BASE.replace("archetype=D", "archetype=slice", 1), "header", "FAIL")

    def test_header_optional_fields_out_of_order(self):
        self.assertStatus(BASE.replace("flags=- | via=cwd | lock=accepted", "lock=accepted | flags=- | via=cwd", 1),
                          "header", "FAIL")

    def test_header_date_does_not_match_filename(self):
        self.assertStatus(BASE, "header", "FAIL", name="2026-10-08-slice-s02-lint-pass.md")

    def test_no_fence(self):
        self.assertStatus(BASE.replace("````text\n", "").replace("````\n", ""), "one-fence", "FAIL")

    def test_unclosed_fence(self):
        self.assertStatus(BASE.split("Start with CHECKPOINT A now.")[0], "one-fence", "FAIL")

    def test_nested_fence_in_three_backticks(self):
        self.assertStatus(BASE.replace("````", "```"), "one-fence", "FAIL")

    def test_stub_block(self):
        head, rest = BASE.split("````text\n", 1)
        stub = head + "````text\nSee the transcript.\nStart now.\n````\n" + rest.split("````\n", 1)[1]
        self.assertStatus(stub, "one-fence", "FAIL")

    def test_self_check_missing(self):
        self.assertStatus(BASE.split("| # | Item |")[0], "self-check", "FAIL")


class Warnings(Base):
    """Advisory or heuristic: WARN, never blocks."""

    def test_filename_words_do_not_match_label(self):
        # §10.1 wants every archetype's command word; a dominant-only name is a WARN
        self.assertStatus(BASE.replace("archetype=D", "archetype=D+L", 1), "filename-words", "WARN")

    def test_extra_fenced_snippet_outside_the_prompt(self):
        self.assertStatus(BASE.replace("Grounding:", "```text\nstray\n```\nGrounding:", 1), "one-fence", "WARN")

    def test_leftover_placeholder(self):
        self.assertStatus(in_block(BASE, "Scope: <area to assess>"), "placeholders", "WARN")

    def test_leftover_generator_note(self):
        self.assertStatus(in_block(BASE, "[generator: drop this line]"), "placeholders", "WARN")

    def test_line_over_100_chars(self):
        # §4.21 counts a long line as ceil(len/100) lines; it does not forbid it
        self.assertStatus(in_block(BASE, "x" * 101), "line-width", "WARN")

    def test_length_over_tier_cap(self):
        self.assertStatus(in_block(BASE, "\n".join(f"filler {i}" for i in range(260))), "length", "WARN")

    def test_terminal_imperative_missing(self):
        self.assertStatus(BASE.replace("Start with CHECKPOINT A now.", "Thanks for reading."),
                          "terminal-imperative", "WARN")

    def test_negative_confirmation_as_last_line(self):
        self.assertStatus(BASE.replace("Start with CHECKPOINT A now.", "No push, no PR, no new files."),
                          "terminal-imperative", "WARN")

    def test_gates_unlabelled(self):
        self.assertStatus(BASE.replace("(script)", ""), "gates-labelled", "WARN")

    def test_unknown_via_value(self):
        self.assertStatus(BASE.replace("via=cwd", "via=guess", 1), "header-vocab", "WARN")

    def test_unknown_lock_value(self):
        self.assertStatus(BASE.replace("lock=accepted", "lock=maybe", 1), "header-vocab", "WARN")

    def test_unknown_flag(self):
        self.assertStatus(BASE.replace("flags=-", "flags=--go --turbo", 1), "header-vocab", "WARN")

    def test_report_without_genprompt_report_line(self):
        self.assertStatus(BASE.replace("GENPROMPT-REPORT", "status"), "report-line", "WARN")


class FalsePositivesFixed(Base):
    """Shapes from the real archive that the first version flagged wrongly."""

    def test_short_prompt_in_long_lines_is_not_a_stub(self):
        head, rest = BASE.split("````text\n", 1)
        long = " ".join(["word"] * 50)                       # 249 chars: counts as 3 lines
        text = head + "````text\n" + "\n".join([long] * 5) + "\nGATE: npm test (script)\nStart now.\n````\n" \
            + rest.split("````\n", 1)[1]
        self.assertStatus(text, "one-fence", "PASS")

    def test_html_tag_and_regex_are_not_placeholders(self):
        text = in_block(BASE, 'Set <html lang dir> and <label for>; keep Map<String, Int>, '
                              '<div class="x">, the regex <G|Sn> and a <= b.')
        self.assertStatus(text, "placeholders", "PASS")

    def test_gate_label_with_a_note(self):
        self.assertStatus(BASE.replace("npm test (script)", "npm test (script, package.json:7)"),
                          "gates-labelled", "PASS")

    def test_gate_label_before_the_command(self):
        text = BASE.replace("GATE: npm test (script) · npm run lint (script)",
                            "- Gate (derived): npm test\n- Check (derived): npm run lint")
        self.assertStatus(text, "gates-labelled", "PASS")

    def test_imperative_later_in_the_last_line(self):
        self.assertStatus(BASE.replace("Start with CHECKPOINT A now.",
                                       "Scope: the settings page only; report the gates."),
                          "terminal-imperative", "PASS")


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
    def run_on(self, text: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / PASS_FILE.name
            shutil.copy2(PASS_FILE, f)
            f.write_text(text, encoding="utf-8")
            return run_tool(DOCTOR, "--prompt", str(f))

    def test_prompt_mode_passes_on_fixture(self):
        code, out = run_tool(DOCTOR, "--prompt", str(PASS_FILE))
        self.assertEqual(code, 0, out)
        self.assertIn("Prompt lint: 11 PASS, 0 WARN, 0 FAIL", out)

    def test_warnings_alone_exit_0(self):
        code, out = self.run_on(BASE.replace("Start with CHECKPOINT A now.", "Thanks."))
        self.assertEqual(code, 0, out)
        self.assertIn("WARN  terminal-imperative", out)

    def test_a_fail_exits_1_and_names_the_check(self):
        code, out = self.run_on(BASE.split("| # | Item |")[0])
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL  self-check", out)

    def test_prompt_mode_needs_a_file(self):
        code, _out = run_tool(DOCTOR, "--prompt")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
