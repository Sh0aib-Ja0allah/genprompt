"""CP9 (1.4.1) pre-freeze eval changes, evals/CP9-plan.md §1: F-2 to F-5, F-7 and P-5.
(F-6, the report-line check, is in test_structural.ReportLineTest; F-1's Z-3 tests are in
test_jmethod.AutoExplainTest.)

    python -m unittest discover -s evals/lint
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "realuse"))

import run  # noqa: E402

DOT = "\u00b7"


def write_card(home: Path, fx: Path, stamp: str) -> Path:
    p = run.card_path(home, fx)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\nrepo:     {fx.name}\nstamp:    {stamp}\n---\nbranch:  main\n", encoding="utf-8")
    return p


class FixtureCase(unittest.TestCase):
    """One git fixture and one no-git fixture for the whole class (the scaffold takes a moment)."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        cls.git_fx = run.fixture(root / "g")
        cls.nogit_fx = run.fixture(root / "n")
        run.strip_git(cls.nogit_fx)
        cls.home = root / "home"

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def sha(self, f: str, short: bool = True) -> str:
        return subprocess.run(["git", "-C", str(self.git_fx), "log", "-1",
                               f"--format={'%h' if short else '%H'}", "--", f],
                              capture_output=True, text=True, check=True).stdout.strip()


class NoGitFixtureTest(FixtureCase):
    """F-2: the no-git fixture is the scaffold with .git removed; git stays on PATH."""

    def test_no_git_dir_same_files_same_card_key(self):
        self.assertFalse((self.nogit_fx / ".git").exists())
        self.assertTrue((self.git_fx / ".git").exists())
        self.assertTrue((self.nogit_fx / "package.json").is_file())
        self.assertFalse(run.is_git_fixture(self.nogit_fx))
        self.assertEqual(run.card_path(self.home, self.nogit_fx).name,
                         run.card_path(self.home, self.git_fx).name)

    def test_seed_card_refuses_no_git(self):
        with self.assertRaises(subprocess.CalledProcessError):
            run.seed_card(self.home / "seed", self.nogit_fx)

    def test_nogit_card_fresh_refused_before_spend(self):
        argv = sys.argv
        try:
            sys.argv = ["run.py", "compare", "--cand", "HEAD", "--cases", "plan", "--home", "card",
                        "--cardless", "plan=1", "--fixture", "nogit"]
            with self.assertRaises(SystemExit) as cm:
                run.main()
            self.assertEqual(cm.exception.code, 2)
        finally:
            sys.argv = argv


class StampCheckTest(FixtureCase):
    """F-3: git fixture = <file>@<sha of its last commit>; no-git = exactly
    <file>@unverified (git unavailable). Everything else fails."""

    def check(self, fx: Path, stamp: str, name: str):
        return run.stamp_check(write_card(self.home / name, fx, stamp), fx)

    def test_git_fixture(self):
        pj, cm = self.sha("package.json"), self.sha("CLAUDE.md")
        ok, det = self.check(self.git_fx, f"package.json@{pj} ; CLAUDE.md@{cm}", "real")
        self.assertTrue(ok, det)
        self.assertIn("2 stamp(s) verified", det)
        full = self.sha("package.json", short=False)
        self.assertTrue(self.check(self.git_fx, f"package.json@{full}", "full")[0])
        self.assertTrue(self.check(self.git_fx, f"package.json@{full[:7]}", "short7")[0])
        bad = {
            "wrong": f"package.json@{'0' * 7}",
            "too-short": f"package.json@{pj[:5]}",
            "unverified": "package.json@unverified (git unavailable)",
            "unverified-bare": "package.json@unverified",
            "dirty": f"package.json@{pj} dirty",
            "untracked": "package.json@untracked",
            "missing-file": f"nope.json@{pj}",
            "other-file-sha": f"package.json@{self.sha('README.md')}" if
                              self.sha("README.md") != pj else "package.json@deadbee",
            "no-at": "package.json",
        }
        for name, stamp in bad.items():
            ok, det = self.check(self.git_fx, stamp, name)
            self.assertFalse(ok, f"{name}: {det}")

    def test_no_git_fixture(self):
        ok, det = self.check(self.nogit_fx, "package.json@unverified (git unavailable) ; "
                                            "CLAUDE.md@unverified (git unavailable)", "honest")
        self.assertTrue(ok, det)
        self.assertIn("honest no-git", det)
        for name, stamp in {"hex": "package.json@9c672ba",
                            "bare-unverified": "package.json@unverified",
                            "other-reason": "package.json@unverified (git log denied)",
                            "missing": "package.json@missing"}.items():
            self.assertFalse(self.check(self.nogit_fx, stamp, name)[0], name)

    def test_no_card_no_stamp(self):
        self.assertEqual(run.stamp_check(self.home / "none.profile.md", self.git_fx), (False, "no card"))
        p = self.home / "nostamp" / "x.profile.md"
        p.parent.mkdir(parents=True)
        p.write_text("---\nrepo: x\n---\n", encoding="utf-8")
        self.assertEqual(run.stamp_check(p, self.git_fx)[1], "no stamp line")


