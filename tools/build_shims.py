"""Build the plugin's command files (commands/*.md) from one table.

The command files are thin: frontmatter (description, argument-hint, allowed-tools) plus @-includes
of PROTOCOL.md and the one archetype/utility file the command needs, with an explicit Read fallback.
Every command shares one allowed-tools baseline (allowed_tools()); only its Write/Edit scopes differ.

Paths inside the command files are written with ${CLAUDE_PLUGIN_ROOT}, which Claude Code expands
when a plugin command loads, so the plugin works wherever it is installed. The generator's own
writable folder is ~/.genprompt/ (the archive and the personal rules), outside every repo and
outside the plugin cache, which is replaced on every plugin update. Each command may write only
its part of it (EMIT_SCOPES / WRITE_SCOPES below).

It also generates the command blocks of guide/08-grammar.md (between the GENERATED markers) from
the same tables, so the grammar cannot drift from the argument hints that ship.

Usage:  python tools/build_shims.py           write any command file that differs
        python tools/build_shims.py --check   compare only; exit 1 on any difference (doctor uses this)
"""
from __future__ import annotations

import json
import re
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
# Write/Edit scopes under the home, per command, matching PROTOCOL's write boundary (E-22):
# prompt-emitting commands write the archive and the archive.py parts file; :learn writes only its
# personal-rules file; :profile writes only the card; the other utilities write nothing.
# doctor --suite checks every command against its own copy of the boundary (WRITE_BOUNDARY), so
# widening a scope here alone fails the suite. A GENPROMPT_HOME sandbox is outside these grants by
# design: a probe grants its own scope.
EMIT_SCOPES = ("generated-prompts/**", "tmp/**")
WRITE_SCOPES: dict[str, tuple[str, ...]] = {
    "learn": ("local-rules.md",),
    "profile": ("generated-prompts/by-repo/**",),
}                                                     # any other utility: none


def write_grants(scopes: tuple[str, ...]) -> list[str]:
    return [f"{tool}({USER_HOME}/{s})" for s in scopes for tool in ("Write", "Edit")]


def allowed_tools(scopes: tuple[str, ...]) -> str:
    return ", ".join(
        ["Read", "Glob", "Grep", *write_grants(scopes), "Bash(cd:*)"]
        + [f"Bash({c}:*)" for c in READ_ONLY_GIT]
        + ["Bash(ls:*)", "Bash(wc:*)", "Bash(tail:*)", "Bash(head:*)", "Bash(date:*)"]
    )

DOCTOR = ", ".join(f"Bash({py} {q}{PLUGIN_ROOT}/tools/doctor.py{q}:*)"
                   for py in ("python3", "python") for q in ("", '"'))
# Every command that emits a prompt archives it through tools/archive.py (PROTOCOL Step 6), so the
# archetype shims and the entry point may run that one script. archive.py writes only under
# ~/.genprompt and runs doctor's per-file lint itself, so no separate doctor --prompt grant.
ARCHIVE = ", ".join(f"Bash({py} {q}{PLUGIN_ROOT}/tools/archive.py{q}:*)"
                    for py in ("python3", "python") for q in ("", '"'))
EXTRA_TOOLS = {
    "doctor": f", {DOCTOR}",
    "learn": "",
    "profile": "",
}
# Extra frontmatter lines per command (cmd -> lines, each "key: value"), emitted after allowed-tools.
# disable-model-invocation keeps a command typeable as /genprompt:<cmd> but takes it out of the
# model's skill listing, which saves listing budget for the commands the model should offer.
# help stays visible: "which command fits" is exactly when the model should offer it.
EXTRA_FM: dict[str, list[str]] = {
    cmd: ["disable-model-invocation: true"] for cmd in ("doctor", "learn", "history", "profile")
}
FLAGS = ("[--repo <name|path>] [--go] [--attended|--unattended] [--dry-run] [--brief] "
         "[--follows <file>] [--verbose]")
