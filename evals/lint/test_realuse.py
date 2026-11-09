"""realuse/run.py: A5 treats only content-free outside results as harmless.

    python -m unittest discover -s evals/lint
"""
from __future__ import annotations

import re
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
        # CP6 ruling: what the shims grant is not denied; builtins no shim grants are
        for c in ("cd", "ls", "head", "tail", "wc", "git diff", "git grep", "git config"):
            self.assertNotIn(f"Bash({c}:*)", cand)
        self.assertIn("Bash(cat:*)", cand)
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
            real, run.HOME = run.HOME, Path("C:/Users/nobody-here")  # tmp is under the real home
            try:
                out = run.analyze(trace, work / "gp-cand", work)["outside"]
            finally:
                run.HOME = real
        self.assertEqual(len(out), 2, out)
        self.assertIn("<other project>", out[0][2])      # call 4: a leaked name
        self.assertEqual(out[1][1], "C:/Windows")         # call 5: not a drive root, by path


class CardGateTest(unittest.TestCase):
    """CP6 R2: card-fresh gates C1 (no derivation Reads) and C2 (≤ card-less + card bytes)."""

    def test_forbidden_files_exist(self):
        root = Path(__file__).resolve().parents[2]
        for rel in run.CARD_FORBIDDEN:
            self.assertTrue((root / rel).is_file(), rel)

    def test_parse_cardless(self):
        self.assertEqual(run.parse_cardless(["slice=32,178", "fix=31530"]),
                         {"slice": 32178.0, "fix": 31530.0})
        for bad in (["slice"], ["nosuch=1"], ["fix=abc"]):
            with self.assertRaises(ValueError):
                run.parse_cardless(bad)

    def test_card_gate(self):
        cl = {"plan": 29853}
        ok, det = run.card_gate("plan", [31000, 30500, 36000], [1500, 1500, 1500], cl)
        self.assertTrue(ok, det)                      # 31,000 ≤ 29,853 + 1,500
        ok, det = run.card_gate("plan", [31400, 31400, 29000], [1500] * 3, cl)
        self.assertFalse(ok, det)                     # 31,400 > 31,353
        self.assertFalse(run.card_gate("fix", [1], [1], cl)[0])

    def test_card_mode_needs_cardless_before_spend(self):
        argv = sys.argv
        try:
            for extra in ([], ["--cardless", "slice=1"]):
                sys.argv = ["run.py", "compare", "--cand", "HEAD", "--cases", "slice", "fix",
                            "--home", "card", *extra]
                with self.assertRaises(SystemExit) as cm:
                    run.main()
                self.assertEqual(cm.exception.code, 2)
        finally:
            sys.argv = argv


