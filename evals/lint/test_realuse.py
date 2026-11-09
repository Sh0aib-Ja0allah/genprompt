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


class DriveRootTest(unittest.TestCase):
    """A drive-root Glob/Grep is judged by the names it returns (CP6a-2 false alarm)."""
    PROBE = "C:/genprompt-probe"

    def test_is_drive_root(self):
        for p in ("C:", "C:/", "C:\\", "c:/", "/c", "/c/", "/"):
            self.assertTrue(run.is_drive_root(p), p)
        for p in ("", "C:/genprompt-probe", "C:/Users", "/c/x", "relative"):
            self.assertFalse(run.is_drive_root(p), p)

    def test_probe_names_pass(self):
        # The CP6a-2 slice r1 / plan r1 result, verbatim in shape: Windows separators and the
        # run's own CLAUDE.md printed relative to its cwd.
        text = ("C:\\genprompt-probe\\genprompt-probe-1\\fixture\\CLAUDE.md\n"
                "C:\\genprompt-probe\\genprompt-homeiso-2\\fixture\\CLAUDE.md\n"
                "CLAUDE.md")
        self.assertEqual(run.names_outside(text, self.PROBE), [])
        self.assertEqual(run.names_outside("/c/genprompt-probe/x/CLAUDE.md", self.PROBE), [])

    def test_messages_pass(self):
        for t in ("No files found", "Found 2 files\nC:/genprompt-probe/a.md\nb/CLAUDE.md",
                  "Ripgrep search timed out after 20 seconds. The search may have matched "
                  "files but did not complete in time.",
                  "Permission to use Glob has been denied.",
                  "(Results are truncated. Consider using a more specific path or pattern.)"):
            self.assertEqual(run.names_outside(t, self.PROBE), [], t)

    def test_outside_names_flagged(self):
        text = ("C:/genprompt-probe/a/CLAUDE.md\n"
                "C:\\Windows\\System32\\denied.md\n"   # "denied" must not hide a name
                "/c/<other project>/CLAUDE.md\n"
                "C:/genprompt-probe-other/CLAUDE.md\n"  # a sibling prefix is not the probe
                "../../<other project>/AGENTS.md\n"
                "C:/<other project>/x.md:12:matched text")  # Grep content mode
        self.assertEqual(len(run.names_outside(text, self.PROBE)), 5)

    def test_analyze_judges_drive_root_by_names(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            probe = Path(tmp).resolve() / "genprompt-probe"
            work = probe / "run-1"
            work.mkdir(parents=True)
            inside = (probe / "run-0" / "fixture" / "CLAUDE.md").as_posix()

            def call(i, path, result):
                use = {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": f"t{i}", "name": "Glob",
                     "input": {"pattern": "CLAUDE*.md", "path": path}}]}}
                res = {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": f"t{i}", "content": result}]}}
                return [json.dumps(use), json.dumps(res)]

            lines = (call(1, "C:/", f"{inside}\nCLAUDE.md")
                     + call(2, "C:\\", [{"type": "text", "text": inside}])
                     + call(3, "C:/", "No files found")
                     + call(4, "C:/", f"{inside}\nC:/<other project>/CLAUDE.md")
                     + call(5, "C:/Windows", "C:/Windows/notes.md"))
            trace = work / "t.jsonl"
            trace.write_text("\n".join(lines), encoding="utf-8")
            out = run.analyze(trace, work / "gp-cand", work)["outside"]
        self.assertEqual(len(out), 2, out)
        self.assertIn("<other project>", out[0][2])      # call 4: a leaked name
        self.assertEqual(out[1][1], "C:/Windows")         # call 5: not a drive root, by path


if __name__ == "__main__":
    unittest.main()
