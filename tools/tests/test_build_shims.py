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


def load_tool(name):
    spec = importlib.util.spec_from_file_location(f"{name}_under_test",
                                                  ROOT / "tools" / f"{name}.py")
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
        # Verbatim, except §4.20 (named rows only) and §4.21 (own tier row only): those keep every
        # other line byte for byte, and each kept row is a line of 03-blocks.
        bs = load_build_shims()
        src = bs.block_sections()
        for r in bs.ARCHETYPES:
            excerpt = (ROOT / "guide" / "blocks" / f"{r.stem}.md").read_text(encoding="utf-8")
            for sec in bs.excerpt_ids(r):
                if sec in (bs.SITUATIONAL, bs.LENGTH):
                    part = bs.excerpt_section(r, sec, src[sec])
                    self.assertIn(part.rstrip("\n") + "\n", excerpt, f"{r.stem}: §{sec} differs")
                    self.assertTrue(set(part.splitlines()) <= set(src[sec].splitlines()), r.stem)
                else:
                    self.assertIn(src[sec].rstrip("\n") + "\n", excerpt, f"{r.stem}: §{sec} differs")

    # E-09d: §4.20 rows and §4.21 tiers are cut per archetype.
    def test_situational_rows_and_tier_are_per_archetype(self):
        bs = load_build_shims()
        by_stem = {r.stem: r for r in bs.ARCHETYPES}
        fix = (ROOT / "guide" / "blocks" / "L-fix.md").read_text(encoding="utf-8")
        self.assertIn("| **RECORD, DO NOT ACT** |", fix)
        self.assertNotIn("| **STANDING RULES** |", fix)
        self.assertIn("| Focused | 200 |", fix)
        self.assertNotIn("| Program | 350 |", fix)
        self.assertIn("STANDING RULES", bs.situational_rows(by_stem["I-roadmap"]))
        slice_ = (ROOT / "guide" / "blocks" / "D-slice.md").read_text(encoding="utf-8")
        self.assertIn("| Slice | 260 |", slice_)
        self.assertNotIn("| Focused | 200 |", slice_)

    def test_check_fails_when_an_archetype_names_no_420_row(self):
        arch = self.copy / "archetypes" / "H-commit.md"
        text = arch.read_text(encoding="utf-8")
        arch.write_text(text.replace("§4.20 commit-staging manifest", "§4.20 something unlisted"),
                        encoding="utf-8", newline="\n")
        code, out = run_tool(self.script, "--check", cwd=self.copy)
        self.assertEqual(code, 1, out)
        self.assertIn("H-commit.md names §4.20 but none of its rows", out)

    # E-09d: the compact §6 checklist at the end of every excerpt keeps every row ID of the full
    # table, so the verdict counts (doctor's checklist_rows) stay tied to guide/04-checklist.md.
    def test_compact_checklist_row_ids_equal_the_full_table(self):
        bs = load_build_shims()
        full = bs.checklist_ids()
        self.assertEqual(full, list(range(1, 24)))
        self.assertEqual(sorted(bs.CHECK_COMPACT), full)
        for r in bs.ARCHETYPES:
            excerpt = (ROOT / "guide" / "blocks" / f"{r.stem}.md").read_text(encoding="utf-8")
            tail = excerpt[excerpt.index("## §6 Emission checklist (compact"):]
            ids = [int(n) for n in re.findall(r"^\|\s*(\d+)\s*\|", tail, re.M)]
            self.assertEqual(ids, full, r.stem)

    def test_doctor_checklist_rows_still_counts_23(self):
        spec = importlib.util.spec_from_file_location("doctor_under_test", ROOT / "tools" / "doctor.py")
        doc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(doc)
        self.assertEqual(doc.checklist_rows(), 23)

    def test_check_fails_when_compact_checklist_drifts(self):
        full = self.copy / "guide" / "04-checklist.md"
        text = full.read_text(encoding="utf-8")
        full.write_text(text.replace("| 23 | Every TRAP", "| 24 | Every TRAP"), encoding="utf-8", newline="\n")
        code, out = run_tool(self.script, "--check", cwd=self.copy)
        self.assertEqual(code, 1, out)
        self.assertIn("CHECK_COMPACT rows", out)

    # E-09d: card-less derivation reads guide/blocks/derive.md (§2.0 + the §2.9 card template).
    def test_derive_excerpt_carries_20_and_the_card_template(self):
        bs = load_build_shims()
        self.assertEqual(bs.derive_errors(), [])
        derive = (ROOT / "guide" / "blocks" / "derive.md").read_text(encoding="utf-8")
        secs = bs.profile_sections()
        self.assertIn(secs["2.0"].rstrip("\n") + "\n", derive)
        self.assertIn("```markdown\n---\nrepo:", derive)
        for later in ("### 2.5 ", "### 2.6 ", "### 2.7 "):
            self.assertNotIn(later, derive)
        self.assertLess(len(derive.encode("utf-8")), 6_000)

    def test_check_fails_when_20_exclude_copy_drifts(self):
        prof = self.copy / "guide" / "01-target-profile.md"
        text = prof.read_text(encoding="utf-8")
        prof.write_text(text.replace("test-results\n   storage/framework`", "test-results`", 1),
                        encoding="utf-8", newline="\n")
        code, out = run_tool(self.script, "--check", cwd=self.copy)
        self.assertEqual(code, 1, out)
        self.assertIn("the EXCLUDE copy differs from §2.1", out)

    # E-09e: shims with the ARCHIVE grant (archetypes, :auto) read the home from archive.py --where
    # (GENPROMPT_HOME or ~/.genprompt); learn/profile/history have no such grant and keep ls -d ~.
    # E-13: --split <N> is offered by plan and roadmap only, its rules live on demand in §8.1, and
    # the archetypes that take it (and :next, for lane reports) point there.
    def test_split_flag_only_on_plan_and_roadmap(self):
        bs = load_build_shims()
        self.assertEqual(set(bs.SPLIT_CMDS), {"plan", "roadmap"})
        for r in bs.ARCHETYPES:
            shim = (ROOT / "commands" / f"{r.cmd}.md").read_text(encoding="utf-8")
            hint = re.search(r"^argument-hint: (.*)$", shim, re.M).group(1)
            self.assertEqual(bs.SPLIT_FLAG in hint, r.cmd in bs.SPLIT_CMDS, r.cmd)
        root = (ROOT / "commands" / f"{bs.ENTRY}.md").read_text(encoding="utf-8")
        self.assertNotIn("--split", root)

    def test_split_rules_are_on_demand_and_referenced(self):
        grammar = (ROOT / "guide" / "08-grammar.md").read_text(encoding="utf-8")
        self.assertIn("### 8.1 `--split <N>`", grammar)
        self.assertIn("| `--split <N>` |", grammar)
        for stem in ("F-plan", "I-roadmap", "J-next"):
            text = (ROOT / "archetypes" / f"{stem}.md").read_text(encoding="utf-8")
            self.assertIn("§8.1", text, stem)
        self.assertIn("`W<k>/<N>:`", (ROOT / "archetypes" / "J-next.md").read_text(encoding="utf-8"))
        self.assertNotIn("--split", (ROOT / "PROTOCOL.md").read_text(encoding="utf-8"))

    # E-15: the options the prose used to hide are named flags, each only on its own commands,
    # each documented in the grammar's per-command table, and each known to doctor/archive.py.
    def test_per_command_flags_sit_only_on_their_commands(self):
        bs = load_build_shims()
        expected = {"plan": {"--split"}, "roadmap": {"--split"}, "review": {"--chat-only"},
                    "commit": {"--verify", "--pr"}, "security": {"--readonly-phase"},
                    "perf": {"--readonly-phase"}, "next": {"--from"}}
        own = {f for v in bs.CMD_FLAGS.values() for f in re.findall(r"--[a-z-]+", v)}
        grammar = (ROOT / "guide" / "08-grammar.md").read_text(encoding="utf-8")
        table = grammar.split("### Per-command modifiers", 1)[1].split("Auto-go", 1)[0]
        for flag in own:
            self.assertIn(f"| `{flag}", table, flag)
        for r in bs.ARCHETYPES:
            shim = (ROOT / "commands" / f"{r.cmd}.md").read_text(encoding="utf-8")
            hint = re.search(r"^argument-hint: (.*)$", shim, re.M).group(1)
            self.assertEqual(set(re.findall(r"--[a-z-]+", hint)) & own, expected.get(r.cmd, set()),
                             r.cmd)
        doctor = load_tool("doctor")
        self.assertTrue(own <= doctor.known_flags())

    # E-15: the PR step lives on demand in §8.2, so only --pr runs pay for it; H only points there.
    def test_commit_pr_step_is_on_demand_and_body_is_placeholders(self):
        h = (ROOT / "archetypes" / "H-commit.md").read_text(encoding="utf-8")
        self.assertIn("`--pr`: read §8.2", h)
        self.assertNotIn("PR BODY", h)
        self.assertNotIn("§4.23", h)
        self.assertNotIn("### 4.23", (ROOT / "guide" / "blocks" / "H-commit.md").read_text(encoding="utf-8"))
        grammar = (ROOT / "guide" / "08-grammar.md").read_text(encoding="utf-8")
        sec = grammar.split("### 8.2 `--pr`", 1)[1]
        self.assertIn("read §4.23", sec)
        self.assertIn("[INSERT §4.23 APPROVAL PER ACTION", sec)
        body = sec.split("PR BODY (", 1)[1].split("Do not merge the PR", 1)[0]
        for line in body.splitlines():
            if line.strip().startswith("## "):
                self.assertRegex(line, r"\{[^}]+\}", line)
        self.assertIn("No client names, customer data, secrets", body)
        self.assertIn("Do not merge the PR, request reviewers", sec)

    # 1.3.1 T-bare: CP6 judges read `tools/archive.py` in an emitted prompt as a cited file missing
    # from the target repo. Generator-facing text names the tool bare (`archive.py`); only the
    # actual call keeps the plugin-root path. Every archetype carries the bare-name line.
    def test_archive_py_is_never_written_as_a_repo_path(self):
        files = [*sorted((ROOT / "commands").glob("*.md")), *sorted((ROOT / "archetypes").glob("*.md")),
                 *sorted((ROOT / "guide" / "blocks").glob("*.md")), ROOT / "PROTOCOL.md"]
        bad = re.compile(r"(?<!\{CLAUDE_PLUGIN_ROOT\}/)tools/archive\.py")
        for f in files:
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                self.assertIsNone(bad.search(line), f"{f.relative_to(ROOT)}:{n}: {line}")
        for f in sorted((ROOT / "archetypes").glob("[A-Z]-*.md")):
            self.assertIn("Name genprompt's own tools bare (`archive.py`)",
                          f.read_text(encoding="utf-8"), f.name)

    # Privacy (CP7): a generator-filled scratch placeholder made investigate prompts name the
    # generator's own scratchpad/temp dir under the real user home. The scratch area is a worker
    # slot or a contract path, and every archetype with a scratch area carries the rule.
    def test_no_rule_text_sends_the_generator_scratch_or_temp_path_into_the_prompt(self):
        files = [*sorted((ROOT / "commands").glob("*.md")), *sorted((ROOT / "archetypes").glob("*.md")),
                 *sorted((ROOT / "guide" / "blocks").glob("*.md")), ROOT / "PROTOCOL.md"]
        placeholder = re.compile(r"<(scratch|temp|tmp)[ _-]?(path|dir|area|folder)>", re.I)
        env_path = re.compile(r"AppData|%TEMP%|\$TMPDIR|\$\{?TEMP\b|(?<![\w.])/tmp/|scratchpad/", re.I)
        for f in files:
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                where = f"{f.relative_to(ROOT)}:{n}: {line}"
                self.assertIsNone(placeholder.search(line), where)
                self.assertIsNone(env_path.search(line), where)
                if "scratchpad" in line.lower():
                    self.assertIn("Never write a path from your own environment", line, where)
        rule = "Never write a path from your own environment (your scratchpad, temp dir or home)"
        for f in sorted((ROOT / "archetypes").glob("[A-Z]-*.md")):
            text = f.read_text(encoding="utf-8")
            if "scratch dir" in text or "scratch path" in text:
                self.assertIn(rule, text, f.name)
                self.assertIn("{scratch dir}", text, f.name)

    # LOCK-UL (1.4.0): CP7 found the user-level CLAUDE.md path (the user's home) in TARGET LOCK
    # Ancestors lines, a card slot and grounding notes. Every user-level slot is the enum, and no
    # rule text asks for a user-level path.
    def test_user_level_is_reported_present_unreadable_none_never_a_path(self):
        files = [*sorted((ROOT / "commands").glob("*.md")), *sorted((ROOT / "archetypes").glob("*.md")),
                 *sorted((ROOT / "guide").glob("*.md")), *sorted((ROOT / "guide" / "blocks").glob("*.md")),
                 *sorted((ROOT / "utilities").glob("*.md")), ROOT / "PROTOCOL.md"]
        slot = re.compile(r"user-level:\s*(<[^>]*>|`?\S+)")
        seen = {"lock": False, "card": False, "grounding": False}
        for f in files:
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                where = f"{f.relative_to(ROOT)}:{n}: {line}"
                self.assertNotRegex(line, r"user-level:\s*<[^>]*\bpath\b", where)
                for m in slot.finditer(line):
                    val = m.group(1).rstrip(",.;").strip("`")
                    self.assertIn(val, ("<present | unreadable | none>", "present"), where)
                if line.startswith("Ancestors ") and "user-level:" in line:
                    seen["lock"] = True
                if line.startswith("ancestors:") and "user-level:" in line:
                    seen["card"] = True
                if "User-level is" in line and f.parent.name == "blocks":
                    seen["grounding"] = True
        self.assertEqual(seen, {"lock": True, "card": True, "grounding": True})
        derive = (ROOT / "guide" / "blocks" / "derive.md").read_text(encoding="utf-8")
        self.assertIn("never its path", derive)

    # 1.3.1 C1: --where names the cwd repo's card, and Step 0 reads it before any repo survey.
    def test_step0_reads_the_card_before_any_repo_survey(self):
        bs = load_build_shims()
        for cmd in [r.cmd for r in bs.ARCHETYPES] + [bs.ENTRY]:
            shim = (ROOT / "commands" / f"{cmd}.md").read_text(encoding="utf-8")
            self.assertIn("then `card` if `present`, before any repo survey or derive.md.", shim, cmd)

    def test_step0_home_comes_from_archive_where_under_the_archive_grant(self):
        bs = load_build_shims()
        where = ('First Bash call, alone and unchained: '
                 '`python3 "${CLAUDE_PLUGIN_ROOT}/tools/archive.py" --where`.')
        for cmd in [r.cmd for r in bs.ARCHETYPES] + [bs.ENTRY]:
            shim = (ROOT / "commands" / f"{cmd}.md").read_text(encoding="utf-8")
            self.assertIn(where, shim, cmd)
            self.assertIn("once more with `python`, alone.", shim, cmd)
            self.assertIn("Then git and other reads, one per call.", shim, cmd)
            # the exact call Step 0 names is pre-approved (no new grant: G1)
            self.assertIn('Bash(python3 "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*)', shim, cmd)
            self.assertIn('Bash(python "${CLAUDE_PLUGIN_ROOT}/tools/archive.py":*)', shim, cmd)
            self.assertNotIn("ls -d ~", shim, cmd)
            # CP6 run 3: a chained first call lost --where and the card, so Step 0 chains nothing
            step0 = re.search(r"^Step 0:.*$", shim, re.M).group(0)
            for op in ("&&", "||", ";", "|"):
                self.assertNotIn(op, step0, (cmd, op))
        for cmd in ("learn", "profile", "history"):
            shim = (ROOT / "commands" / f"{cmd}.md").read_text(encoding="utf-8")
            self.assertIn("`ls -d ~ ~/.genprompt/local-rules.md` once", shim, cmd)
            self.assertNotIn("archive.py --where", shim, cmd)

    # E-12: exactly the prompt-emitting commands (every archetype in ARCHETYPES, plus :auto) carry
    # ListAgents and offer --send; no utility does. SendMessage is pre-approved nowhere, so the
    # harness asks before every send (review HIGH). Counts come from the table, not literals.
    def test_dispatch_grant_is_on_exactly_the_emitting_commands(self):
        bs = load_build_shims()
        emitters = {r.cmd for r in bs.ARCHETYPES} | {bs.ENTRY}
        carriers = set()
        for path in sorted((ROOT / "commands").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            tools = re.search(r"^allowed-tools:(.*)$", text, re.M).group(1)
            hint = re.search(r"^argument-hint:(.*)$", text, re.M).group(1)
            granted = {t.strip() for t in tools.split(",")}
            self.assertNotIn("SendMessage", text.split("\n---", 1)[0], path.name)
            if "ListAgents" in granted:
                self.assertIn("[--send <session>]", hint, path.name)
                carriers.add(path.stem)
            else:
                self.assertNotIn("--send", hint, path.name)
        self.assertEqual(carriers, emitters)
        self.assertEqual(len(carriers), len(bs.ARCHETYPES) + 1)
        self.assertIn("--send", bs.FLAGS_RO)

    def test_investigate_excerpt_has_its_blocks(self):
        # E-14: archetype X needs the defect chain, falsifiability and the findings register.
        excerpt = (ROOT / "guide" / "blocks" / "X-investigate.md").read_text(encoding="utf-8")
        heads = set(re.findall(r"^### (4\.\d+) ", excerpt, re.M))
        for sec in ("4.9", "4.13", "4.14", "4.15", "4.20", "4.25"):
            self.assertIn(sec, heads, f"§{sec} missing from the X excerpt")

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
