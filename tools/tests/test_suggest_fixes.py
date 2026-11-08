"""doctor --suggest-fixes: a print-only repair plan. Built on a synthetic archive in a temp
GENPROMPT_HOME (never ~/.genprompt); the run must leave every file byte- and mtime-identical."""
from __future__ import annotations

import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import ROOT, error_lines, run_tool  # noqa: E402

DOCTOR = ROOT / "tools" / "doctor.py"
HEAD = "# genprompt shard: {key}  (path: /srv/repos/{key})\n# Fields: date | archetype | slug | file | task (<=200 chars)\n# schema: v3\n"
TAB = "\t"


def prompt(key: str, date: str, letters: str, *, self_check: bool = True, now: str = "Slice S01, the thing") -> str:
    body = [f"<!-- genprompt v3: key={key} | repo={key} | path=/srv/repos/{key} | date={date} | "
            f"archetype={letters} | follows=- -->", "", "````text", "Repo: /srv/repos/x, branch main.",
            f"NOW: {now}", "GATE: npm test (script)", "WHAT YOU CANNOT DO: push.", "REPORT: gates.",
            "Start now.", "````", ""]
    if self_check:
        body += ["| # | Item | Verdict | Reason |", "|---|---|---|---|", "| 1 | Target | PASS | fixture |", ""]
    return "\n".join(body)


class SuggestFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.home = Path(cls._tmp.name)
        a = cls.home / "generated-prompts"
        (a / "by-repo").mkdir(parents=True)
        (a / "alpha").mkdir()
        (a / "beta").mkdir()
        long_task = "Long task " + "x" * 230
        rows = [
            "2026-10-01 | D | s01-good | 2026-10-01-slice-s01-good.md | A good row",
            "2026-10-02 | none | s01-closeout | none | status: verified, no prompt emitted; abc1234",
            f"2026-10-03 | D | s02-long | 2026-10-03-slice-s02-long.md | {long_task}",
            TAB.join(["2026-10-04", "alpha", "Worker A", "Some Session", "2026-10-04 a note"]),
            "2026-10-05 | J | s03-status | - | status: parked, no prompt emitted; waiting",
            "2026-10-06 | D | s04-lost | - | Slice S04 with no file",
            "2026-10-07 | L | f01-nocheck | 2026-10-07-fix-f01-nocheck.md | A prompt without its self-check",
        ]
        (a / "by-repo" / "alpha.tsv").write_text(HEAD.format(key="alpha") + "\n".join(rows) + "\n", encoding="utf-8")
        (a / "alpha" / "2026-10-01-slice-s01-good.md").write_text(prompt("alpha", "2026-10-01", "D"), encoding="utf-8")
        (a / "alpha" / "2026-10-03-slice-s02-long.md").write_text(prompt("alpha", "2026-10-03", "D"), encoding="utf-8")
        (a / "alpha" / "2026-10-07-fix-f01-nocheck.md").write_text(
            prompt("alpha", "2026-10-07", "L", self_check=False), encoding="utf-8")
        (a / "alpha" / "2026-10-08-fix-f02-orphan.md").write_text(
            prompt("alpha", "2026-10-08", "L", now="Fix F02, the orphan"), encoding="utf-8")
        # beta: a non-standard shard header (no '# schema:' line); every row is v3-dated
        (a / "by-repo" / "beta.tsv").write_text(
            "# genprompt v3 shard: beta\n# date | letters | slug | file | task\n"
            "2026-10-26 | D | s01-b | 2026-10-26-slice-s01-b.md | Beta slice\n", encoding="utf-8")
        (a / "beta" / "2026-10-26-slice-s01-b.md").write_text(prompt("beta", "2026-10-26", "D"), encoding="utf-8")
        cls.before = cls.snapshot()
        cls.code, cls.out = run_tool(DOCTOR, "--suggest-fixes", home=cls.home)
        cls.after = cls.snapshot()
        _c, cls.archive_out = run_tool(DOCTOR, "--archive", home=cls.home)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    @classmethod
    def snapshot(cls) -> dict[str, tuple[str, int]]:
        return {str(p.relative_to(cls.home)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
                for p in cls.home.rglob("*") if p.is_file()}

    def block(self, tag: str, where: str) -> str:
        m = re.search(rf"^\[{tag}\] [^\n]*  {re.escape(where)}\n(?:    [^\n]*\n)*", self.out, re.M)
        self.assertIsNotNone(m, f"no [{tag}] block for {where}:\n{self.out}")
        return m.group(0)

    def test_writes_nothing_and_exits_0(self):
        self.assertEqual(self.code, 0, self.out)
        self.assertEqual(self.before, self.after)          # same files, same bytes, same mtimes
        self.assertIn("PRINT-ONLY", self.out)
        self.assertIn("BACK UP FIRST", self.out)

    def test_every_archive_error_is_covered(self):
        n = len(error_lines(self.archive_out))
        self.assertGreater(n, 0)
        self.assertIn(f"doctor --archive ERRORs: {n}; covered by this plan: {n}", self.out)

    def test_status_row_file_none_is_derivable(self):
        b = self.block("derivable", "by-repo/alpha.tsv:5")
        self.assertIn("after:  2026-10-02 | none | s01-closeout | - | status: verified", b)

    def test_long_task_is_shortened(self):
        b = self.block("derivable", "by-repo/alpha.tsv:6")
        after = re.search(r"after:  (.*)", b).group(1)
        self.assertLessEqual(len(after.split(" | ", 4)[4]), 200)
        self.assertTrue(after.startswith("2026-10-03 | D | s02-long | 2026-10-03-slice-s02-long.md | Long task"))

    def test_foreign_tab_row_is_manual(self):
        b = self.block("manual", "by-repo/alpha.tsv:7")
        self.assertIn("foreign row", b)
        self.assertNotIn("after:", b)

    def test_status_task_without_file_becomes_status_row(self):
        b = self.block("derivable", "by-repo/alpha.tsv:8")
        self.assertIn("after:  2026-10-05 | none | s03-status | - |", b)

    def test_prompt_row_without_file_needs_a_decision(self):
        b = self.block("manual", "by-repo/alpha.tsv:9")
        self.assertIn("only you know which", b)

    def test_missing_self_check_is_never_invented(self):
        b = self.block("manual", "alpha/2026-10-07-fix-f01-nocheck.md")
        self.assertIn("cannot be repaired automatically", b)
        self.assertNotIn("after:", b)

    def test_orphan_file_gets_a_row_from_its_header_and_now_line(self):
        b = self.block("derivable", "alpha/2026-10-08-fix-f02-orphan.md")
        self.assertIn("after:  2026-10-08 | L | f02-orphan | 2026-10-08-fix-f02-orphan.md | Fix F02, the orphan", b)

    def test_shard_header_is_derivable_for_a_pure_v3_shard(self):
        b = self.block("derivable", "by-repo/beta.tsv")
        self.assertIn("after:  # genprompt shard: beta  (path: /srv/repos/beta)", b)
        self.assertIn("# schema: v3", b)

    def test_usage_error_exits_2(self):
        code, _out = run_tool(DOCTOR, "--suggest-fixes", "--archive", home=self.home)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
