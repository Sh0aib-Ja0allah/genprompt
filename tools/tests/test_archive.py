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
         "task": "Slice S02: add the settings page", "flags": "-", "via": "cwd", "lock": "accepted",
         "body": BODY}
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

    def test_existing_file_is_refused_without_replace(self):
        self.assertEqual(self.run_archive(parts())[0], 0)
        before = (self.shard.read_text(encoding="utf-8"), self.file.read_text(encoding="utf-8"))
        code, out = self.run_archive(parts(task="a second try"))
        self.assertEqual(code, 3, out)
        self.assertIn("REFUSED", out)
        self.assertEqual((self.shard.read_text(encoding="utf-8"), self.file.read_text(encoding="utf-8")), before)

    def test_dry_run_writes_nothing(self):
        code, out = self.run_archive(parts(), "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("DRY RUN: nothing written.", out)
        self.assertIn("row          2026-10-07 | D | s02-lint-pass", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_lint_failure_still_writes_then_exits_1(self):
        # write first, then validate: a printed prompt must never be missing from the archive
        bad = BODY.split("| # | Item |")[0]                    # no self-check table
        code, out = self.run_archive(parts(body=bad))
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL  self-check", out)
        self.assertIn("ARCHIVED WITH ERRORS", out)
        self.assertTrue(self.file.exists())
        self.assertEqual(len(self.data_rows()), 1)

    def test_warnings_alone_archive_with_exit_0(self):
        code, out = self.run_archive(parts(body=BODY.replace("Start with CHECKPOINT A now.", "Thanks.")))
        self.assertEqual(code, 0, out)
        self.assertIn("WARN  terminal-imperative", out)
        self.assertIn("(1 warning(s))", out)

    def test_replace_fixes_a_flagged_file_in_place(self):
        bad = BODY.split("| # | Item |")[0]
        self.assertEqual(self.run_archive(parts(body=bad))[0], 1)
        code, out = self.run_archive(parts(task="Slice S02, fixed"), "--replace")
        self.assertEqual(code, 0, out)
        self.assertIn("(replaced)", out)
        self.assertEqual(self.file.read_text(encoding="utf-8"), PASS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(self.data_rows(), ["2026-10-07 | D | s02-lint-pass | 2026-10-07-slice-s02-lint-pass.md | "
                                            "Slice S02, fixed"])

    def test_replace_never_duplicates_the_row(self):
        self.assertEqual(self.run_archive(parts(slug="s01-first", task="first"))[0], 0)
        self.assertEqual(self.run_archive(parts())[0], 0)
        self.assertEqual(self.run_archive(parts(slug="s03-third", task="third"))[0], 0)
        for _ in range(2):
            self.assertEqual(self.run_archive(parts(task="again"), "--replace")[0], 0)
        rows = self.data_rows()
        self.assertEqual(len(rows), 3, rows)
        self.assertEqual(sum(1 for r in rows if "2026-10-07-slice-s02-lint-pass.md" in r), 1)
        self.assertTrue(rows[1].endswith("| again"), rows)        # rewritten in place, order kept

    def test_replace_on_a_new_file_just_archives_it(self):
        code, out = self.run_archive(parts(), "--replace")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(self.data_rows()), 1)

    def test_task_is_normalised_not_refused(self):
        code, out = self.run_archive(parts(task="has a | pipe and an em—dash " + "x" * 220))
        self.assertEqual(code, 0, out)
        self.assertIn("WARN  task  replaced '|'", out)
        task = self.data_rows()[0].split(" | ", 4)[4]
        self.assertLessEqual(len(task), 200)
        self.assertNotIn("|", task)

    def test_bad_structural_field_exits_2_and_writes_nothing(self):
        code, out = self.run_archive(parts(slug="Not A Slug"))
        self.assertEqual(code, 2, out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_22_and_23_row_self_checks_are_accepted_by_archive_and_doctor(self):
        # E-08 appends row 23; every prompt archived before it has 22 rows. Both stay valid.
        head = BODY.split("| # | Item |")[0]
        for rows in (22, 23):
            table = "| # | Item | Verdict | Reason |\n|---|---|---|---|\n" + "".join(
                f"| {n} | item {n} | PASS | reason {n} |\n" for n in range(1, rows + 1))
            code, out = self.run_archive(parts(body=head + table, slug=f"s02-rows-{rows}"))
            self.assertEqual(code, 0, out)
            self.assertIn("PASS  self-check", out)
        code, out = run_tool(DOCTOR, "--archive", home=self.home)
        self.assertEqual(error_lines(out), [], out)

    def test_status_row_writes_only_the_shard(self):
        code, out = self.run_archive({"key": "lint-demo", "path": "/srv/repos/lint-demo", "date": "2026-10-08",
                                      "archetype": "none", "slug": "s02-closeout",
                                      "task": "status: verified, no prompt emitted; abc1234"})
        self.assertEqual(code, 0, out)
        self.assertEqual(self.data_rows(), ["2026-10-08 | none | s02-closeout | - | "
                                            "status: verified, no prompt emitted; abc1234"])
        self.assertFalse((self.arch / "lint-demo").exists())

    def test_missing_or_unknown_vocabulary_warns_but_archives(self):
        data = parts(via="guess")
        data.pop("lock")
        code, out = self.run_archive(data)
        self.assertEqual(code, 0, out)
        self.assertIn("WARN  header-vocab", out)
        self.assertIn("lock missing", out)
        self.assertIn("via=guess is not argument|continuation|cwd|ask", out)
        self.assertTrue(self.file.exists())

    def test_doctor_stats_count_via_lock_and_flags(self):
        runs = [("s10-a", "--go --brief", "argument", "go"),
                ("s11-b", "-", "cwd", "accepted"),
                ("s12-c", "--verbose", "continuation", "corrected"),
                ("s13-d", "--unattended", "cwd", "accepted")]
        for slug, flags, via, lock in runs:
            self.assertEqual(self.run_archive(parts(slug=slug, flags=flags, via=via, lock=lock))[0], 0)
        old = parts(slug="s09-old")
        for k in ("flags", "via", "lock"):
            old.pop(k)
        self.assertEqual(self.run_archive(old)[0], 0)          # a pre-E-05 style header
        code, out = run_tool(DOCTOR, "--archive", home=self.home)
        self.assertEqual(error_lines(out), [], out)
        self.assertIn("Measured (flags/via/lock in the header): 4 file(s); 1 older file(s) predate the fields", out)
        self.assertIn("via:   argument 1, continuation 1, cwd 2", out)
        self.assertIn("lock:  go 1, accepted 2, corrected 1; correction rate 33% of 3 confirmed locks", out)
        self.assertIn("flags: --go 1/4, --brief 1/4, --dry-run 0/4, --verbose 1/4, --unattended 1/4", out)
        self.assertNotIn("WARN", out.split("Summary:")[0])         # old headers are never flagged

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