# A's archive.py --card outputs (1.4.1 card-by-tool wording, sent to C before commit)
WRITE_OUT = ("CARD      C:/genprompt-probe/w/homes/h/generated-prompts/by-repo/fixture.profile.md\n"
             "stamp     package.json@9c672ba ; CLAUDE.md@9c672ba\n"
             "card new\n")
NOGIT_OUT = ("CARD      C:/genprompt-probe/w/homes/h/generated-prompts/by-repo/fixture.profile.md\n"
             "stamp     package.json@unverified (git unavailable) ; CLAUDE.md@unverified (git unavailable)\n"
             "WARN  card  git unavailable: stamps are 'unverified (git unavailable)', so this card is "
             "re-derived every run\n"
             "card new\n")
DRY_OUT = "DRY RUN: would write C:/x/fixture.profile.md\n---\nrepo: fixture\n---\ncard not written (--dry-run)\n"
SIGNALLED_OUT = "dry-run signalled in parts: not written\nDRY RUN: would write C:/x\ncard not written (--dry-run)\n"
REJECT_OUT = ("FAIL  card  user_level is not present, unreadable or none\n"
              "CARD NOT WRITTEN: fix the card section and re-run.\n")
WHERE_OUT = "home C:/x/homes/h\nlocal-rules C:/x/local-rules.md (absent)\ncard C:/x/fixture.profile.md (absent)\n"


class CardStateLineTest(unittest.TestCase):
    """F-4 (pure part): the tool's printed card-state lines, pinned from A's wording, read by the
    same matcher as the lock's Stack row."""

    def test_card_state_line(self):
        self.assertEqual(run.card_state_line(WRITE_OUT), "card new")
        self.assertEqual(run.card_state_line(NOGIT_OUT), "card new")
        self.assertEqual(run.card_state_line(DRY_OUT), "card not written (--dry-run)")
        self.assertEqual(run.card_state_line(SIGNALLED_OUT), "card not written (--dry-run)")
        for out in (REJECT_OUT, WHERE_OUT, "CARD      C:/x.profile.md\n", "card new, I think\n", ""):
            self.assertIsNone(run.card_state_line(out), out)

    def test_matcher_agrees_with_the_tool(self):
        # the printed line, put in a Stack row (unwrapped and wrapped), reads as the same state
        for line, kind in (("card new", "new"), ("card not written (--dry-run)", None)):
            for row in (f"Stack       Node {DOT} role senior Node engineer {DOT} {line}",
                        f"Stack       Node {DOT} role senior Node engineer\n            {DOT} {line}"):
                self.assertEqual(run.card_claim([row]), kind, row)
            self.assertEqual(run.state_kind(line), kind)
        # the lock's other Stack-slot values are not "new" and not a format miss
        for other in ("card 3d, stamps fresh", "card 12d, stale: package.json moved"):
            self.assertIsNone(run.card_claim([f"Stack   Node {DOT} {other}"]), other)

    def test_state_match(self):
        self.assertTrue(run.state_match("new", "card new"))
        self.assertTrue(run.state_match(None, "card not written (--dry-run)"))
        self.assertTrue(run.state_match("format-miss", "card not written (--dry-run)"))
        self.assertFalse(run.state_match(None, "card new"))
        self.assertFalse(run.state_match("new", "card not written (--dry-run)"))
        self.assertFalse(run.state_match("new", None))
        self.assertFalse(run.state_match(None, None))