# Read-only archetypes (Autonomy "N/A") omit --attended/--unattended: the flag does nothing there.
FLAGS_RO = FLAGS.replace("[--attended|--unattended] ", "")

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
         UNDERSTAND, "read-only assessment, one doc", read_only=True),
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
         UNDERSTAND, "plan doc, no code", read_only=True),
    Arch("G", "greenfield", "G-greenfield", "Greenfield from a reference repo",
         "Build a new layer from scratch, studying a reference repo first (worker prompt)",
         "<layer> studying <reference repo>",
         BUILD, "new layer, reference studied first"),
    Arch("H", "commit", "H-commit", "Commit & push (incl. verify+commit)",
         "Commit and push a scoped body of finished work, or verify then commit (worker prompt)",
         "<work to commit> [verify+]",
         SHIP, "commit & push, staged by path", read_only=True),
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
         UNDERSTAND, "map a repo, draft its contract + profile", read_only=True),
    Arch("N", "design", "N-design", "Design / spike / ADR",
         "Design before building: ADR, API contract, schema/ERD, design map, spike (worker prompt)",
         "<ADR | API contract | schema | design system | spike>: <decision>",
         UNDERSTAND, "design docs, no production code", read_only=True),
    Arch("O", "test", "O-test", "Test engineering",
         "Write missing tests, fix flaky or vacuous tests, or build a test harness (worker prompt)",
         "<area | coverage target | flaky or vacuous tests>",
         BUILD, "test engineering"),
    Arch("P", "review", "P-review", "Code review",
         "Review a diff, branch, PR or recent commits: findings only, no edits (worker prompt)",
         "<base..head | branch | PR number | last N commits>",
         UNDERSTAND, "code review, findings only", read_only=True),
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
         UNDERSTAND, "docs checked against the code", read_only=True),
    Arch("X", "investigate", "X-investigate", "Investigate / root cause",
         "Find the root cause of a bug with unknown cause: repro, trace, path:line (worker prompt)",
         "<symptom: what happens vs expected, and how to trigger it>",
         UNDERSTAND, "unknown-cause bug → root cause, hand-off to :fix", read_only=True),
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
         "[--suite | --archive | --suggest-fixes]",
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


def frontmatter(desc: str, hint: str, extra: str = "", cmd: str = "",
                scopes: tuple[str, ...] = ()) -> str:
    fm = "".join(f"{line}\n" for line in EXTRA_FM.get(cmd, []))
    return (f"---\ndescription: {yaml_str(desc)}\nargument-hint: {yaml_str(hint)}\n"
            f"allowed-tools: {allowed_tools(scopes)}{extra}\n{fm}---\n")


def includes(files: list[str], protocol: bool = True, where: bool = False) -> str:
    """where: the shim carries the ARCHIVE grant, so Step 0 asks `archive.py --where` for the
    home (GENPROMPT_HOME or ~/.genprompt, E-09e); other shims keep `ls -d ~`."""
    load = ["PROTOCOL.md", *files] if protocol else list(files)
    inc = "\n".join(f"@{PLUGIN_ROOT}/{f}" for f in load)
    reads = ", ".join(f"`{PLUGIN_ROOT}/{f}`" for f in load)
    # The home is defined once in PROTOCOL ("Where things live") and printed by Step 0 (E-09f).
    paths = f"Paths: the genprompt root (read-only rules) is `{PLUGIN_ROOT}`.\n\n"
    if not protocol:
        # Protocol-free utilities: they emit no prompt, need no TARGET LOCK and write nothing, so
        # Step 0 must not send the model to PROTOCOL.md (that would undo the saving).
        return (f"{inc}\n\n{paths}"
                f"Step 0: if any file listed here is missing from context, Read it now: {reads}. "
                f"This utility does not need `PROTOCOL.md`; do not Read it. If "
                f"`{USER_HOME}/local-rules.md` exists, Read it (personal rules). Everything below "
                f"assumes they are loaded.\n")
    # The @-lines above expand into the files' text when the command loads (verified for plugin
    # commands in E-09b). Re-reading them "to be safe" doubled the rule load, so Step 0 reads a
    # file only when its text is genuinely absent (E-09f: the @ paths are the fallback list).
    return (f"{inc}\n\n{paths}"
            f"Step 0: the files above are already in context (their text follows the `@` lines; "
            f"PROTOCOL's third line says `GENPROMPT-PROTOCOL v3 LOADED`). Don't Read them again "
            f"unless that marker is absent. Then run " + (
                f"`python3 {PLUGIN_ROOT}/tools/archive.py --where` once (`python` if `python3` is "
                f"missing or a store alias): its `home` line is the absolute home for every "
                f"`{USER_HOME}/` path and Write; if its `local-rules` line says `present`, Read "
                f"that file.\n" if where else
                f"`ls -d ~ {USER_HOME}/local-rules.md` once: it prints your absolute home (for every "
                f"Write); if `local-rules.md` exists, Read it.\n"))


