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

    def test_builtins_denied(self):
        rules = run.deny_rules(Path("C:/genprompt-probe/x"))
        for c in ("echo", "printf", "test", "[", "pwd", "env", "printenv"):
            self.assertIn(f"Bash({c}:*)", rules)

    def test_drive_root_dirs(self):
        # on this machine: the probe root's own top folder is never denied, its siblings are,
        # and "(" ")" never reach a rule
        root = run.default_workroot()
        dirs = run.drive_root_dirs(root)
        self.assertTrue(all(d.parent == Path(root.anchor) for d in dirs))
        self.assertNotIn(root.resolve().parents[len(root.resolve().parents) - 2], dirs)
        rules = run.deny_rules(root=root)
        self.assertFalse(any("genprompt-probe" in r for r in rules))
        self.assertFalse(any(r.count("(") != 1 or r.count(")") != 1
                             for r in rules if r.startswith(("Read(", "Glob(", "Grep("))))
        self.assertEqual(run.drive_root_dirs(Path(root.anchor)), [])

    def test_cp6a_harmless(self):
        self.assertTrue(run.harmless("ls from 'C:\\Users\\x' was blocked by a deny rule."))
        self.assertTrue(run.STORE_ALIAS_RE.search(
            "Exit code 49 / Python was not found; run without arguments to install"))
        arch = 'python "C:/p/gp-cand/tools/archive.py"'
        self.assertTrue(run.safe_bash(f"{arch} --dry-run --parts C:/p/homes/h/tmp/x.json 2>&1"))
        self.assertTrue(run.safe_bash(f"python3 C:/p/gp-cand/tools/archive.py --where 2>&1 || "
                                      f"{arch} --where"))
        # a base's archive.py, chained shell or a non-dry-run write is never safe
        self.assertFalse(run.safe_bash('python "C:/p/gp-b-fb4db7b/tools/archive.py" --where'))
        self.assertFalse(run.safe_bash(f"{arch} --where; cat ~/.gitconfig"))
        self.assertFalse(run.safe_bash(f"{arch} --parts C:/p/x.json"))
        self.assertFalse(run.safe_bash('echo "$HOME"'))


if __name__ == "__main__":
    unittest.main()
