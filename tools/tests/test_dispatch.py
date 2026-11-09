"""E-12: dispatch (`--send <session>`, §10.8). The send itself needs a live peer session, so it is
checked by hand at CP6; these tests pin what can be checked statically: the grant sits on exactly
the prompt-emitting commands (doctor enforces it independently), PROTOCOL carries only a pointer,
the per-run excerpts carry no dispatch text, and §10.8 states the strict layer-1 rules."""
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


DOC = load(ROOT / "tools" / "doctor.py", "doctor_dispatch")
SHIMS = load(ROOT / "tools" / "build_shims.py", "shims_dispatch")
EMITTERS = [a.cmd for a in SHIMS.ARCHETYPES] + [SHIMS.ENTRY]


def section(text: str, head: str) -> str:
    start = text.index(head)
    nxt = re.search(r"^(### |---)", text[start + len(head):], re.M)
    return text[start:start + len(head) + (nxt.start() if nxt else len(text))]


class DispatchText(unittest.TestCase):
    def test_generator_and_doctor_agree_on_the_tools(self):
        self.assertEqual({t.strip() for t in SHIMS.DISPATCH.split(",")}, DOC.DISPATCH_TOOLS)

    def test_protocol_has_one_pointer_and_no_rules(self):
        proto = (ROOT / "PROTOCOL.md").read_text(encoding="utf-8")
        hits = [ln for ln in proto.splitlines() if "--send" in ln]
        self.assertEqual(len(hits), 1, hits)
        self.assertIn("§10.8", hits[0])
        self.assertIn("even under `--go` or auto-go", hits[0])
        self.assertNotIn("SendMessage", proto)

    def test_excerpts_carry_no_dispatch_text(self):
        # The per-run load is gated: --send detail lives in §10.8, which no command @-includes.
        for p in sorted((ROOT / "guide" / "blocks").glob("*.md")):
            text = p.read_text(encoding="utf-8")
            for word in ("--send", "SendMessage", "ListAgents", "§10.8"):
                self.assertNotIn(word, text, p.name)
        for p in (ROOT / "commands").glob("*.md"):
            self.assertNotIn("06-library", p.read_text(encoding="utf-8"), p.name)

    def test_library_states_the_strict_layer_one_rules(self):
        lib = (ROOT / "guide" / "06-library.md").read_text(encoding="utf-8")
        s = section(lib, "### 10.8 Dispatch")
        for rule in (
            "compared case-sensitively with the lock's repo key",   # exact key, case-sensitive
            "No fuzzy, substring or prefix match",
            "A name without ` : ` is a mismatch",                   # missing prefix = mismatch
            "Under `--go`, auto-go or `lock=auto`, stop anyway",    # auto-go never covers a send
            "Only an explicit `yes` sends. No answer, `no` or anything else: no send",
            "printed for copy/paste as always",                    # the fallback
            '`"sent": "copy"` otherwise; without `--send`, no `sent` field',
            "the bare session name, no `[ref]`",
            "verbatim",                                             # read back, never re-typed
            "git rev-parse --show-toplevel",                        # layer 2: the worker's check
            'reply "wrong session"',
            "Nothing else: no lock, grounding, header table or self-check",   # layer 3
            "Never send to a name that is not listed, or to\n   this session",
            "never the listing",
        ):
            self.assertIn(rule, s, rule)
        self.assertNotIn("--subagent", lib)


class DoctorDispatchGuard(unittest.TestCase):
    """doctor --suite fails a utility that gains the dispatch tools, or an emitter that loses them."""

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
        p.write_bytes(text.replace(old, new, 1).encode("utf-8"))

    def test_repo_commands_pass(self):
        self.assertEqual(self.errors(), [])

    def test_utility_with_send_is_an_error(self):
        self.edit("history", "Read, Glob", "Read, SendMessage, Glob")
        errs = self.errors()
        self.assertEqual(len(errs), 1, errs)
        self.assertIn(":history emits no prompt, so it must not carry SendMessage", errs[0])

    def test_emitter_missing_listagents_is_an_error(self):
        self.edit("plan", ", ListAgents, SendMessage", ", SendMessage")
        errs = self.errors()
        self.assertEqual(len(errs), 1, errs)
        self.assertIn("dispatch grant ListAgents is missing for :plan", errs[0])


if __name__ == "__main__":
    unittest.main()