ARCH = "C:/genprompt-probe/w/gp-cand/tools/archive.py"
PARTS = "C:/genprompt-probe/w/homes/h/tmp/p.json"


class CandidateCardLineTest(FixtureCase):
    """F-4 (tool part): this tree's archive.py --card (A's card-by-tool, merged at 6b3cee4) prints
    a card-state line the matcher reads right, on the git and the no-git fixture."""

    ARCHIVE = Path(__file__).resolve().parents[2] / "tools" / "archive.py"

    def tool(self, fx: Path, home: Path, *flags: str, user_level: str = "unreadable",
             parts_flags: str = "") -> subprocess.CompletedProcess:
        import os
        pf = home / "tmp" / "p.json"
        pf.parent.mkdir(parents=True, exist_ok=True)
        parts = run.card_parts(fx, user_level)
        if parts_flags:
            parts["flags"] = parts_flags
        pf.write_text(json.dumps(parts), encoding="utf-8")
        return subprocess.run([sys.executable, str(self.ARCHIVE), "--card", *flags, str(pf)], cwd=fx,
                              capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "GENPROMPT_HOME": home.as_posix()})

    def test_dry_run_first_write_repeat_and_reject(self):
        home = self.home / "tool-git"
        fx = self.git_fx
        card = run.card_path(home, fx)
        for flags, pflags in (("--dry-run",), ""), ((), "--go --dry-run"):
            dry = self.tool(fx, home, *flags, parts_flags=pflags)
            line = run.card_state_line(dry.stdout)
            self.assertEqual(line, "card not written (--dry-run)", dry.stdout)
            self.assertNotIn(run.state_kind(line), ("new", "format-miss"))
            self.assertFalse(card.exists())
        first = self.tool(fx, home)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(run.card_state_line(first.stdout), "card new")
        self.assertEqual(run.state_kind(run.card_state_line(first.stdout)), "new")
        self.assertTrue(run.stamp_check(card, fx)[0], card.read_text(encoding="utf-8"))
        # the same card again: the tool replaces it (a cache) and says "card new" again; the
        # PROTOCOL reports an unchanged fresh card as "card Nd, stamps fresh" without calling it
        again = self.tool(fx, home)
        self.assertEqual(run.card_state_line(again.stdout), "card new")
        before = run.file_digest(card)
        rej = self.tool(fx, home, user_level="C:/Users/someone/.claude")
        self.assertEqual(rej.returncode, 2, rej.stdout)
        self.assertIsNone(run.card_state_line(rej.stdout))
        self.assertIn("CARD NOT WRITTEN", rej.stdout)
        self.assertEqual(run.file_digest(card), before)

    def test_no_git_stamps_honest(self):
        home = self.home / "tool-nogit"
        out = self.tool(self.nogit_fx, home)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(run.card_state_line(out.stdout), "card new")
        ok, det = run.stamp_check(run.card_path(home, self.nogit_fx), self.nogit_fx)
        self.assertTrue(ok, det)
        self.assertIn("honest no-git", det)


