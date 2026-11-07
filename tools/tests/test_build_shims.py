"""build_shims.py --check: passes on the repo, fails on an altered or extra command file.

Alterations happen in a temporary copy of tools/ and commands/, never in the repo's commands/.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import ROOT, run_tool  # noqa: E402

BUILD = ROOT / "tools" / "build_shims.py"


def load_build_shims():
    spec = importlib.util.spec_from_file_location("build_shims_under_test", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class BuildShims(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.copy = Path(self._tmp.name) / "plugin"
        (self.copy / "tools").mkdir(parents=True)
        shutil.copy2(BUILD, self.copy / "tools" / "build_shims.py")
        shutil.copytree(ROOT / "commands", self.copy / "commands")
        shutil.copytree(ROOT / "guide", self.copy / "guide")     # --check also covers 08-grammar.md
        self.script = self.copy / "tools" / "build_shims.py"

    def tearDown(self):
        self._tmp.cleanup()

    def test_check_passes_on_repo(self):
        code, out = run_tool(BUILD, "--check")
        self.assertEqual(code, 0, out)
        self.assertIn(", 0 differ/extra", out)

    def test_check_passes_on_unaltered_copy(self):
        # The control for the failure tests below: the copy itself is clean, so they fail for
        # the reason they name.
        code, out = run_tool(self.script, "--check", cwd=self.copy)
        self.assertEqual(code, 0, out)
        self.assertNotIn("ERROR", out)

    def test_check_fails_on_altered_shim(self):
        shim = self.copy / "commands" / "slice.md"
        shim.write_text(shim.read_text(encoding="utf-8") + "hand edit\n", encoding="utf-8", newline="\n")
        code, out = run_tool(self.script, "--check", cwd=self.copy)
        self.assertEqual(code, 1, out)
        self.assertIn("DIFF  commands/slice.md", out)
        self.assertNotIn("ERROR", out)

    def test_check_fails_on_extra_command(self):
        (self.copy / "commands" / "handmade.md").write_text("---\n---\n", encoding="utf-8")
        code, out = run_tool(self.script, "--check", cwd=self.copy)
        self.assertEqual(code, 1, out)
        self.assertIn("EXTRA commands/handmade.md", out)
        self.assertNotIn("ERROR", out)

    def test_tables_have_no_duplicates(self):
        self.assertEqual(load_build_shims().table_errors(), [])


if __name__ == "__main__":
    unittest.main()