class InvestigateCaseTest(unittest.TestCase):
    """E-14: the probe request and the eval case for archetype X agree."""

    def test_request_matches_case(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import build_cases
        spec = build_cases.EXTRA["investigate"]
        self.assertEqual(spec["request"], f"/genprompt:investigate {run.REQUESTS['investigate']}")
        self.assertEqual(build_cases.ARCHIVE_META["investigate"], ("X", "investigate"))
        files = build_cases.case_files("investigate", spec)
        self.assertIn("tags: [extra, investigate]", files["prompt.md"])
        self.assertIn(r"?\bX\b'", files["graders/archetype-label.md"])
        self.assertNotIn("\b", "".join(files.values()))   # no backspace from a bad escape

    def test_symptom_is_true_of_the_fixture(self):
        # The request claims per-line amounts 25.00/40.00/5.00 and TOTAL 40.50 vs 63.00 EUR.
        import json
        root = Path(__file__).resolve().parents[1] / "fixtures" / "ledgerlite"
        inv = json.loads((root / "examples" / "sample.json").read_text(encoding="utf-8"))
        lines = [ln["qty"] * ln["unitCents"] for ln in inv["lines"]]
        self.assertEqual(lines, [2500, 4000, 500])
        disc = lambda c: c - round(c * inv["discountPct"] / 100)  # noqa: E731
        self.assertEqual(disc(sum(lines[1:])), 4050)   # the bug: the loop starts at i = 1
        self.assertEqual(disc(sum(lines)), 6300)
        self.assertIn("for (let i = 1;",
                      (root / "src" / "invoice.js").read_text(encoding="utf-8").splitlines()[13])


class ChainRuleTest(unittest.TestCase):
    """CP6 ruling (b): a chain or pipeline is safe only if every part is safe on its own."""
    P = "C:/genprompt-probe"
    ARCH = "python3 C:/genprompt-probe/r/gp-cand/tools/archive.py"

    def ok(self, cmd):
        self.assertTrue(run.safe_bash(cmd, self.P), cmd)

    def bad(self, cmd):
        self.assertFalse(run.safe_bash(cmd, self.P), cmd)

    def test_safe_chains(self):
        self.ok("git branch --show-current; git branch --merged main; git rev-parse --short HEAD")
        self.ok(f"{self.ARCH} --where 2>&1 || python C:/genprompt-probe/r/gp-cand/tools/"
                f"archive.py --where 2>&1; cd \"C:/genprompt-probe/r/fixture\" && git log -1 "
                f"--format=%h && ls -la")
        self.ok('cd "C:/genprompt-probe/r/fixture" && git status --porcelain -uall && ls docs '
                '2>/dev/null')
        self.ok('cd "C:\\genprompt-probe\\r\\fixture" && head -3 package.json && wc -l src/cli.js')
        self.ok("git grep -n discount -- src && git diff HEAD~1 -- src/invoice.js")

    def test_safe_pipelines(self):
        self.ok("git log --oneline | head -20")
        self.ok(f"{self.ARCH} --where 2>&1 | head -5")

    def test_unsafe_part_flags_the_chain(self):
        self.bad(f"{self.ARCH} --where; cat ~/.gitconfig")
        self.bad("git status; npm --version")
        self.bad("git log && echo done")
        self.bad("git log | tee out.txt")
        self.bad("git ls-files | xargs wc -l")
        self.bad("git log | sh")

    def test_redirects(self):
        self.ok("ls docs 2>/dev/null")
        self.ok("git log -1 2>&1")
        self.bad("git log > log.txt")
        self.bad("git log >> log.txt")
        self.bad("wc -l < C:/Users/x/secret.txt")
        self.bad("git log 1>/dev/null")

    def test_subshells_and_substitution(self):
        self.bad(f"({self.ARCH} --where || python x)")
        self.bad("ls $(git rev-parse --show-toplevel)")
        self.bad("ls `pwd`")
        self.bad("{ git log; }")
        self.bad("git log &")

    def test_paths_stay_inside_the_probe(self):
        self.bad('ls "C:/Users/someone"')
        self.bad("ls /c/Users/someone/.genprompt")
        self.bad('cd "C:/Users/someone" && git log')
        self.bad("head -5 C:\\Users\\someone\\.gitconfig")
        self.bad("ls ~")
        self.bad("ls $HOME")
        self.bad("cd ../.. && ls")
        self.bad("cd")             # a bare cd goes to $HOME
        self.bad("git log --git-dir=C:/elsewhere/.git")
        self.bad("ls C:/genprompt-probe-other")   # a sibling prefix is not the probe root
        self.ok("ls C:/genprompt-probe/r/fixture")
        self.ok("ls /c/genprompt-probe/r/fixture")

    def test_v4_trace_commands(self):
        # the V4 trace's chains, judged with the new rule: all safe (paths inside the probe)
        root = "C:/genprompt-probe/genprompt-v4-20261109-094638"
        self.ok(f"python {root}/gp-cand/tools/archive.py --where; git status --porcelain")
        self.ok(f'cd "{root}/fixture" && git status --porcelain && ls -la && head -3 package.json')


class BashRanTest(unittest.TestCase):
    """CP6 ruling: "not run" is only a permission denial or the bare store-alias message."""

    def test_not_run(self):
        for t in ("Permission to use Bash with command ls ~ has been denied.",
                  "Permission to use Bash has been denied because Claude Code is running in "
                  "don't ask mode.",
                  "<tool_use_error>Error: No such tool available: Bash. Bash is disabled",
                  "ls from 'C:\\Users\\x' was blocked by a deny rule.",
                  "Python was not found; run without arguments to install from the Microsoft "
                  "Store, or disable this shortcut from Settings.",
                  "Exit code 49\nPython was not found; run without arguments to install"):
            self.assertFalse(run.bash_ran(t), t)

    def test_ran(self):
        for t in ("Python was not found; run without arguments to install\n"
                  "home C:/genprompt-probe/x/homes/h",       # the fallback ran
                  "File does not exist.\nREADME.md",           # no longer a pass
                  "total 15\n-rw-r--r-- 1 a b 25 Nov 9 .gitignore",
                  "(Bash completed with no output)"):
            self.assertTrue(run.bash_ran(t), t)


class HomeLeakTest(unittest.TestCase):
    """CP6 ruling: A5 flags any tool output that names the real home."""
    H = Path("C:/Users/someone")

    def test_marks(self):
        m = run.home_marks(self.H)
        for s in ("c:/users/someone", "c:\\users\\someone", "/c/users/someone"):
            self.assertIn(s, m)

    def test_shows_home(self):
        m = run.home_marks(self.H)
        for t in ("HOME=/c/Users/someone", "C:\\Users\\someone\\.genprompt\\x.md",
                  '{"path": "C:\\\\Users\\\\someone"}', "c:/users/someone"):
            self.assertTrue(run.shows_home(t, m), t)
        for t in ("C:/Users/someone-else/x", "C:/genprompt-probe/x", "~/.claude/CLAUDE.md",
                  # the harness's own spill notice (CP6 card-less plan r3) is not a leak
                  "<persisted-output>\nOutput too large (34KB). Full output saved to: "
                  "C:\\Users\\someone\\.claude\\projects\\c--x\\abc\\tool-results\\t.txt"):
            self.assertFalse(run.shows_home(t, m), t)
        # ...but only that notice: the same path elsewhere in the output still flags
        self.assertTrue(run.shows_home("Output too large (1KB). Full output saved to: "
                                       "C:\\Users\\someone\\.claude\\projects\\x.txt\n"
                                       "C:\\Users\\someone\\.genprompt\\client-a.md", m))

    def test_analyze_flags_home_output(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp).resolve() / "genprompt-probe" / "run-1"
            work.mkdir(parents=True)

            def call(i, name, inp, result):
                return [json.dumps({"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": f"t{i}", "name": name, "input": inp}]}}),
                    json.dumps({"type": "user", "message": {"content": [
                        {"type": "tool_result", "tool_use_id": f"t{i}", "content": result}]}})]
            lines = (call(1, "Bash", {"command": "git log -1"}, "HOME=/c/Users/someone")
                     + call(2, "Bash", {"command": "ls C:/Users/someone"},
                            "Permission to use Bash with command ls C:/Users/someone has been "
                            "denied.")
                     + call(3, "Read", {"file_path": "C:/Users/someone/.genprompt/x.md"},
                            "<tool_use_error>File is in a directory that is denied by your "
                            "permission settings.</tool_use_error>"))
            trace = work / "t.jsonl"
            trace.write_text("\n".join(lines), encoding="utf-8")
            real, run.HOME = run.HOME, self.H
            try:
                a = run.analyze(trace, work / "gp-cand", work)
            finally:
                run.HOME = real
        bad = [x for x in a["outside"] if not x[2].startswith("denied")]
        self.assertEqual(len(bad), 1, bad)
        self.assertTrue(bad[0][2].startswith("SHOWS REAL HOME"))
        self.assertNotIn("someone", bad[0][2])  # counts only, never the output