class CardProvenanceTest(unittest.TestCase):
    """F-5: who wrote the card, whether the writing call was bare and granted, the retry."""

    def test_bare_granted(self):
        yes = [f'python3 "{ARCH}" --card "{PARTS}"', f"python {ARCH} --card {PARTS}",
               f'python3 "{ARCH}" "{PARTS}" 2>&1', f"python3 '{ARCH}' --dry-run {PARTS}",
               f'python3 "{ARCH.replace("/", chr(92))}" --card "{PARTS}"']
        no = [f'python3 "{ARCH}" "{PARTS}"; echo "exit=$?"', f'python3 "{ARCH}" "{PARTS}" && ls',
              f'python3 "{ARCH}" "{PARTS}" | tail -3', f'python3 "{ARCH}" "{PARTS}" > out.txt',
              f'cd C:/x && python3 "{ARCH}" "{PARTS}"', f'(python3 "{ARCH}" "{PARTS}")',
              f'py "{ARCH}" "{PARTS}"', f'python3 -c "print(1)" "{ARCH}"',
              f'python3 "C:/x/tools/other.py" "{PARTS}"']
        for c in yes:
            self.assertTrue(run.bare_granted(c), c)
        for c in no:
            self.assertFalse(run.bare_granted(c), c)

    def test_summary_writer_and_retry(self):
        denied = {"cmd": f'python3 "{ARCH}" --card "{PARTS}"; echo "exit=$?"',
                  "out": "Permission to use Bash has been denied.", "denied": True}
        where = {"cmd": f'python3 "{ARCH}" --where', "out": WHERE_OUT, "denied": False}
        archive = {"cmd": f'python3 "{ARCH}" "{PARTS}"', "out": "archived C:/x.md\n", "denied": False}
        card = {"cmd": f'python3 "{ARCH}" --card "{PARTS}"', "out": WRITE_OUT, "denied": False}
        s = run.archive_summary([where, denied, archive, card])
        self.assertEqual((s["calls"], s["bare"], s["denied"], s["retried"], s["writer_bare"]),
                         (3, 2, 1, True, True))
        self.assertEqual(run.printed_card_state([where, archive, card]), "card new")
        self.assertEqual(run.printed_card_state([where, archive]), None)  # --where's card line
        # the card printed by a non-bare call that ran (a granted prefix, then a chained suffix)
        chained = dict(card, cmd=card["cmd"] + " 2>&1 | tail -5")
        self.assertFalse(run.archive_summary([chained])["writer_bare"])
        self.assertFalse(run.archive_summary([denied])["writer_bare"])

    def test_card_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, fx = Path(tmp) / "h", Path(tmp) / "fixture"
            card = write_card(home, fx, "x@unverified")
            by_tool = {"archive_calls": [{"cmd": f'python3 "{ARCH}" --card p', "out": WRITE_OUT,
                                          "denied": False}], "wrote_paths": []}
            self.assertEqual(run.card_writer(by_tool, home, fx, True), "archive.py")
            by_model = dict(by_tool, wrote_paths=[card.as_posix()])
            self.assertEqual(run.card_writer(by_model, home, fx, True), "model")
            silent = {"archive_calls": [], "wrote_paths": []}
            self.assertEqual(run.card_writer(silent, home, fx, True), "unknown")
            self.assertIsNone(run.card_writer(by_tool, home, fx, False))

    def test_analyze_records_archive_calls_and_writes(self):
        def ev(*blocks, kind="assistant"):
            return json.dumps({"type": kind, "message": {"content": list(blocks)}})
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp).resolve() / "probe" / "w"
            plugin = work / "gp-cand"
            plugin.mkdir(parents=True)
            cardp = (work / "homes" / "h" / "generated-prompts" / "by-repo" / "fixture.profile.md").as_posix()
            lines = [
                ev({"type": "tool_use", "id": "1", "name": "Bash",
                    "input": {"command": f'python3 "{plugin.as_posix()}/tools/archive.py" --card p.json'}}),
                ev({"type": "tool_result", "tool_use_id": "1", "content": WRITE_OUT}, kind="user"),
                ev({"type": "tool_use", "id": "2", "name": "Write", "input": {"file_path": cardp}}),
                ev({"type": "tool_result", "tool_use_id": "2", "content": "File created"}, kind="user"),
                json.dumps({"type": "result", "result": "done", "total_cost_usd": 0}),
            ]
            t = work / "t.jsonl"
            t.write_text("\n".join(lines), encoding="utf-8")
            a = run.analyze(t, plugin, work, write=True)
        self.assertEqual(len(a["archive_calls"]), 1)
        self.assertEqual(run.card_state_line(a["archive_calls"][0]["out"]), "card new")
        self.assertEqual(a["wrote_paths"], [cardp])

    def test_card_gates(self):
        good = {"written": True, "writer": "archive.py", "archived": True, "stamp_ok": True,
                "stamp": "2 verified", "printed": "card new", "match": True,
                "archive": {"bare": 1, "denied": 0, "retried": False, "writer_bare": True}}
        gates = run.card_gates([("slice r1", good), ("fix r1", good)])
        self.assertTrue(all(ok for _, ok, _ in gates), gates)
        self.assertEqual(len(gates), 5)
        for key, val in (("writer", "model"), ("archived", False), ("stamp_ok", False),
                         ("match", False), ("archive", dict(good["archive"], writer_bare=False))):
            bad = dict(good, **{key: val})
            gates = run.card_gates([("slice r1", good), ("plan r3", bad)])
            failed = [(n, d) for n, ok, d in gates if not ok]
            self.assertEqual(len(failed), 1, key)
            self.assertIn("plan r3", failed[0][1])
            self.assertIn("1/2", failed[0][0])
        self.assertFalse(all(ok for _, ok, _ in run.card_gates([])))
        self.assertIn("plan r3", run.card_table([("plan r3", good)]))


