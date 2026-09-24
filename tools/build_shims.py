"""Build the plugin's command files (commands/*.md) from one table.

The command files are thin: frontmatter (description, argument-hint, allowed-tools) plus @-includes
of PROTOCOL.md and the one archetype/utility file the command needs, with an explicit Read fallback.
Every command shares ALLOWED_TOOLS, so the permission baseline cannot drift between commands.

Paths inside the command files are written with ${CLAUDE_PLUGIN_ROOT}, which Claude Code expands
when a plugin command loads, so the plugin works wherever it is installed. The generator's own
writable folder is ~/.genprompt/ (the archive and the personal rules), outside every repo and
outside the plugin cache, which is replaced on every plugin update.

Usage:  python tools/build_shims.py           write any command file that differs
        python tools/build_shims.py --check   compare only; exit 1 on any difference (doctor uses this)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

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

# letter, command, file stem, archetype name, description, argument hint
ARCHETYPES = [
    ("A", "redesign", "A-redesign", "Single-artifact redesign",
     "Generate a senior-level redesign/refactor prompt for one file (screen, component, module)",
     "<file path> (<screen|dialog|component|module>)"),
    ("B", "audit", "B-audit", "Audit / read-only assessment",
     "Generate a read-only audit prompt (one doc with a ranked backlog, no code)",
     "<area to assess>"),
    ("C", "kickoff", "C-kickoff", "Kickoff with dirty WIP",
     "Generate a kickoff prompt for a unit with uncommitted WIP in the tree",
     "<unit to start>"),
    ("D", "slice", "D-slice", "Slice execution",
     "Generate a slice-execution prompt (one vertical slice, with checkpoints)",
     "Slice <ID>, scope: <bullets>"),
    ("E", "approve", "E-approve", "Approval / rulings / amendment",
     "Generate an approval/rulings prompt: lock decisions, rule on findings, or amend a sent prompt",
     "decisions: <list>; order: <...>  |  amend <prior prompt>"),
    ("F", "plan", "F-plan", "Planning-only",
     "Generate a planning-only prompt (one plan doc with stable ids, no code)",
     "<unit> <backend|frontend|cross-repo>"),
    ("G", "greenfield", "G-greenfield", "Greenfield from a reference repo",
     "Generate a greenfield prompt that studies a reference repo first, then builds",
     "<layer> studying <reference repo>"),
    ("H", "commit", "H-commit", "Commit & push (incl. verify+commit)",
     "Generate a commit-and-push prompt for a scoped body of work (or verify-then-commit)",
     "<work to commit> [verify+]"),
    ("I", "roadmap", "I-roadmap", "Roadmap / backlog execution",
     "Generate a roadmap/backlog-execution prompt (drive a whole backlog doc to done)",
     "drive <doc> to done"),
    ("J", "next", "J-next", "Continuation",
     "Generate the NEXT prompt from a pasted worker stop-report (or a closeout if nothing is left)",
     "<paste the worker's report, or nothing if it is already in the chat>"),
    ("K", "resume", "K-resume", "Resume after compaction",
     "Generate a resume-after-compaction prompt (rebuild lost worker context, then continue)",
     "<unit/slice the worker was mid-way through>"),
    ("L", "fix", "L-fix", "Defect-driven fix slice",
     "Generate a defect-driven fix prompt (per-defect repro, acceptance, false positives)",
     "<defect list, or the audit/report that found them>"),
    ("M", "onboard", "M-onboard", "Onboard / discovery",
     "Generate an onboarding prompt: map an unfamiliar or empty repo and draft its CLAUDE.md contract",
     "[repo]"),
    ("N", "design", "N-design", "Design / spike / ADR",
     "Generate a design prompt: ADR, API contract, schema/ERD, design-system mapping or spike (no production code)",
     "<ADR | API contract | schema | design system | spike>: <decision>"),
    ("O", "test", "O-test", "Test engineering",
     "Generate a test-engineering prompt: write missing tests, fix vacuous/flaky tests, build a harness",
     "<area | coverage target | flaky or vacuous tests>"),
    ("P", "review", "P-review", "Code review",
     "Generate a code-review prompt for a diff, branch, PR or recent commits (findings only, no edits)",
     "<base..head | branch | PR number | last N commits>"),
    ("Q", "security", "Q-security", "Security review and hardening",
     "Generate a security prompt: threat model, authz/uploads/secrets/headers review, then safe fixes",
     "<area | whole app>"),
    ("R", "perf", "R-perf", "Performance",
     "Generate a performance prompt: measure first, then optimise with before/after numbers",
     "<symptom or target metric>"),
    ("S", "upgrade", "S-upgrade", "Upgrade and migration",
     "Generate an upgrade/migration prompt: framework or dependency majors, ORM/platform/data moves, staged",
     "<package> <from> -> <to>  |  <migration>"),
    ("T", "release", "T-release", "Release and deploy",
     "Generate a release/deploy prompt: version, changelog, runbook, smoke, rollback, approval per action",
     "<version | environment | handover>"),
    ("U", "hotfix", "U-hotfix", "Hotfix / incident",
     "Generate a hotfix prompt for a live incident: triage, mitigate, root cause, regression test, postmortem",
     "<symptom, since when, who is affected>"),
    ("V", "cleanup", "V-cleanup", "Cleanup / maintenance",
     "Generate a cleanup prompt: dead code, feature removal, restore-green, refactor with no behaviour change",
     "<dead code | removal | restore-green | refactor target>"),
    ("W", "docs", "W-docs", "Documentation",
     "Generate a documentation prompt: README, API docs, runbooks, admin/handover guides checked against code",
     "<doc> for <audience>"),
]

# command, extra include files, description, argument hint
UTILITIES = [
    ("help", ["utilities/help.md", "archetypes/README.md", "guide/08-grammar.md"],
     "genprompt picker: which command fits a goal, with flags and examples (no prompt emitted)",
     "[goal, e.g. 'I need to upgrade Laravel']"),
    ("history", ["utilities/history.md"],
     "Show a repo's recent genprompt prompts, the follows chain and the profile status",
     "[repo] [n]"),
    ("doctor", ["utilities/doctor.md"],
     "Run the genprompt integrity check on the rules suite and the prompt archive",
     "[--suite | --archive]"),
    ("learn", ["utilities/learn.md", "guide/00-index.md"],
     "Save a lesson as a personal genprompt rule in ~/.genprompt/local-rules.md (shows the diff first)",
     "<rule or lesson>"),
    ("profile", ["utilities/profile.md", "guide/01-target-profile.md", "stacks/stack-matrix.md"],
     "Derive or refresh a repo's genprompt profile card (no prompt emitted)",
     "[repo] [--dry-run]"),
]


def yaml_str(value: str) -> str:
    # A JSON string is a valid YAML double-quoted scalar: safe for ': ', '#', '[' and '<'.
    return json.dumps(value, ensure_ascii=False)


def frontmatter(desc: str, hint: str, extra: str = "") -> str:
    return (f"---\ndescription: {yaml_str(desc)}\nargument-hint: {yaml_str(hint)}\n"
            f"allowed-tools: {ALLOWED_TOOLS}{extra}\n---\n")


def includes(files: list[str]) -> str:
    inc = "\n".join(f"@{PLUGIN_ROOT}/{f}" for f in ["PROTOCOL.md", *files])
    reads = ", ".join(f"`{PLUGIN_ROOT}/{f}`" for f in ["PROTOCOL.md", *files])
    return (f"{inc}\n\n"
            f"Paths for this run: the genprompt root (these rules, read-only) is `{PLUGIN_ROOT}`. "
            f"The genprompt home (the archive and your personal rules) is `{USER_HOME}/`.\n\n"
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
    return (frontmatter(desc, hint, extra) + "\n" + includes(files) +
            f"\nUtility `/genprompt:{cmd}`: follow `utilities/{cmd}.md`. It emits no worker prompt.\n\n"
            f"Request: $ARGUMENTS\n")


def root_shim() -> str:
    return (frontmatter("Generate a ready-to-paste Claude Code prompt (picks the archetype from the "
                        "request; auto-targets the current repo)",
                        f"[task, or a pasted worker report, or empty for the picker]   {FLAGS}")
            + "\n" + includes(["archetypes/README.md"]) +
            f"\nEntry point `/genprompt:{ENTRY}`. Pick the archetype from the request using the picker "
            "in `archetypes/README.md`, then Read that archetype's file and follow PROTOCOL Steps 1–7. "
            "A pasted worker stop-report with no instruction means archetype J (`:next`). An empty "
            "request: resolve the target anyway, then offer the picker in one message, instead of "
            "asking twice.\n\nRequest: $ARGUMENTS\n")


def table_errors() -> list[str]:
    errors = []
    cmds = [ENTRY] + [r[1] for r in ARCHETYPES] + [u[0] for u in UTILITIES]
    letters = [r[0] for r in ARCHETYPES]
    for name, seq in (("command", cmds), ("letter", letters)):
        dup = sorted({x for x in seq if seq.count(x) > 1})
        if dup:
            errors.append(f"duplicate {name}(s) in the tables: {', '.join(dup)}")
    return errors


def expected() -> dict[Path, str]:
    out = {COMMANDS / f"{ENTRY}.md": root_shim()}
    for row in ARCHETYPES:
        out[COMMANDS / f"{row[1]}.md"] = archetype_shim(*row)
    for row in UTILITIES:
        out[COMMANDS / f"{row[0]}.md"] = utility_shim(*row)
    return out


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
    if check:
        say(f"commands: {len(exp)} expected, {bad} differ/extra")
    return 1 if (check and bad) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