class ValidityTest(unittest.TestCase):
    """CP6 validity rule and V1-V3."""

    def test_thresholds(self):
        Y, n = True, False
        ok = {c: [Y, Y, Y] for c in ("slice", "fix", "redesign", "plan")} | {"investigate": [Y, Y, n]}
        self.assertTrue(run.card_validity(ok)["ok"])
        twelve = {"slice": [Y, Y, n], "fix": [Y, Y, n], "redesign": [Y, Y, n],
                  "plan": [Y, Y, Y], "investigate": [Y, Y, Y]}
        v = run.card_validity(twelve)
        self.assertTrue(v["ok"], v)
        self.assertEqual((v["need_total"], v["need_case"]), (12, 2))
        eleven = dict(twelve, plan=[Y, Y, n])
        self.assertFalse(run.card_validity(eleven)["ok"])            # 11 of 15
        one_case_short = dict({c: [Y, Y, Y] for c in twelve}, fix=[Y, n, n])
        v = run.card_validity(one_case_short)                          # 13 of 15, fix 1/3
        self.assertFalse(v["ok"])
        self.assertIn("fix 1/3", v["detail"])
        cp6 = {"slice": [Y, n, n], "fix": [n, n, n], "redesign": [n, n, n],
               "plan": [n, Y, n], "investigate": [n, n, n]}
        self.assertFalse(run.card_validity(cp6)["ok"])                 # the CP6 run: 2 of 15

    def test_card_seen_from_read_or_where(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp).resolve() / "genprompt-probe" / "run-1"
            work.mkdir(parents=True)
            card = (work / "homes" / "h" / "generated-prompts" / "by-repo" /
                    "fixture.profile.md").as_posix()

            def trace(name, inp, result):
                t = work / f"{name}.jsonl"
                t.write_text("\n".join([
                    json.dumps({"type": "assistant", "message": {"content": [
                        {"type": "tool_use", "id": "t1", "name": name, "input": inp}]}}),
                    json.dumps({"type": "user", "message": {"content": [
                        {"type": "tool_result", "tool_use_id": "t1", "content": result}]}})]),
                    encoding="utf-8")
                real, run.HOME = run.HOME, Path("C:/Users/nobody-here")
                try:
                    return run.analyze(t, work / "gp-cand", work)["card_seen"]
                finally:
                    run.HOME = real
            arch = (work / "gp-cand" / "tools" / "archive.py").as_posix()
            self.assertTrue(trace("Read", {"file_path": card}, "1\t---\n2\trepo: fixture"))
            self.assertTrue(trace("Bash", {"command": f"python {arch} --where"},
                                  f"home {(work / 'homes' / 'h').as_posix()}\nlocal-rules x"))
            self.assertFalse(trace("Bash", {"command": f"python {arch} --where; cd x && ls"},
                                   f"Permission to use Bash with command python {arch} has been "
                                   f"denied."))
            self.assertFalse(trace("Glob", {"pattern": "*", "path": card}, card))


