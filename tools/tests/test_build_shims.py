"""build_shims.py --check: passes on the repo, fails on an altered or extra command file.

Alterations happen in a temporary copy of tools/ and commands/, never in the repo's commands/.
"""
from __future__ import annotations

import importlib.util
import re
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
        shutil.copytree(ROOT / "archetypes", self.copy / "archetypes")  # excerpts derive from them
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

    def test_only_the_four_utilities_hide_from_model_invocation(self):
        # E-02b: doctor, learn, history and profile stay typeable but leave the model's listing;
        # every other command (help and all archetypes included) must stay visible.
        hidden = sorted(p.stem for p in (ROOT / "commands").glob("*.md")
                        if "\ndisable-model-invocation: true\n" in p.read_text(encoding="utf-8").split("\n---\n", 1)[0] + "\n")
        self.assertEqual(hidden, ["doctor", "history", "learn", "profile"])

    def test_archive_grant_on_every_prompt_emitting_command_only(self):
        # E-04b: Step 6 archives through tools/archive.py, so every archetype shim and :auto may
        # run it (python3 and python, quoted and unquoted); the utilities emit no prompt.
        bs = load_build_shims()
        expected = sorted([a[1] for a in bs.ARCHETYPES] + [bs.ENTRY])
        granted = []
        for p in (ROOT / "commands").glob("*.md"):
            fm = p.read_text(encoding="utf-8").split("\n---\n", 1)[0]
            if "tools/archive.py" in fm:
                granted.append(p.stem)
                for py in ("python3", "python"):
                    self.assertIn(f"Bash({py} ${{CLAUDE_PLUGIN_ROOT}}/tools/archive.py:*)", fm, p.name)
                    self.assertIn(f'Bash({py} "${{CLAUDE_PLUGIN_ROOT}}/tools/archive.py":*)', fm, p.name)
        self.assertEqual(sorted(granted), expected)

    def test_tables_have_no_duplicates(self):
        self.assertEqual(load_build_shims().table_errors(), [])

    # E-09a: per-archetype excerpts of guide/03-blocks.md, @-included by each archetype shim.
    def test_excerpts_contain_every_insert_and_the_common_blocks(self):
        bs = load_build_shims()
        self.assertEqual(bs.excerpt_errors(), [])
        insert = re.compile(r"\[INSERT §(4\.\d+)")
        for r in bs.ARCHETYPES:
            text = (ROOT / "archetypes" / f"{r.stem}.md").read_text(encoding="utf-8")
            excerpt = (ROOT / "guide" / "blocks" / f"{r.stem}.md").read_text(encoding="utf-8")
            heads = set(re.findall(r"^### (4\.\d+) ", excerpt, re.M))
            for sec in set(insert.findall(text)) | set(bs.COMMON_BLOCKS):
                self.assertIn(sec, heads, f"{r.stem}: §{sec} missing from its excerpt")

    def test_excerpt_sections_match_03_blocks_byte_for_byte(self):
        bs = load_build_shims()
        src = bs.block_sections()
        for r in bs.ARCHETYPES:
            excerpt = (ROOT / "guide" / "blocks" / f"{r.stem}.md").read_text(encoding="utf-8")
            for sec in bs.excerpt_ids(r):
                self.assertIn(src[sec].rstrip("\n") + "\n", excerpt, f"{r.stem}: §{sec} differs")

    def test_every_archetype_shim_includes_its_excerpt(self):
        bs = load_build_shims()
        for r in bs.ARCHETYPES:
            shim = (ROOT / "commands" / f"{r.cmd}.md").read_text(encoding="utf-8")
            self.assertIn(f"@${{CLAUDE_PLUGIN_ROOT}}/guide/blocks/{r.stem}.md\n", shim, r.cmd)

    def test_check_fails_on_altered_excerpt(self):
        ex = self.copy / "guide" / "blocks" / "D-slice.md"
        ex.write_text(ex.read_text(encoding="utf-8") + "hand edit\n", encoding="utf-8", newline="\n")
        code, out = run_tool(self.script, "--check", cwd=self.copy)
        self.assertEqual(code, 1, out)
        self.assertIn("DIFF  guide/blocks/D-slice.md", out)

    def test_check_fails_when_no_414_insert_names_the_report_line(self):
        # E-10: one [INSERT §4.14 …] line per template must name GENPROMPT-REPORT.
        arch = self.copy / "archetypes" / "L-fix.md"
        text = arch.read_text(encoding="utf-8")
        self.assertIn("GENPROMPT-REPORT", text)
        arch.write_text(text.replace("GENPROMPT-REPORT", "report"), encoding="utf-8", newline="\n")
        code, out = run_tool(self.script, "--check", cwd=self.copy)
        self.assertEqual(code, 1, out)
        self.assertIn("L-fix.md: no [INSERT §4.14 …] line names GENPROMPT-REPORT", out)


if __name__ == "__main__":
    unittest.main()
