"""E-22: each shipped command's Write/Edit grants match PROTOCOL's write boundary exactly, and
doctor --suite fails a command whose grants are widened (or dropped). Nothing writes into the repo:
the guard tests run on copies of commands/ in a temp dir."""
from __future__ import annotations

import importlib.util
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _util import ROOT  # noqa: E402


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DOC = load(ROOT / "tools" / "doctor.py", "doctor_write_grants")
SHIMS = load(ROOT / "tools" / "build_shims.py", "shims_write_grants")
EMITTERS = [a.cmd for a in SHIMS.ARCHETYPES] + [SHIMS.ENTRY]
UTILITIES = [u[0] for u in SHIMS.UTILITIES]

H = "~/.genprompt"
EMIT = {f"Write({H}/generated-prompts/**)", f"Edit({H}/generated-prompts/**)",
        f"Write({H}/tmp/**)", f"Edit({H}/tmp/**)"}
PINNED = {
    "learn": {f"Write({H}/local-rules.md)", f"Edit({H}/local-rules.md)"},
    "profile": {f"Write({H}/generated-prompts/by-repo/**)", f"Edit({H}/generated-prompts/by-repo/**)"},
    "history": set(), "doctor": set(), "help": set(),
}


def grants(cmd: str) -> set[str]:
    return DOC.write_grants_of((ROOT / "commands" / f"{cmd}.md").read_text(encoding="utf-8"))


def matches(rule_path: str, path: str) -> bool:
    """gitignore-style match as permission rules use it: ** spans folders, * stays in one."""
    rx = re.escape(rule_path).replace(r"\*\*", "\0").replace(r"\*", "[^/]*").replace("\0", ".*")
    return re.fullmatch(rx, path) is not None


def scopes_of(cmd: str) -> list[str]:
    return [g[len("Write("):-1] for g in grants(cmd) if g.startswith("Write(")]


class PinnedGrants(unittest.TestCase):
    def test_every_command_is_pinned(self):
        self.assertEqual(set(EMITTERS) | set(PINNED), {p.stem for p in (ROOT / "commands").glob("*.md")})
        self.assertEqual(set(UTILITIES), set(PINNED))

    def test_emitters_write_only_the_archive_and_tmp(self):
        for cmd in EMITTERS:
            self.assertEqual(grants(cmd), EMIT, cmd)

    def test_utilities_have_their_exact_grants(self):
        for cmd, want in PINNED.items():
            self.assertEqual(grants(cmd), want, cmd)

    def test_the_whole_home_is_never_granted(self):
        for p in (ROOT / "commands").glob("*.md"):
            got = DOC.write_grants_of(p.read_text(encoding="utf-8"))
            self.assertFalse({f"Write({H}/**)", f"Edit({H}/**)", "Write", "Edit"} & got, p.name)

    def test_generator_and_doctor_boundary_agree(self):
        self.assertEqual(SHIMS.EMIT_SCOPES, DOC.WRITE_BOUNDARY_EMIT)
        self.assertEqual(SHIMS.WRITE_SCOPES, DOC.WRITE_BOUNDARY)


class PathsMatch(unittest.TestCase):
    """The paths the rules name must fall inside the grants, and nothing else may."""

    def test_emitter_paths(self):
        scopes = scopes_of("slice")
        for path in (f"{H}/tmp/s02-settings.json",
                     f"{H}/generated-prompts/acme-api/2026-11-09-slice-s02-settings.md",
                     f"{H}/generated-prompts/by-repo/acme-api.profile.md",
                     f"{H}/generated-prompts/by-repo/acme-api.tsv"):
            self.assertTrue(any(matches(s, path) for s in scopes), path)
        for path in (f"{H}/local-rules.md", f"{H}/notes.md", f"{H}/history/x.md"):
            self.assertFalse(any(matches(s, path) for s in scopes), path)

    def test_learn_and_profile_paths(self):
        self.assertTrue(any(matches(s, f"{H}/local-rules.md") for s in scopes_of("learn")))
        self.assertFalse(any(matches(s, f"{H}/tmp/x.json") for s in scopes_of("learn")))
        prof = scopes_of("profile")
        self.assertTrue(any(matches(s, f"{H}/generated-prompts/by-repo/acme-api.profile.md") for s in prof))
        self.assertFalse(any(matches(s, f"{H}/generated-prompts/acme-api/x.md") for s in prof))
        self.assertFalse(any(matches(s, f"{H}/local-rules.md") for s in prof))


class DoctorGuard(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cmds = Path(self._tmp.name) / "commands"
        shutil.copytree(ROOT / "commands", self.cmds)

    def tearDown(self):
        self._tmp.cleanup()

    def errors(self) -> list[str]:
        DOC.findings.clear()
        DOC.check_write_grants(EMITTERS, commands=self.cmds)
        return [m for sev, _a, m in DOC.findings if sev == "ERROR"]

    def edit(self, cmd: str, old: str, new: str) -> None:
        p = self.cmds / f"{cmd}.md"
        text = p.read_text(encoding="utf-8")
        self.assertIn(old, text)
        p.write_text(text.replace(old, new, 1), encoding="utf-8")

    def test_repo_commands_pass(self):
        self.assertEqual(self.errors(), [])

    def test_widened_emitter_is_an_error(self):
        self.edit("slice", f"Write({H}/tmp/**)", f"Write({H}/**)")
        errs = self.errors()
        self.assertTrue(any(f"write grant Write({H}/**) is outside" in e for e in errs), errs)
        self.assertTrue(any(f"Write({H}/tmp/**) is missing" in e for e in errs), errs)

    def test_bare_write_on_a_read_only_utility_is_an_error(self):
        self.edit("history", "Read, Glob, Grep,", "Read, Glob, Grep, Write,")
        errs = self.errors()
        self.assertTrue(any("commands/history.md: write grant Write is outside" in e for e in errs), errs)

    def test_learn_writing_the_archive_is_an_error(self):
        self.edit("learn", f"Edit({H}/local-rules.md)",
                  f"Edit({H}/local-rules.md), Edit({H}/generated-prompts/**)")
        errs = self.errors()
        self.assertTrue(any(f"learn.md: write grant Edit({H}/generated-prompts/**)" in e for e in errs), errs)

    def test_other_write_tools_count(self):
        self.edit("doctor", "Read, Glob, Grep,", f"Read, Glob, Grep, MultiEdit({H}/**),")
        self.assertTrue(any("MultiEdit" in e for e in self.errors()))


if __name__ == "__main__":
    unittest.main()
