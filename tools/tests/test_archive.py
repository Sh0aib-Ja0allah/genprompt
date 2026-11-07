"""tools/archive.py: the deterministic archive writer. Every test writes into a temporary
GENPROMPT_HOME, never into ~/.genprompt."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import FIXTURES, ROOT, error_lines, run_tool  # noqa: E402

ARCHIVE_PY = ROOT / "tools" / "archive.py"
DOCTOR = ROOT / "tools" / "doctor.py"
PASS_FILE = FIXTURES / "lint" / "2026-10-07-slice-s02-lint-pass.md"
BODY = PASS_FILE.read_text(encoding="utf-8").split("\n", 1)[1]


def parts(**over) -> dict:
    p = {"key": "lint-demo", "repo": "lint-demo", "path": "/srv/repos/lint-demo",
         "date": "2026-10-07", "archetype": "D", "follows": "-", "slug": "s02-lint-pass",
         "task": "Slice S02: add the settings page", "body": BODY}
    p.update(over)
    return p


class ArchiveWriter(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.arch = self.home / "generated-prompts"
        self.shard = self.arch / "by-repo" / "lint-demo.tsv"
        self.file = self.arch / "lint-demo" / "2026-10-07-slice-s02-lint-pass.md"

    def tearDown(self):
        self._tmp.cleanup()

    def run_archive(self, data: dict, *flags: str) -> tuple[int, str]:
        src = self.home.parent / f"{self.home.name}-parts.json"
        src.write_text(json.dumps(data), encoding="utf-8")
        try:
            return run_tool(ARCHIVE_PY, *flags, str(src), home=self.home)
        finally:
            src.unlink()

    def data_rows(self) -> list[str]:
        return [ln for ln in self.shard.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")]

    def test_new_shard_gets_header_lines_and_a_valid_file(self):
        code, out = self.run_archive(parts())
        self.assertEqual(code, 0, out)
        self.assertIn("ARCHIVED", out)
        lines = self.shard.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "# genprompt shard: lint-demo  (path: /srv/repos/lint-demo)")
        self.assertEqual(lines[2], "# schema: v3")
        self.assertEqual(lines[3], "2026-10-07 | D | s02-lint-pass | 2026-10-07-slice-s02-lint-pass.md | "
                                   "Slice S02: add the settings page")
        self.assertEqual(self.file.read_text(encoding="utf-8"), PASS_FILE.read_text(encoding="utf-8"))
        # doctor agrees: the per-file lint and the whole-archive check are both clean
        code, out = run_tool(DOCTOR, "--prompt", str(self.file))
        self.assertEqual(code, 0, out)
        code, out = run_tool(DOCTOR, "--archive", home=self.home)
        self.assertEqual(error_lines(out), [], out)

    def test_existing_shard_appends_below_the_last_line(self):
        self.assertEqual(self.run_archive(parts())[0], 0)
        code, out = self.run_archive(parts(slug="s03-next", task="Slice S03"))
        self.assertEqual(code, 0, out)
        self.assertEqual(len(self.data_rows()), 2)
        self.assertTrue(self.data_rows()[1].startswith("2026-10-07 | D | s03-next | 2026-10-07-slice-s03-next.md"))
        self.assertEqual(self.shard.read_text(encoding="utf-8").count("# schema: v3"), 1)

    def test_legacy_shard_row_goes_below_the_marker(self):
        self.shard.parent.mkdir(parents=True)
        self.shard.write_text("# genprompt shard: lint-demo  (path: x)\n# Fields: d\n"
                              "# schema: legacy rows first; v3 rows go below the marker line at the end of this file\n"
                              "2026-06-01 | slice | old | - | old row\n# --- v3 ---", encoding="utf-8")
        code, out = self.run_archive(parts())
        self.assertEqual(code, 0, out)
        lines = self.shard.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[-2], "# --- v3 ---")
        self.assertTrue(lines[-1].startswith("2026-10-07 | D | s02-lint-pass"))

    def test_existing_file_is_refused(self):
        self.assertEqual(self.run_archive(parts())[0], 0)
        before = self.shard.read_text(encoding="utf-8")
        code, out = self.run_archive(parts(task="a second try"))
        self.assertEqual(code, 3, out)
        self.assertIn("REFUSED", out)
        self.assertEqual(self.shard.read_text(encoding="utf-8"), before)

    def test_dry_run_writes_nothing(self):
        code, out = self.run_archive(parts(), "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("DRY RUN: nothing written.", out)
        self.assertIn("row          2026-10-07 | D | s02-lint-pass", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_lint_failure_exits_1_and_writes_nothing(self):
        bad = BODY.replace("Start with CHECKPOINT A now.", "Thanks.")
        code, out = self.run_archive(parts(body=bad))
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL  terminal-imperative", out)
        self.assertIn("NOT ARCHIVED", out)
        self.assertNotIn("ARCHIVED  ", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_bad_task_field_exits_1(self):
        code, out = self.run_archive(parts(task="has a | pipe"))
        self.assertEqual(code, 1, out)
        self.assertIn("task contains '|'", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_status_row_writes_only_the_shard(self):
        code, out = self.run_archive({"key": "lint-demo", "path": "/srv/repos/lint-demo", "date": "2026-10-08",
                                      "archetype": "none", "slug": "s02-closeout",
                                      "task": "status: verified, no prompt emitted; abc1234"})
        self.assertEqual(code, 0, out)
        self.assertEqual(self.data_rows(), ["2026-10-08 | none | s02-closeout | - | "
                                            "status: verified, no prompt emitted; abc1234"])
        self.assertFalse((self.arch / "lint-demo").exists())

    def test_optional_header_fields_are_written_in_order(self):
        code, out = self.run_archive(parts(lock="go", flags="--go", via="cwd"))
        self.assertEqual(code, 0, out)
        first = self.file.read_text(encoding="utf-8").splitlines()[0]
        self.assertTrue(first.endswith("| follows=- | flags=--go | via=cwd | lock=go -->"), first)

    def test_parts_on_stdin(self):
        head, rest = BODY.split("````text", 1)
        prompt, self_check = rest.split("````\n", 1)
        data = parts(body=None, header_table=head.strip(), prompt="````text" + prompt + "````",
                     self_check=self_check.strip())
        data.pop("body")
        env = dict(os.environ, GENPROMPT_HOME=str(self.home), PYTHONIOENCODING="utf-8")
        proc = subprocess.run([sys.executable, str(ARCHIVE_PY), "-"], input=json.dumps(data), env=env,
                              capture_output=True, encoding="utf-8", check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(self.file.exists())


if __name__ == "__main__":
    unittest.main()