class SandboxEnvTest(unittest.TestCase):
    """CP6 ruling (a): HOME, USERPROFILE, XDG and git config point at a per-run sandbox."""

    def test_env_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            env = run.sandbox_env(Path(tmp), "gp-cand-plan-r1")
            script = Path(env["CLAUDE_ENV_FILE"]).read_text(encoding="utf-8")
            prof = (Path(tmp) / "profiles" / "gp-cand-plan-r1").resolve().as_posix()
            for k in ("HOME", "USERPROFILE", "XDG_CONFIG_HOME", "XDG_CACHE_HOME",
                      "XDG_DATA_HOME", "GIT_CONFIG_GLOBAL"):
                self.assertRegex(script, rf"(?m)^export {k}='?{re.escape(prof)}")
            self.assertIn("export GIT_CONFIG_NOSYSTEM=1", script)
            self.assertTrue((Path(prof) / run.PROFILE_MARK).is_file())
            self.assertEqual(env["GIT_CONFIG_NOSYSTEM"], "1")

    def test_isolation_helpers(self):
        grant = run.shim_bash_grant()
        for r in ("Bash(cd:*)", "Bash(ls:*)", "Bash(head:*)", "Bash(git status:*)"):
            self.assertIn(r, grant)
        self.assertTrue(run.real_home_sealed("ls from 'C:\\Users\\x' was blocked by a deny rule."))
        self.assertTrue(run.real_home_sealed(
            "Exit code 2\nls: cannot access 'C:/Users/x/.genprompt': No such file or directory"))
        self.assertFalse(run.real_home_sealed("client-a\nclient-b"))
        self.assertFalse(run.real_home_sealed("[user]\n\tname = x"))
        self.assertTrue(run.sandbox_listing(f".\n..\n.cache\n.config\n.gitconfig\n.local\n"
                                            f"{run.PROFILE_MARK}"))
        self.assertFalse(run.sandbox_listing(f"{run.PROFILE_MARK}\nDesktop\nDocuments"))
        self.assertFalse(run.sandbox_listing("Desktop\nDocuments"))


if __name__ == "__main__":
    unittest.main()
