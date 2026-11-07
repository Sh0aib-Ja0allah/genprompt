"""Build the plugin's command files (commands/*.md) from one table.

The command files are thin: frontmatter (description, argument-hint, allowed-tools) plus @-includes
of PROTOCOL.md and the one archetype/utility file the command needs, with an explicit Read fallback.
Every command shares ALLOWED_TOOLS, so the permission baseline cannot drift between commands.

Paths inside the command files are written with ${CLAUDE_PLUGIN_ROOT}, which Claude Code expands
when a plugin command loads, so the plugin works wherever it is installed. The generator's own
writable folder is ~/.genprompt/ (the archive and the personal rules), outside every repo and
outside the plugin cache, which is replaced on every plugin update.

It also generates the command blocks of guide/08-grammar.md (between the GENERATED markers) from
the same tables, so the grammar cannot drift from the argument hints that ship.

Usage:  python tools/build_shims.py           write any command file that differs
        python tools/build_shims.py --check   compare only; exit 1 on any difference (doctor uses this)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import NamedTuple

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]           # the plugin root, wherever it lives
COMMANDS = ROOT / "commands"
PLUGIN_ROOT = "${CLAUDE_PLUGIN_ROOT}"                  # expanded by Claude Code at load time
USER_HOME = "~/.genprompt"                             # archive + personal rules
ENTRY = "auto"                                         # /genprompt:auto picks the archetype

READ_ONLY_GIT = [
    "git status", "git log", "git diff", "git show", "git rev-parse", "git ls-files",
    "git rev-list", "git shortlog", "git grep", "git cat-file -p", "git config --get",
    "git worktree list", "git stash list",
    "git branch --show-current", "git branch -a", "git branch -r", "git branch --list",
    "git branch -vv", "git remote -v", "git remote get-url",
    "git symbolic-ref refs/remotes/origin/HEAD", "git symbolic-ref --short refs/remotes/origin/HEAD",
]
ALLOWED_TOOLS = ", ".join(
    ["Read", "Glob", "Grep",
     f"Write({USER_HOME}/**)",
     f"Edit({USER_HOME}/**)",
     "Bash(cd:*)"]
    + [f"Bash({c}:*)" for c in READ_ONLY_GIT]
    + ["Bash(ls:*)", "Bash(wc:*)", "Bash(tail:*)", "Bash(head:*)", "Bash(date:*)"]
)
DOCTOR = ", ".join(f"Bash({py} {q}{PLUGIN_ROOT}/tools/doctor.py{q}:*)"
                   for py in ("python3", "python") for q in ("", '"'))
EXTRA_TOOLS = {
    "doctor": f", {DOCTOR}",
    "learn": "",
    "profile": "",
}
FLAGS = ("[--repo <name|path>] [--go] [--attended|--unattended] [--dry-run] [--brief] "
         "[--follows <file>]")

# Grammar groups (guide/08-grammar.md §8), in the order they are printed.
ENTRY_GROUP = "Entry"
BUILD = "Build and change"
UNDERSTAND = "Understand, decide, document"
SHIP = "Ship and continue"
GROUPS = (BUILD, UNDERSTAND, SHIP)


class Arch(NamedTuple):
    letter: str        # permanent (§12)
    cmd: str           # permanent (§12)
    stem: str          # archetypes/<stem>.md
    name: str
    desc: str          # frontmatter description: trigger words first, <= 90 characters
    hint: str          # argument hint, also printed in the grammar
    group: str         # one of GROUPS
    tagline: str       # the grammar's short gloss
    read_only: bool = False  # Autonomy "N/A": the hint omits --attended/--unattended


class Util(NamedTuple):
    cmd: str
    files: list        # include files besides PROTOCOL.md
    desc: str
    hint: str
    tagline: str


ARCHETYPES = [
    Arch("A", "redesign", "A-redesign", "Single-artifact redesign",
         "Redesign or refactor one file (screen, component, module) at senior level (worker prompt)",
         "<file path> (<screen|dialog|component|module|controller>)",
         BUILD, "one artifact, senior-level rebuild"),
    Arch("B", "audit", "B-audit", "Audit / read-only assessment",
         "Audit an area read-only: one doc with a ranked backlog, no code (worker prompt)",
         "<area to assess>",
         UNDERSTAND, "read-only assessment, one doc"),
    Arch("C", "kickoff", "C-kickoff", "Kickoff with dirty WIP",
         "Kick off a unit over uncommitted WIP already in the tree (worker prompt)",
         "<unit to start>",
         BUILD, "start work over uncommitted WIP"),
    Arch("D", "slice", "D-slice", "Slice execution",
         "Build one vertical slice (a feature or change set) with checkpoints (worker prompt)",
         "Slice <ID>, scope: <bullets>",
         BUILD, "one vertical slice, checkpoints"),
    Arch("E", "approve", "E-approve", "Approval / rulings / amendment",
         "Rule on findings, lock decisions, or amend a sent prompt (worker prompt)",
         "decisions: <list>; order: <...>  |  amend <prior prompt>",
         SHIP, "rulings / amendment"),
    Arch("F", "plan", "F-plan", "Planning-only",
         "Plan a unit or cross-repo work: one plan doc with stable ids, no code (worker prompt)",
         "<unit> <backend|frontend|cross-repo>",
         UNDERSTAND, "plan doc, no code"),
    Arch("G", "greenfield", "G-greenfield", "Greenfield from a reference repo",
         "Build a new layer from scratch, studying a reference repo first (worker prompt)",
         "<layer> studying <reference repo>",
         BUILD, "new layer, reference studied first"),
    Arch("H", "commit", "H-commit", "Commit & push (incl. verify+commit)",
         "Commit and push a scoped body of finished work, or verify then commit (worker prompt)",
         "<work to commit> [verify+]",
         SHIP, "commit & push, staged by path"),
    Arch("I", "roadmap", "I-roadmap", "Roadmap / backlog execution",
         "Execute a whole backlog or roadmap doc to done, part by part (worker prompt)",
         "drive <doc> to done",
         BUILD, "whole backlog, in parts"),
    Arch("J", "next", "J-next", "Continuation",
         "Next step from a pasted worker stop-report, or a closeout if nothing left (worker prompt)",
         "<paste the worker's report, or nothing if it is already in the chat>",
         SHIP, "the next prompt"),
    Arch("K", "resume", "K-resume", "Resume after compaction",
         "Resume a worker that lost context after compaction: rebuild it, continue (worker prompt)",
         "<unit/slice the worker was mid-way through>",
         SHIP, "re-anchor after compaction"),
    Arch("L", "fix", "L-fix", "Defect-driven fix slice",
         "Fix confirmed defects: repro, acceptance and false positives per defect (worker prompt)",
         "<defect list, or the audit/report that found them>",
         BUILD, "confirmed defects, repro + acceptance each"),
    Arch("M", "onboard", "M-onboard", "Onboard / discovery",
         "Onboard an unfamiliar or empty repo: map it, draft its CLAUDE.md contract (worker prompt)",
         "[repo]",
         UNDERSTAND, "map a repo, draft its contract + profile"),
    Arch("N", "design", "N-design", "Design / spike / ADR",
         "Design before building: ADR, API contract, schema/ERD, design map, spike (worker prompt)",
         "<ADR | API contract | schema | design system | spike>: <decision>",
         UNDERSTAND, "design docs, no production code"),
    Arch("O", "test", "O-test", "Test engineering",
         "Write missing tests, fix flaky or vacuous tests, or build a test harness (worker prompt)",
         "<area | coverage target | flaky or vacuous tests>",
         BUILD, "test engineering"),
    Arch("P", "review", "P-review", "Code review",
         "Review a diff, branch, PR or recent commits: findings only, no edits (worker prompt)",
         "<base..head | branch | PR number | last N commits>",
         UNDERSTAND, "code review, findings only"),
    Arch("Q", "security", "Q-security", "Security review and hardening",
         "Security: threat model, review authz/uploads/secrets/headers, safe fixes (worker prompt)",
         "<area | whole app>",
         UNDERSTAND, "threat model + hardening"),
    Arch("R", "perf", "R-perf", "Performance",
         "Speed up something slow or heavy: measure, optimise, before/after numbers (worker prompt)",
         "<symptom or target metric>",
         BUILD, "measure, then optimise"),
    Arch("S", "upgrade", "S-upgrade", "Upgrade and migration",
         "Upgrade framework or dependency majors, or migrate ORM/platform/data (worker prompt)",
         "<package> <from> -> <to>  |  <migration>",
         BUILD, "majors, ORM/data/platform migrations"),
    Arch("T", "release", "T-release", "Release and deploy",
         "Release or deploy: version, changelog, runbook, smoke, rollback, approvals (worker prompt)",
         "<version | environment | handover>",
         SHIP, "release/deploy, approval per action"),
    Arch("U", "hotfix", "U-hotfix", "Hotfix / incident",
         "Hotfix a live incident: triage, mitigate, root cause, test, postmortem (worker prompt)",
         "<symptom, since when, who is affected>",
         BUILD, "triage → mitigate → root cause"),
    Arch("V", "cleanup", "V-cleanup", "Cleanup / maintenance",
         "Clean up dead code, remove a feature, restore green, no-behaviour refactor (worker prompt)",
         "<dead code | removal | restore-green | refactor target>",
         BUILD, "no behaviour change"),
    Arch("W", "docs", "W-docs", "Documentation",
         "Write or repair docs (README, API, runbook, handover) checked vs code (worker prompt)",
         "<doc> for <audience>",
         UNDERSTAND, "docs checked against the code"),
]

UTILITIES = [
    Util("help", ["utilities/help.md", "archetypes/README.md", "guide/08-grammar.md"],
         "Which genprompt command fits my goal? Picker with flags and examples (no prompt)",
         "[goal, e.g. 'I need to upgrade Laravel']",
         "\"I want to X\" → which command, with flags and examples"),
    Util("history", ["utilities/history.md"],
         "Show a repo's recent genprompt prompts, the follows chain, profile status (no prompt)",
         "[repo] [n]",
         "the latest n shard rows (default 10) and the follows chain"),
    Util("doctor", ["utilities/doctor.md"],
         "Check the genprompt rules suite and prompt archive for integrity errors (no prompt)",
         "[--suite | --archive]",
         "integrity check of the rules and the archive"),
    Util("learn", ["utilities/learn.md", "guide/00-index.md"],
         "Save a lesson as a personal genprompt rule in local-rules.md, diff first (no prompt)",
         "<rule or lesson>",
         "save a lesson as a personal rule in ~/.genprompt/local-rules.md (shows the diff first)"),
    Util("profile", ["utilities/profile.md", "guide/01-target-profile.md", "stacks/stack-matrix.md"],
         "Derive or refresh a repo's genprompt profile card (no prompt)",
         "[repo] [--dry-run]",
         "derive or refresh the profile card; no prompt"),
]

# Utilities that do not load PROTOCOL.md: they emit no prompt, need no TARGET LOCK and write nothing.
# learn keeps PROTOCOL: it edits local-rules.md under the protocol's write boundary and precedence.
PROTOCOL_FREE = {"help", "doctor"}


def yaml_str(value: str) -> str:
    # A JSON string is a valid YAML double-quoted scalar: safe for ': ', '#', '[' and '<'.
    return json.dumps(value, ensure_ascii=False)


def frontmatter(desc: str, hint: str, extra: str = "") -> str:
    return (f"---\ndescription: {yaml_str(desc)}\nargument-hint: {yaml_str(hint)}\n"
            f"allowed-tools: {ALLOWED_TOOLS}{extra}\n---\n")


def includes(files: list[str], protocol: bool = True) -> str:
    load = ["PROTOCOL.md", *files] if protocol else list(files)
    inc = "\n".join(f"@{PLUGIN_ROOT}/{f}" for f in load)
    reads = ", ".join(f"`{PLUGIN_ROOT}/{f}`" for f in load)
    paths = (f"Paths for this run: the genprompt root (these rules, read-only) is `{PLUGIN_ROOT}`. "
             f"The genprompt home (the archive and your personal rules) is `{USER_HOME}/`.\n\n")
    if not protocol:
        # Protocol-free utilities: they emit no prompt, need no TARGET LOCK and write nothing, so
        # Step 0 must not send the model to PROTOCOL.md (that would undo the saving).
        return (f"{inc}\n\n{paths}"
                f"Step 0: if any file listed here is missing from context, Read it now: {reads}. "
                f"This utility does not need `PROTOCOL.md`; do not Read it. If "
                f"`{USER_HOME}/local-rules.md` exists, Read it (personal rules). Everything below "
                f"assumes they are loaded.\n")
    return (f"{inc}\n\n{paths}"
            f"Step 0: if the line `GENPROMPT-PROTOCOL v3 LOADED` is not visible above, or any "
            f"file listed here is missing from context, Read it now: {reads}. Then run "
            f"`ls -d ~ {USER_HOME}/local-rules.md` once: it prints your absolute home directory "
            f"(use it for every Write), and if `local-rules.md` exists, Read it (personal rules, see "
            f"PROTOCOL). Everything below assumes they are loaded.\n")


def archetype_shim(letter, cmd, stem, name, desc, hint) -> str:
    return (frontmatter(desc, f"{hint}   {FLAGS}") + "\n" + includes([f"archetypes/{stem}.md"]) +
            f"\nCommand `/genprompt:{cmd}` → archetype **{letter}: {name}** (§5.{letter}). "
            f"Follow PROTOCOL Steps 1–7 with this archetype. If the request is really a different "
            f"archetype, say so in the TARGET LOCK and use the right one (hybrids are fine).\n\n"
            f"Request: $ARGUMENTS\n")


def utility_shim(cmd, files, desc, hint) -> str:
    extra = EXTRA_TOOLS.get(cmd, "")
    return (frontmatter(desc, hint, extra) + "\n" +
            includes(files, protocol=cmd not in PROTOCOL_FREE) +
            f"\nUtility `/genprompt:{cmd}`: follow `utilities/{cmd}.md`. It emits no worker prompt.\n\n"
            f"Request: $ARGUMENTS\n")


ENTRY_DESC = "Any task: picks the archetype from the request, targets the current repo (worker prompt)"
ENTRY_HINT = "[task, or a pasted worker report, or empty for the picker]"
ENTRY_TAGLINE = "pick the archetype from the request and emit its prompt, or offer the picker"


def root_shim() -> str:
    return (frontmatter(ENTRY_DESC, f"{ENTRY_HINT}   {FLAGS}")
            + "\n" + includes(["archetypes/README.md"]) +
            f"\nEntry point `/genprompt:{ENTRY}`. Pick the archetype from the request using the picker "
            "in `archetypes/README.md`, then Read that archetype's file and follow PROTOCOL Steps 1–7. "
            "A pasted worker stop-report with no instruction means archetype J (`:next`). An empty "
            "request: resolve the target anyway, then offer the picker in one message, instead of "
            "asking twice.\n\nRequest: $ARGUMENTS\n")


def table_errors() -> list[str]:
    errors = []
    cmds = [ENTRY] + [r.cmd for r in ARCHETYPES] + [u.cmd for u in UTILITIES]
    letters = [r.letter for r in ARCHETYPES]
    for r in ARCHETYPES:
        if r.group not in GROUPS:
            errors.append(f"archetype {r.cmd}: unknown grammar group {r.group!r}")
    for name, seq in (("command", cmds), ("letter", letters)):
        dup = sorted({x for x in seq if seq.count(x) > 1})
        if dup:
            errors.append(f"duplicate {name}(s) in the tables: {', '.join(dup)}")
    return errors


def expected() -> dict[Path, str]:
    out = {COMMANDS / f"{ENTRY}.md": root_shim()}
    for r in ARCHETYPES:
        out[COMMANDS / f"{r.cmd}.md"] = archetype_shim(r.letter, r.cmd, r.stem, r.name, r.desc,
                                                       r.hint)
    for u in UTILITIES:
        out[COMMANDS / f"{u.cmd}.md"] = utility_shim(u.cmd, u.files, u.desc, u.hint)
    return out


# --- guide/08-grammar.md: the command blocks between the markers are generated -----------------

GRAMMAR = ROOT / "guide" / "08-grammar.md"
GRAMMAR_BEGIN = "<!-- BEGIN GENERATED: tools/build_shims.py (edit the tables there, then run it) -->"
GRAMMAR_END = "<!-- END GENERATED -->"


def _gline(cmd: str, hint: str, tail: str, hint_width: int) -> str:
    return (f"/genprompt:{cmd}".ljust(21) + " " + hint.ljust(hint_width) + "  " + tail).rstrip()


def grammar_region() -> str:
    """The generated part of §8: an Entry block, then one fenced block per group."""
    parts = []

    def block(title: str, rows: list[str]) -> None:
        parts.append(f"### {title}\n\n```text\n" + "\n".join(rows) + "\n```\n")

    block(ENTRY_GROUP, [_gline(ENTRY, ENTRY_HINT, ENTRY_TAGLINE, 46)])
    for g in GROUPS:
        block(g, [_gline(r.cmd, r.hint, f"{r.letter}  {r.tagline}", 46)
                  for r in ARCHETYPES if r.group == g])
    block("Utilities (they emit no worker prompt)",
          [_gline(u.cmd, u.hint, u.tagline, 21) for u in UTILITIES])
    return "\n".join(parts)


def expected_docs() -> dict[Path, str | None]:
    """Hand-written docs with a generated region. None: the file or its markers are missing."""
    cur = GRAMMAR.read_text(encoding="utf-8") if GRAMMAR.exists() else ""
    b, e = cur.find(GRAMMAR_BEGIN), cur.find(GRAMMAR_END)
    if b < 0 or e < b:
        return {GRAMMAR: None}
    return {GRAMMAR: cur[:b + len(GRAMMAR_BEGIN)] + "\n\n" + grammar_region() + "\n" + cur[e:]}


def say(msg: str) -> None:
    sys.stdout.write(f"{msg}\n")


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--check"]
    if unknown:
        say(f"unknown argument(s): {' '.join(unknown)}   usage: build_shims.py [--check]")
        return 2
    check = "--check" in argv
    errors = table_errors()
    for e in errors:
        say(f"ERROR {e}")
    if errors:
        return 1
    exp = expected()
    bad = 0
    for path, text in exp.items():
        cur = path.read_text(encoding="utf-8") if path.exists() else None
        if cur == text:
            continue
        if check:
            say(f"DIFF  {path.relative_to(ROOT).as_posix()}")
            bad += 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
            say(f"wrote {path.relative_to(ROOT).as_posix()}")
    for p in sorted(set(COMMANDS.glob("*.md")) - set(exp)):
        say(f"EXTRA {p.relative_to(ROOT).as_posix()} (not generated by build_shims.py)")
        bad += 1
    docs = expected_docs()
    docs_bad, missing = 0, False
    for path, text in docs.items():
        rel = path.relative_to(ROOT).as_posix()
        if text is None:
            say(f"ERROR {rel}: file or generated-region markers missing")
            docs_bad, missing = docs_bad + 1, True
        elif path.read_text(encoding="utf-8") != text:
            if check:
                say(f"DIFF  {rel} (generated region)")
                docs_bad += 1
            else:
                path.write_text(text, encoding="utf-8", newline="\n")
                say(f"wrote {rel} (generated region)")
    if check:
        say(f"commands: {len(exp)} expected, {bad} differ/extra")
        say(f"docs: {len(docs)} with a generated region, {docs_bad} differ")
    return 1 if (check and (bad or docs_bad)) or missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
