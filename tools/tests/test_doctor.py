"""doctor.py against fixture archives: it must pass the good case and FAIL on each known-bad case.

The fixtures live in tools/tests/fixtures/ and are reached through GENPROMPT_HOME, so the tests
never read the real ~/.genprompt archive.
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import FIXTURES, ROOT, error_lines, run_tool  # noqa: E402

DOCTOR = ROOT / "tools" / "doctor.py"
GOOD = FIXTURES / "good"
BAD = FIXTURES / "bad"


class GoodArchive(unittest.TestCase):
    def test_good_archive_passes(self):
        code, out = run_tool(DOCTOR, "--archive", home=GOOD)
        self.assertEqual(error_lines(out), [], out)
        self.assertIn("Summary: 0 ERROR, 0 WARN", out)
        self.assertEqual(code, 0, out)

    def test_short_prompt_in_long_lines_is_not_a_stub(self):
        # 6 physical block lines but ~15 width-counted lines: the old physical-line rule called
        # this "the full prompt is missing"; the width-aware rule (shared with lint_prompt) does not
        _code, out = run_tool(DOCTOR, "--archive", home=GOOD)
        self.assertNotIn("f01-long-lines", out)
        self.assertIn("Measured (flags/via/lock in the header): 0 file(s); 2 older file(s) predate the fields", out)

    def test_missing_archive_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_tool(DOCTOR, "--archive", home=Path(tmp))
        self.assertEqual(code, 0, out)
        self.assertIn("no archive yet", out)


class BadArchive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code, cls.out = run_tool(DOCTOR, "--archive", "--verbose", home=BAD)
        cls.errors = error_lines(cls.out)

    def errors_for(self, name: str) -> list[str]:
        return [ln for ln in self.errors if name in ln]

    def test_bad_archive_exits_1(self):
        self.assertEqual(self.code, 1, self.out)

    def test_legacy_rows_are_info_not_error(self):
        self.assertEqual(self.errors_for("beta"), [], self.out)
        self.assertIn("INFO   [archive] em-dash or middle dot in row: beta.tsv:4", self.out)

    def test_tab_separated_row_parses(self):
        self.assertEqual(self.errors_for("gamma"), [], self.out)

    def test_shifted_columns_are_flagged(self):
        errs = self.errors_for("delta")
        self.assertTrue(any("archetype label 's01-shifted-row'" in e for e in errs), self.out)
        self.assertTrue(any("slug 'D' is not lowercase kebab-case" in e for e in errs), self.out)

    def test_tab_shard_with_stray_pipe_keeps_its_fields(self):
        errs = self.errors_for("zeta.tsv")
        self.assertEqual(errs, ["ERROR  [archive] zeta.tsv:5: '|' inside the task text"], self.out)

    def test_truncated_prompt_is_flagged(self):
        errs = self.errors_for("epsilon/2026-10-05-slice-s01-truncated.md")
        self.assertTrue(any("the full prompt is missing" in e for e in errs), self.out)
        self.assertTrue(any("no self-check table" in e for e in errs), self.out)


class ProfileFreshness(unittest.TestCase):
    """§2.9: freshness is the file@sha stamps; doctor (which cannot run git in the repo) only
    enforces the 90-day ceiling, so a 30-day-old card that used to WARN at 14 days is now valid."""

    def run_with_cards(self, ages: dict[str, int]) -> str:
        import datetime as _dt
        with tempfile.TemporaryDirectory() as tmp:
            shards = Path(tmp) / "generated-prompts" / "by-repo"
            shards.mkdir(parents=True)
            for key, age in ages.items():
                (shards / f"{key}.tsv").write_text(
                    f"# genprompt shard: {key}  (path: /srv/{key})\n# Fields: date | archetype | slug | file | task\n"
                    "# schema: v3\n", encoding="utf-8")
                derived = (_dt.date.today() - _dt.timedelta(days=age)).isoformat()
                (shards / f"{key}.profile.md").write_text(
                    f"---\nrepo: {key}\npath: /srv/{key}\nkey: {key}\nderived: {derived}\n"
                    f"stamp: package.json@abc1234 ; CLAUDE.md@def5678\n---\nstack: x\n", encoding="utf-8")
            _code, out = run_tool(DOCTOR, "--archive", home=Path(tmp))
        return out

    def test_card_within_the_ceiling_is_valid(self):
        out = self.run_with_cards({"thirty": 30, "eightynine": 89})
        self.assertNotIn("days old", out, out)
        self.assertIn("Summary: 0 ERROR, 0 WARN", out)

    def test_card_past_the_ceiling_warns(self):
        out = self.run_with_cards({"old": 100})
        self.assertIn("profile old.profile.md is 100 days old, past the 90-day ceiling", out)
        self.assertNotIn("ERROR  [archive] profile", out)


def load_doctor():
    spec = importlib.util.spec_from_file_location("doctor_under_test", DOCTOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Separator(unittest.TestCase):
    def test_separator_is_chosen_per_shard(self):
        doc = load_doctor()
        tab = ["# schema: v3", "2026-10-01\tD\ta\tf.md\tx", "2026-10-02\tD\tb\tf.md\ty | z"]
        pipe = ["# schema: v3", "2026-10-01 | D | a | f.md | x"]
        self.assertEqual(doc.shard_separator(tab), "\t")
        self.assertEqual(doc.shard_separator(pipe), "|")
        self.assertEqual(doc.shard_separator(["# only comments"]), "|")
        self.assertEqual(len(doc.split_row(tab[2], "\t")), 5)


class ReleaseSync(unittest.TestCase):
    """check_release against a temporary copy of the manifests and CHANGELOG."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        shutil.copytree(ROOT / ".claude-plugin", self.root / ".claude-plugin")
        shutil.copy2(ROOT / "CHANGELOG.md", self.root / "CHANGELOG.md")
        self.doc = load_doctor()
        self.count = len(self.doc.load_build_shims().ARCHETYPES)

    def tearDown(self):
        self._tmp.cleanup()

    def errors(self) -> list[str]:
        self.doc.findings.clear()
        self.doc.check_release(self.root, self.count)
        return [msg for sev, _area, msg in self.doc.findings if sev == "ERROR"]

    def edit_json(self, name: str, fn) -> None:
        path = self.root / ".claude-plugin" / name
        data = json.loads(path.read_text(encoding="utf-8"))
        fn(data)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def test_repo_versions_agree(self):
        self.assertEqual(self.errors(), [])

    def test_unreleased_heading_is_skipped(self):
        log = self.root / "CHANGELOG.md"
        text = log.read_text(encoding="utf-8")
        if "## Unreleased" not in text:
            text = text.replace("\n## ", "\n## Unreleased\n\n- a pending change\n\n## ", 1)
            log.write_text(text, encoding="utf-8")
        self.assertEqual(self.errors(), [])

    def test_plugin_version_mismatch_is_an_error(self):
        self.edit_json("plugin.json", lambda d: d.update(version="9.9.9"))
        errs = self.errors()
        self.assertTrue(errs and all("version mismatch" in e for e in errs), errs)
        self.assertTrue(any("marketplace.json metadata.version" in e for e in errs), errs)

    def test_marketplace_entry_mismatch_names_both_places(self):
        self.edit_json("marketplace.json", lambda d: d["plugins"][0].update(version="0.0.1"))
        errs = self.errors()
        self.assertEqual(len(errs), 1, errs)
        self.assertIn(".claude-plugin/plugin.json version", errs[0])
        self.assertIn("plugins[0].version is 0.0.1", errs[0])

    def test_changelog_mismatch_is_an_error(self):
        log = self.root / "CHANGELOG.md"
        # bump the top released heading, whatever the current release is
        log.write_text(re.sub(r"^## \d+\.\d+\.\d+", "## 9.9.9", log.read_text(encoding="utf-8"), count=1,
                              flags=re.M), encoding="utf-8")
        errs = self.errors()
        self.assertTrue(any("CHANGELOG.md top released heading is 9.9.9" in e for e in errs), errs)

    def test_archetype_count_claim_must_match_table(self):
        self.edit_json("plugin.json",
                       lambda d: d.update(description=d["description"].replace(
                           f"{self.count} archetypes", f"{self.count + 1} archetypes")))
        errs = self.errors()
        self.assertEqual(len(errs), 1, errs)
        self.assertIn(f"says {self.count + 1} archetypes", errs[0])


class ProtocolSize(unittest.TestCase):
    """E-09c: a suite WARN once PROTOCOL.md passes the core budget."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "PROTOCOL.md"
        self.doc = load_doctor()

    def tearDown(self):
        self._tmp.cleanup()

    def warns(self, size: int) -> list[str]:
        self.path.write_bytes(b"x" * size)
        self.doc.findings.clear()
        self.doc.check_protocol_size(self.path)
        return [msg for sev, _area, msg in self.doc.findings if sev == "WARN"]

    def test_at_the_budget_is_quiet(self):
        self.assertEqual(self.warns(self.doc.PROTOCOL_MAX_BYTES), [])

    def test_over_the_budget_warns(self):
        msgs = self.warns(self.doc.PROTOCOL_MAX_BYTES + 1)
        self.assertEqual(len(msgs), 1, msgs)
        self.assertIn("core budget", msgs[0])


class Suite(unittest.TestCase):
    def test_suite_passes_on_this_repo(self):
        code, out = run_tool(DOCTOR, "--suite")
        self.assertEqual(error_lines(out), [], out)
        self.assertEqual(code, 0, out)

    def test_unknown_argument_exits_2(self):
        code, _out = run_tool(DOCTOR, "--nope")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
