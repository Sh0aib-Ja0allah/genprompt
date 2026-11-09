"""realuse/run.py: A5 treats only content-free outside results as harmless.

    python -m unittest discover -s evals/lint
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "realuse"))

import run  # noqa: E402


class HarmlessTest(unittest.TestCase):
    def test_empty_glob_is_harmless(self):
        self.assertTrue(run.harmless("No files found"))
        self.assertTrue(run.harmless("  No files found\n"))
        self.assertTrue(run.harmless("No matches found"))

    def test_existing_harmless_results(self):
        for t in ("Permission to use Glob has been denied.", "File does not exist.",
                  "search timed out after 20s"):
            self.assertTrue(run.harmless(t), t)

    def test_names_are_flagged(self):
        self.assertFalse(run.harmless("C:/<other project>/CLAUDE.md"))
        self.assertFalse(run.harmless("No files found\nC:/<other project>/notes.md"))
        self.assertFalse(run.harmless("Found 2 files\nC:/a.md\nC:/b.md"))


class HomeModeTest(unittest.TestCase):
    def test_deny_rules_home_mode(self):
        work = Path("C:/genprompt-probe/x") if run.os.name == "nt" else Path("/var/tmp/genprompt-probe/x")
        cand, base = run.deny_rules(work), run.deny_rules(work, base=True)
        self.assertNotIn("Bash", cand)
        self.assertIn("Bash(ls:*)", cand)
        self.assertNotIn("Bash(python:*)", cand)
        self.assertIn("Bash(python:*)", base)
        self.assertIn("Bash(python3:*)", base)
        self.assertIn("Write(~/**)", cand)
        self.assertTrue(any(r.startswith("Write(") and r.endswith("/fixture/**)") for r in cand))
        self.assertIn("Bash", run.deny_rules())  # default mode keeps Bash off

    def test_safe_bash(self):
        self.assertTrue(run.SAFE_BASH_RE.match("git log -1 --format=%h -- package.json"))
        self.assertTrue(run.SAFE_BASH_RE.match("python3 C:/p/gp-cand/tools/archive.py --where"))
        self.assertFalse(run.SAFE_BASH_RE.match("cat ~/.gitconfig"))
        self.assertFalse(run.SAFE_BASH_RE.match("python3 C:/p/gp-cand/tools/archive.py --parts x"))


if __name__ == "__main__":
    unittest.main()
