"""E-21: every tool resolves the genprompt home through ONE helper, doctor.genprompt_home(), which
honours GENPROMPT_HOME. Nothing here touches the real ~/.genprompt: the home-relative case
redirects HOME/USERPROFILE to a temp dir and every write goes to a temp GENPROMPT_HOME."""
from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import FIXTURES, ROOT, run_tool  # noqa: E402

TOOLS = ROOT / "tools"
PASS_FILE = FIXTURES / "lint" / "2026-10-07-slice-s02-lint-pass.md"
REL_FILE = Path("generated-prompts") / "lint-demo" / PASS_FILE.name


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DOC = load(TOOLS / "doctor.py", "doctor_home_test")


def parts() -> dict:
    return {"key": "lint-demo", "repo": "lint-demo", "path": "/srv/repos/lint-demo",
            "date": "2026-10-07", "archetype": "D", "follows": "-", "slug": "s02-lint-pass",
            "task": "Slice S02: add the settings page", "flags": "-", "via": "cwd",
            "lock": "accepted", "body": PASS_FILE.read_text(encoding="utf-8").split("\n", 1)[1]}


class Helper(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def test_unset_or_blank_means_the_default_home(self):
        for env in ({}, {"GENPROMPT_HOME": ""}, {"GENPROMPT_HOME": "   "}):
            self.assertEqual(DOC.genprompt_home(env), Path.home() / ".genprompt", env)

    def test_absolute_value_is_used_as_is(self):
        self.assertEqual(DOC.genprompt_home({"GENPROMPT_HOME": str(self.tmp)}), self.tmp)
        self.assertEqual(DOC.genprompt_home({"GENPROMPT_HOME": f"  {self.tmp}  "}), self.tmp)

    def test_tilde_is_expanded_against_the_user_home(self):
        fake = {"HOME": str(self.tmp), "USERPROFILE": str(self.tmp)}
        with mock.patch.dict(os.environ, fake):
            got = DOC.genprompt_home({"GENPROMPT_HOME": "~/probe-home"})
        self.assertEqual(got, self.tmp / "probe-home")
        self.assertTrue(got.is_absolute())

    def test_relative_value_becomes_absolute(self):
        old = os.getcwd()
        os.chdir(self.tmp)
        try:
            got = DOC.genprompt_home({"GENPROMPT_HOME": "sandbox"})
        finally:
            os.chdir(old)
        self.assertEqual(got, self.tmp / "sandbox")

    def test_module_constants_follow_the_helper(self):
        self.assertEqual(DOC.GENPROMPT_HOME, DOC.genprompt_home())
        self.assertEqual(DOC.ARCHIVE, DOC.GENPROMPT_HOME / "generated-prompts")


class OneResolver(unittest.TestCase):
    """No tool resolves the home on its own: Path.home(), expanduser() and the GENPROMPT_HOME
    variable appear in tools/*.py only inside doctor.genprompt_home()."""

    PATTERN = re.compile(r"Path\.home\(|expanduser\(|environ[^\n]*GENPROMPT_HOME")

    def test_only_the_helper_resolves_the_home(self):
        tree = ast.parse((TOOLS / "doctor.py").read_text(encoding="utf-8"))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "genprompt_home")
        allowed = range(fn.lineno, fn.end_lineno + 1)
        stray = []
        for py in sorted(TOOLS.glob("*.py")):
            for no, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                code = line.split("#", 1)[0]
                if self.PATTERN.search(code) and not (py.name == "doctor.py" and no in allowed):
                    stray.append(f"{py.name}:{no}: {line.strip()}")
        self.assertEqual(stray, [])


class ToolsHonourTheOverride(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.src = self.tmp / "parts.json"
        self.src.write_text(json.dumps(parts()), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_archive_resolves_the_home_per_run_not_at_import(self):
        # Imported first, pointed at the sandbox afterwards: the write must still land there.
        arch = load(TOOLS / "archive.py", "archive_home_test")
        home = self.tmp / "late-home"
        with mock.patch.dict(os.environ, {"GENPROMPT_HOME": str(home)}), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            code = arch.main([str(self.src)])
        self.assertEqual(code, 0, out.getvalue())
        self.assertTrue((home / REL_FILE).exists())

    def test_archive_relative_home_resolves_against_cwd(self):
        code, out = run_tool(TOOLS / "archive.py", str(self.src), home=Path("rel-home"), cwd=self.tmp)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.tmp / "rel-home" / REL_FILE).exists(), out)

    def test_where_prints_the_resolved_home_and_writes_nothing(self):
        home = self.tmp / "where-home"
        code, out = run_tool(TOOLS / "archive.py", "--where", home=home)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [f"home {home.as_posix()}",
                                            f"local-rules {home.as_posix()}/local-rules.md (absent)"])
        self.assertFalse(home.exists())
        home.mkdir()
        (home / "local-rules.md").write_text("auto-go: on\n", encoding="utf-8")
        _code, out = run_tool(TOOLS / "archive.py", "--where", home=home)
        self.assertTrue(out.rstrip().endswith("local-rules.md (present)"), out)

    def test_where_takes_no_other_argument(self):
        code, out = run_tool(TOOLS / "archive.py", "--where", str(self.src), home=self.tmp / "h")
        self.assertEqual(code, 2, out)
        self.assertFalse((self.tmp / "h").exists())

    def test_suggest_fixes_backup_line_names_the_active_home(self):
        home = self.tmp / "fixture-home"
        shutil.copytree(FIXTURES / "bad", home)
        code, out = run_tool(TOOLS / "doctor.py", "--suggest-fixes", home=home)
        self.assertEqual(code, 0, out)
        backup = next((ln for ln in out.splitlines() if ln.startswith("BACK UP FIRST")), "")
        self.assertIn(str(home), backup)
        self.assertNotIn("~/.genprompt", backup)


if __name__ == "__main__":
    unittest.main()
