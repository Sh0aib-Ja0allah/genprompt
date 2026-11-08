"""tools/build_skill_bundle.py: the Agensi bundle is derived from the suite and deterministic.
Every build goes to a temp dir; nothing is written into the repo."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import ROOT, run_tool  # noqa: E402

TOOL = ROOT / "tools" / "build_skill_bundle.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BUNDLE = load(TOOL, "bundle_under_test")
SHIMS = load(ROOT / "tools" / "build_shims.py", "shims_for_bundle_test")
META = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


class SkillBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out1 = Path(cls._tmp.name) / "a"
        cls.out2 = Path(cls._tmp.name) / "b"
        cls.r1 = BUNDLE.build(cls.out1)
        cls.r2 = BUNDLE.build(cls.out2)
        with zipfile.ZipFile(cls.r1["zip"]) as zf:
            cls.names = zf.namelist()
            cls.skill = zf.read("genprompt/SKILL.md").decode("utf-8")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_two_builds_are_byte_identical(self):
        self.assertEqual(self.r1["sha256"], self.r2["sha256"])
        self.assertEqual(hashlib.sha256(self.r2["zip"].read_bytes()).hexdigest(), self.r2["sha256"])

    def test_version_comes_from_plugin_json(self):
        self.assertEqual(self.r1["version"], META["version"])
        self.assertIn(f"version: {META['version']}\n", self.skill)
        self.assertTrue(self.r1["zip"].name.endswith(f"-{META['version']}.zip"))

    def test_counts_come_from_the_tables(self):
        self.assertIn(f"## The {len(SHIMS.ARCHETYPES)} archetypes", self.skill)
        self.assertIn(f"## The {len(SHIMS.UTILITIES)} utilities", self.skill)
        rows = re.findall(r"^\| [A-Z] \| `/genprompt:([a-z]+)` \|", self.skill, re.M)
        self.assertEqual(rows, [a.cmd for a in SHIMS.ARCHETYPES])
        n_cmds = 1 + len(SHIMS.ARCHETYPES) + len(SHIMS.UTILITIES)
        self.assertIn(f"through its {n_cmds} slash commands", self.skill)

    def test_layout_is_one_genprompt_folder_with_skill_md(self):
        self.assertTrue(all(n.startswith("genprompt/") for n in self.names))
        self.assertIn("genprompt/SKILL.md", self.names)
        for must in ("PROTOCOL.md", "LICENSE", ".claude-plugin/plugin.json", "tools/doctor.py",
                     "tools/build_shims.py", "tools/archive.py", "archetypes/README.md", "guide/00-index.md"):
            self.assertIn(f"genprompt/{must}", self.names, must)
        self.assertEqual(self.names, sorted(self.names))

    def test_nothing_outside_the_intended_set(self):
        banned = (".git/", ".github/", "evals/", "tools/tests/", "assets/", "dist/", "__pycache__")
        for n in self.names:
            rel = n[len("genprompt/"):]
            self.assertFalse(rel.startswith(banned) or "__pycache__" in rel or rel.endswith(".pyc"), n)
        self.assertNotIn("genprompt/.gitignore", self.names)

    def test_every_tracked_suite_file_is_included(self):
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True, check=True)
        expected = {f"genprompt/{p}" for p in out.stdout.split()
                    if not p.startswith(BUNDLE.EXCLUDE_PREFIXES) and p not in BUNDLE.EXCLUDE_FILES}
        self.assertEqual(set(self.names) - {"genprompt/SKILL.md"}, expected)

    def test_entries_have_a_fixed_timestamp(self):
        with zipfile.ZipFile(self.r1["zip"]) as zf:
            self.assertEqual({i.date_time for i in zf.infolist()}, {BUNDLE.FIXED_TIME})

    def test_loose_skill_copy_matches_the_zipped_one(self):
        self.assertEqual(self.r1["skill"].read_text(encoding="utf-8"), self.skill)

    def test_extracted_bundle_passes_doctor_suite(self):
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(self.r1["zip"]) as zf:
            zf.extractall(tmp)
            code, out = run_tool(Path(tmp) / "genprompt" / "tools" / "doctor.py", "--suite",
                                 cwd=Path(tmp) / "genprompt")
        self.assertEqual(code, 0, out)
        # The bundle must pass the suite with no ERROR; a WARN (e.g. the PROTOCOL size budget)
        # is the repo's own state and is reported, not a bundle defect.
        self.assertIn("Summary: 0 ERROR,", out)

    def test_cli_prints_path_and_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_tool(TOOL, "--out", tmp)
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"sha256   [0-9a-f]{64}")
        self.assertIn(self.r1["sha256"], out)


class BundleCurrency(unittest.TestCase):
    """E-18b: doctor --suite checks the bundle the tool WOULD build, without building a zip."""

    def setUp(self):
        self.doc = load(ROOT / "tools" / "doctor.py", "doctor_bundle_check")
        self.skill = BUNDLE.skill_md(META, SHIMS)
        self.names = BUNDLE.bundle_files(ROOT, use_git=False)

    def errors(self, **kw) -> list[str]:
        self.doc.findings.clear()
        self.doc.check_bundle(**kw)
        return [m for sev, _a, m in self.doc.findings if sev == "ERROR"]

    def test_repo_bundle_is_current(self):
        self.assertEqual(self.errors(), [])

    def test_walk_matches_git_file_set(self):
        # doctor walks the tree (no subprocess); it must pick the same files as the git-based build
        self.assertEqual(set(self.names), set(BUNDLE.bundle_files(ROOT)))

    def test_stale_version_is_an_error(self):
        stale = self.skill.replace(f"version: {META['version']}", "version: 1.0.0", 1)
        errs = self.errors(skill=stale, names=self.names)
        self.assertTrue(any("SKILL.md version 1.0.0 != plugin.json" in e for e in errs), errs)

    def test_stale_counts_are_errors(self):
        n = len(SHIMS.ARCHETYPES)
        stale = self.skill.replace(f"## The {n} archetypes", f"## The {n - 1} archetypes", 1)
        stale = re.sub(r"^\| W \|.*\n", "", stale, flags=re.M)          # a 22-row listing
        errs = self.errors(skill=stale, names=self.names)
        self.assertTrue(any(f"'## The {n} archetypes'" in e for e in errs), errs)
        self.assertTrue(any("archetype table differs" in e for e in errs), errs)

    def test_missing_runtime_file_is_an_error(self):
        names = [n for n in self.names if n != "commands/slice.md" and n != "tools/archive.py"]
        errs = self.errors(skill=self.skill, names=names)
        self.assertTrue(any("commands/slice.md would be missing" in e for e in errs), errs)
        self.assertTrue(any("tools/archive.py would be missing" in e for e in errs), errs)

    def test_shipping_evals_or_tests_is_an_error(self):
        names = self.names + ["evals/run.py", "tools/tests/test_doctor.py", "dist/agensi/x.zip"]
        errs = self.errors(skill=self.skill, names=names)
        for rel in ("evals/run.py", "tools/tests/test_doctor.py", "dist/agensi/x.zip"):
            self.assertTrue(any(f"bundle: {rel} would be shipped" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