def archetype_shim(letter, cmd, stem, name, desc, hint, flags: str = FLAGS) -> str:
    return (frontmatter(desc, f"{hint}   {flags}", f", {ARCHIVE}", cmd=cmd,
                        scopes=EMIT_SCOPES) + "\n" +
            includes([f"archetypes/{stem}.md", f"{BLOCKS_DIR}/{stem}.md"], where=True) +
            f"\nCommand `/genprompt:{cmd}` → archetype **{letter}: {name}** (§5.{letter}): follow "
            f"PROTOCOL Steps 1–7. If the request is really another archetype, say so in the lock "
            f"and use it (hybrids are fine).\n\n"
            f"Request: $ARGUMENTS\n")


def utility_shim(cmd, files, desc, hint) -> str:
    extra = EXTRA_TOOLS.get(cmd, "")
    return (frontmatter(desc, hint, extra, cmd=cmd, scopes=WRITE_SCOPES.get(cmd, ())) + "\n" +
            includes(files, protocol=cmd not in PROTOCOL_FREE) +
            f"\nUtility `/genprompt:{cmd}`: follow `utilities/{cmd}.md`. It emits no worker prompt.\n\n"
            f"Request: $ARGUMENTS\n")


ENTRY_DESC = "Any task: picks the archetype from the request, targets the current repo (worker prompt)"
ENTRY_HINT = "[task, or a pasted worker report, or empty for the picker]"
ENTRY_TAGLINE = "pick the archetype from the request and emit its prompt, or offer the picker"


def root_shim() -> str:
    return (frontmatter(ENTRY_DESC, f"{ENTRY_HINT}   {FLAGS}", f", {ARCHIVE}", scopes=EMIT_SCOPES)
            + "\n" + includes(["archetypes/README.md"], where=True) +
            f"\nEntry point `/genprompt:{ENTRY}`. Pick the archetype from the request using the picker "
            "in `archetypes/README.md`, then Read that archetype's file and its block excerpt "
            f"`{BLOCKS_DIR}/<letter>-<command>.md` (this entry point loads neither up front, because "
            "it picks the archetype first), and follow PROTOCOL Steps 1–7. "
            "A pasted worker stop-report with no instruction means archetype J (`:next`). An empty "
            "request: resolve the target anyway, then, in one message and without asking twice, "
            "show the target and these six commands, each with its purpose: "
            "`:onboard` (understand a repo you haven't worked in), "
            "`:slice` (build one feature or change set), "
            "`:next` (continue from a worker's stop-report), "
            "`:review` (review what the worker committed), "
            "`:fix` (fix confirmed bugs), "
            "`:commit` (commit and push finished work). "
            "End with: for anything else, `/genprompt:help <your goal>`."
            "\n\nRequest: $ARGUMENTS\n")


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
                                                       r.hint, FLAGS_RO if r.read_only else FLAGS)
    for u in UTILITIES:
        out[COMMANDS / f"{u.cmd}.md"] = utility_shim(u.cmd, u.files, u.desc, u.hint)
    for r in ARCHETYPES:
        out[ROOT / BLOCKS_DIR / f"{r.stem}.md"] = block_excerpt(r)
    out[ROOT / BLOCKS_DIR / f"{DERIVE}.md"] = derive_excerpt()
    return out


