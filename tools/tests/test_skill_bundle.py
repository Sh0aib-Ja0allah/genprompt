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
        self.assertIn("Summary: 0 ERROR, 0 WARN", out)

    def test_cli_prints_path_and_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_tool(TOOL, "--out", tmp)
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"sha256   [0-9a-f]{64}")
        self.assertIn(self.r1["sha256"], out)


if __name__ == "__main__":
    unittest.main()