class BudgetTest(unittest.TestCase):
    """F-7: R5 budgets (card-fresh FAIL), +5% WARNs vs v1.4.0 (card-fresh floor, card-less L1)."""

    def test_pinned_values(self):
        self.assertEqual(run.R5_BUDGETS, {"slice": 34500, "fix": 35500, "redesign": 34000,
                                          "plan": 32000, "investigate": 37500})
        self.assertEqual(run.V140_CARD_FRESH["plan"], 29610)
        self.assertEqual(run.V140_CARDLESS["investigate"], 40517)

    def test_card_fresh(self):
        gates, warns = run.budget_checks("card", dict(run.V140_CARD_FRESH))
        self.assertEqual([ok for _, ok, _ in gates], [True])
        self.assertEqual(warns, [])
        gates, warns = run.budget_checks("card", {"plan": 31200, "slice": 32368})
        self.assertTrue(gates[0][1])  # under 32,000 but over 29,610 + 5% = 31,090.5
        self.assertEqual(len(warns), 1)
        self.assertIn("plan", warns[0])
        gates, warns = run.budget_checks("card", {"plan": 32001})
        self.assertFalse(gates[0][1])
        self.assertIn("plan 32,001 > 32,000", gates[0][2])

    def test_card_less_warn_only(self):
        gates, warns = run.budget_checks("empty", {"fix": 40500, "slice": 37679})
        self.assertEqual(gates, [])
        self.assertEqual(len(warns), 1)
        self.assertIn("card-less median 38,462", warns[0])


class SmokeTest(unittest.TestCase):
    """P-5: offline, no model. On this tree (card-by-tool merged) both fixtures pass."""

    def test_smoke_passes_on_this_tree(self):
        import argparse
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            with redirect_stdout(buf):
                code = run.smoke(argparse.Namespace(cand="HEAD", workroot=tmp))
        out = buf.getvalue()
        self.assertEqual(code, 0, out)
        self.assertIn("P-5 smoke: PASS", out)
        self.assertIn("git: PASS", out)
        self.assertIn("nogit: PASS", out)
        self.assertIn("honest no-git", out)
        for kind in run.FIXTURES:
            self.assertIn(f"{kind}: --where exit codes", out)


if __name__ == "__main__":
    unittest.main()