# --- guide/blocks/<stem>.md: per-archetype excerpts of guide/03-blocks.md (E-09a, E-09d) ---------
# 03-blocks stays the single, hand-edited source. Each archetype shim @-includes its excerpt, so a
# generator has every block it needs without loading all of 03-blocks. The excerpt also carries
# the compact §6 checklist (E-09d), so a normal run reads no rule file at all.

BLOCKS_SRC = ROOT / "guide" / "03-blocks.md"
BLOCKS_DIR = "guide/blocks"
# E-09d: only the blocks PROTOCOL's own steps use on every run: notation (§4.0), the printed header,
# grounding and interpretations (§4.1-§4.3, Step 6.3), the report (§4.14), the length budget
# (§4.21, Step 5.4) and verify-at-start (§4.22, Step 4). Anchor, source of truth, skepticism and
# the stop-list (§4.5-§4.7, §4.13) come in only where the archetype names them; otherwise the
# generator composes them from Step 5's carry list and §6.
COMMON_BLOCKS = ("4.0", "4.1", "4.2", "4.3", "4.14", "4.21", "4.22")
_SEC_HEAD = re.compile(r"^### (4\.\d+)\b", re.M)
_SEC_REF = re.compile(r"§(4\.\d+)")
_INSERT_REF = re.compile(r"\[INSERT §(4\.\d+)")
_INSERT_414 = re.compile(r"\[INSERT §4\.14\b[^\]]*\]")   # body may span lines

# §4.20 is a table of situational blocks; an excerpt carries only the rows its archetype names.
# Each row's bold name → how an archetype refers to it (case-insensitive, anywhere in its file).
SITUATIONAL = "4.20"
SITUATIONAL_KEYS = {
    "THE CENTRAL PROBLEM TO SOLVE": r"central problem",
    "Structure and its reasoning": r"\bstructure\b(?: table| and its|:)",
    "Sequencing with rationale": r"\bsequencing\b",
    "Oracle / predicate framing": r"\boracle\b",
    "One predicate, not N guards": r"one predicate",
    "RECORD, DO NOT ACT": r"record, do not act",
    "Epistemics / bias check": r"\bepistemics\b",
    "STOP / DEFER with revert": r"stop ?/ ?defer",
    "Tree-integrity guard": r"tree-integrity",
    "Explicit tool allow-list": r"allow-list",
    "Reading manifest with depth": r"reading manifest",
    "Deliverable TOC with an ID scheme": r"deliverable toc",
    "Commit-staging manifest": r"commit-staging",
    "Write it up as method": r"write it up as method",
    "STANDING RULES": r"standing rules",
    "STEP 0 dependency check": r"step 0",
}
_ROW_NAME = re.compile(r"^\| \*\*(.+?)\*\* \|", re.M)
# §4.21's tier table (doctor.check_tiers reads the same rows): an excerpt keeps its own tier.
LENGTH = "4.21"
_TIER_ROW = re.compile(r"^\|\s*(?:Delta|Focused|Slice|Program)\s*\|[^|]*\|([^|]+)\|")


def _sec_key(s: str) -> int:
    return int(s.split(".")[1])


def block_sections() -> dict[str, str]:
    """guide/03-blocks.md cut by `### 4.x` heading: {"4.14": "### 4.14 …\n…"} (verbatim)."""
    text = BLOCKS_SRC.read_text(encoding="utf-8") if BLOCKS_SRC.exists() else ""
    heads = list(_SEC_HEAD.finditer(text))
    out = {}
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out[m.group(1)] = text[m.start():end]
    return out


def archetype_text(r: Arch) -> str:
    p = ROOT / "archetypes" / f"{r.stem}.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def excerpt_ids(r: Arch) -> list[str]:
    """Common blocks + every §4.x the archetype names (Required list, INSERTs, prose)."""
    ids = set(COMMON_BLOCKS) | set(_SEC_REF.findall(archetype_text(r)))
    return sorted(ids, key=_sec_key)


def situational_rows(r: Arch) -> list[str]:
    """The §4.20 row names the archetype refers to (SITUATIONAL_KEYS)."""
    text = archetype_text(r).lower()
    return [name for name, pat in SITUATIONAL_KEYS.items() if re.search(pat, text)]


def excerpt_section(r: Arch, sec: str, src: str) -> str:
    """A §4 block as the excerpt carries it: verbatim lines, except that §4.20 keeps only the rows
    the archetype names and §4.21's tier table keeps only the archetype's own tier."""
    lines = src.splitlines(keepends=True)
    if sec == SITUATIONAL:
        keep = set(situational_rows(r))
        lines = [ln for ln in lines if not (m := _ROW_NAME.match(ln)) or m.group(1) in keep]
    elif sec == LENGTH:
        lines = [ln for ln in lines
                 if not (m := _TIER_ROW.match(ln)) or r.letter in re.findall(r"\b([A-Z])\b", m.group(1))]
    return "".join(lines)


def block_excerpt(r: Arch) -> str:
    secs = block_sections()
    ids = [i for i in excerpt_ids(r) if i in secs]
    body = "".join(excerpt_section(r, i, secs[i]).rstrip("\n") + "\n\n" for i in ids).rstrip("\n") + "\n"
    rows = (f" (§{SITUATIONAL}: named rows only; " if SITUATIONAL in ids else " (") + \
        f"§{LENGTH}: tier {r.letter} only)"
    return (f"<!-- generated by tools/build_shims.py: do not edit. -->\n"
            f"# Blocks for archetype {r.letter}: {r.name} (excerpt of §4)\n\n"
            f"From `guide/03-blocks.md`{rows}.\n\n"
            + body + "\n" + compact_checklist())


# --- the compact §6 checklist, carried at the end of every excerpt (E-09d) --------------------
# guide/04-checklist.md stays the full table (doctor's checklist_rows() counts it). The compact
# form keeps every row ID with a one-line test, so the verdict counts stay tied to the full table.

CHECKLIST_SRC = ROOT / "guide" / "04-checklist.md"
CHECK_COMPACT = {
    1: "Target resolved, source stated (argument/continuation/cwd/ask); conflicts in the lock",
    2: "Absolute repo anchor + branch; monorepo: in-scope root, siblings named OUT",
    3: "One sharp task statement at the top",
    4: "Contract named with precedence, hard rules pointed to; ancestor scan literal, "
       "no unscanned file named",
    5: "Ordered source of truth, annotated, with an exclusion or staleness warning; paths exist",
    6: "Skepticism with a falsifying artifact from THIS repo (N/A only for a delta E/J)",
    7: "Load-bearing claims at `file:line`; unchecked ones `[UNVERIFIED]`; nothing invented",
    8: "**Literal gates in this prompt**, each `(script)`/`(contract)`/`(derived)`; `test: NONE` "
       "if true; ⚠ destructive; read-only: side effects listed",
    9: "Baseline with expected delta and the honesty clause (read-only: unchanged)",
    10: "Scope bounded negatively, out-of-scope by path (L, A: one by ID/path/command, with why)",
    11: "Approval gate xor MODE block, else `N/A: read-only / commit-only` + writes",
    12: "Git posture explicit, matching the contract (read-only: \"no git writes\", verbs listed)",
    13: "Stop-list of what must not be faked, each with what it blocks and what unblocks it",
    14: "Report spec starts with the §4.14 `GENPROMPT-REPORT` line (`Prompt:` filled); negative "
        "confirmations; `git status` reconciled",
    15: "A terminal imperative",
    16: "Exactly one fenced block (4 backticks if nested); every `<…>` filled, `[generator: …]` "
        "stripped, worker variables `{…}`",
    17: "Doc paths follow §2.7, or chat-only with the reason; nothing renamed or renumbered",
    18: "Follows/amends/reviews in the header; prior work confirmed landed, partial said",
    19: "Every number labelled `verified by artifact` or `reported, not confirmed`; nothing run",
    20: "No leaked example specifics; volatile facts in §4.22; no attribution or finality "
        "claim; occupancy checked",
    21: "Length within budget (§4.21), lines ≤ 100 (lone unbreakable token excepted), or why",
    22: "Archived by `tools/archive.py`, result cited; `--dry-run`: N/A + lint result, no card; "
        "no python: FAIL",
    23: "Every TRAP, locked decision, stop-list and out-of-scope item has a \"because\" reason",
}
_CHECK_ROW = re.compile(r"^\|\s*(\d+)\s*\|", re.M)


def checklist_ids() -> list[int]:
    """The row IDs of the full §6 table in guide/04-checklist.md, in order."""
    text = CHECKLIST_SRC.read_text(encoding="utf-8") if CHECKLIST_SRC.exists() else ""
    return [int(n) for n in _CHECK_ROW.findall(text)]


def compact_checklist() -> str:
    n = len(CHECK_COMPACT)
    rows = "".join(f"| {i} | {CHECK_COMPACT[i]} |\n" for i in sorted(CHECK_COMPACT))
    return ("## §6 Emission checklist (compact; full rows: `guide/04-checklist.md`)\n\n"
            f"Grade all {n} rows (Step 6). Judgement rows 5, 6, 7, 10, 13 and 23 cite evidence on "
            "PASS; no bulk-passing; fix a FAIL or say why it ships. Read-only and commit-only "
            "archetypes meet code-writing rows in their own terms. Read a row's full text only "
            "before marking it FAIL.\n\n"
            "| # | Item |\n|---|---|\n" + rows)


def checklist_errors() -> list[str]:
    full = checklist_ids()
    if not full:
        return ["guide/04-checklist.md: no §6 rows found"]
    if full != sorted(CHECK_COMPACT):
        return [f"CHECK_COMPACT rows {sorted(CHECK_COMPACT)} differ from guide/04-checklist.md "
                f"rows {full}"]
    return []


def excerpt_errors() -> list[str]:
    """A named §4.x that 03-blocks lacks, or an INSERT the excerpt would not contain."""
    errors = []
    secs = block_sections()
    if not secs:
        return ["guide/03-blocks.md: no `### 4.x` sections found"]
    names = set(_ROW_NAME.findall(secs.get(SITUATIONAL, "")))
    for missing in sorted(names - set(SITUATIONAL_KEYS)):
        errors.append(f"guide/03-blocks.md §{SITUATIONAL} row {missing!r} has no SITUATIONAL_KEYS entry")
    for stale in sorted(set(SITUATIONAL_KEYS) - names):
        errors.append(f"SITUATIONAL_KEYS names {stale!r}, which §{SITUATIONAL} lacks")
    for r in ARCHETYPES:
        ids = set(excerpt_ids(r))
        text = archetype_text(r)
        for ref in sorted(set(_SEC_REF.findall(text)), key=_sec_key):
            if ref not in secs:
                errors.append(f"archetypes/{r.stem}.md names §{ref}, which guide/03-blocks.md lacks")
        for ref in _INSERT_REF.findall(text):
            if ref not in ids:
                errors.append(f"archetypes/{r.stem}.md INSERTs §{ref}, missing from its excerpt")
        if SITUATIONAL in ids and not situational_rows(r):
            errors.append(f"archetypes/{r.stem}.md names §{SITUATIONAL} but none of its rows")
        # E-10: a generator that composes §4.14 from the INSERT line alone must still emit the
        # report header (the baseline fix case did not), so one §4.14 INSERT must name it.
        inserts = _INSERT_414.findall(text)
        if inserts and not any("GENPROMPT-REPORT" in body for body in inserts):
            errors.append(f"archetypes/{r.stem}.md: no [INSERT §4.14 …] line names GENPROMPT-REPORT")
    return errors + checklist_errors()


# --- guide/blocks/derive.md: the card-less derivation path (E-09d) ----------------------------
# guide/01-target-profile.md stays the single source. A run with no fresh card reads this excerpt
# (§2.0 plus the §2.9 card template), not all of guide/01; §2.0 names when a full section is needed.

PROFILE_SRC = ROOT / "guide" / "01-target-profile.md"
DERIVE = "derive"
LADDERS = ROOT / "stacks" / "ladders"
_SUB_HEAD = re.compile(r"^### (2\.\d+)\b", re.M)
_CARD_FENCE = re.compile(r"^```markdown\n.*?^```\n", re.M | re.S)
_EXCLUDE_BLOCK = re.compile(r"EXCLUDE = (.*?)\n```", re.S)


def profile_sections() -> dict[str, str]:
    """guide/01's §2 cut by `### 2.x` heading (verbatim; the last one runs to the file's end)."""
    text = PROFILE_SRC.read_text(encoding="utf-8") if PROFILE_SRC.exists() else ""
    heads = list(_SUB_HEAD.finditer(text))
    return {m.group(1): text[m.start():(heads[i + 1].start() if i + 1 < len(heads) else len(text))]
            for i, m in enumerate(heads)}


def derive_excerpt() -> str:
    secs = profile_sections()
    card = _CARD_FENCE.search(secs.get("2.9", ""))
    return ("<!-- generated by tools/build_shims.py from guide/01-target-profile.md: do not edit. -->\n"
            "# Profile derivation (excerpt of §2: §2.0 and the §2.9 card template)\n\n"
            "Read this only when PROTOCOL Step 2 finds no fresh card. Section numbers refer to "
            "`guide/01-target-profile.md`.\n\n"
            + secs.get("2.0", "").rstrip("\n") + "\n\n"
            "### 2.9 The profile card (template)\n\n"
            + (card.group(0) if card else ""))


def derive_errors() -> list[str]:
    """§2.0 must exist, copy §2.1's EXCLUDE list exactly, and name every ladder file."""
    secs = profile_sections()
    s20 = secs.get("2.0", "")
    if not s20:
        return ["guide/01-target-profile.md: no `### 2.0` section (the derivation path)"]
    errors = []
    if not _CARD_FENCE.search(secs.get("2.9", "")):
        errors.append("guide/01-target-profile.md §2.9: no ```markdown card template")
    m = _EXCLUDE_BLOCK.search(secs.get("2.1", ""))
    want = m.group(1).split() if m else []
    tick = re.search(r"\(§2\.1, copied here\):\s*`([^`]*)`", s20)
    if not want or not tick or tick.group(1).split() != want:
        errors.append("guide/01 §2.0 step 1: the EXCLUDE copy differs from §2.1")
    have = sorted(p.stem for p in LADDERS.glob("*.md"))
    lad = re.search(r"one of `([^`]*)`", s20)
    if LADDERS.is_dir() and (not lad or sorted(lad.group(1).split()) != have):
        errors.append(f"guide/01 §2.0 step 4: the ladder names differ from stacks/ladders/ ({' '.join(have)})")
    for ref in sorted(set(re.findall(r"§(2\.\d+)", s20)) - set(secs)):
        errors.append(f"guide/01 §2.0 names §{ref}, which guide/01 lacks")
    return errors


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
    errors = table_errors() + excerpt_errors() + derive_errors()
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
    generated_dirs = (COMMANDS, ROOT / BLOCKS_DIR)
    for p in sorted({f for d in generated_dirs for f in d.glob("*.md")} - set(exp)):
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
        n_blk = sum(1 for p in exp if p.parent == ROOT / BLOCKS_DIR)
        say(f"commands: {len(exp) - n_blk} expected, excerpts: {n_blk} expected "
            f"(incl. {DERIVE}.md), {bad} differ/extra")
        say(f"docs: {len(docs)} with a generated region, {docs_bad} differ")
    return 1 if (check and (bad or docs_bad)) or missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
