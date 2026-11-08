#!/usr/bin/env python3
"""Generate genprompt's eval cases for `claude plugin eval` from one spec.

Each case directory (evals/cases/<name>/) gets prompt.md, case.yaml, scaffold.sh and graders/*.md.
They are generated so the shared graders cannot drift between cases, the same way
tools/build_shims.py generates commands/. Never edit evals/cases/ by hand.

    python evals/build_cases.py          # write evals/cases/
    python evals/build_cases.py --check  # exit 1 if evals/cases/ differs from the spec
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
CASES = EVALS / "cases"
FIXTURE = EVALS / "fixtures" / "ledgerlite"
OVERLAYS = EVALS / "fixtures" / "overlays"

FLAGS = "--go --dry-run"
# The generator only reads. Bash cannot be granted on Windows (the eval sandbox refuses an
# unconfined shell), so the baseline runs without it; see README "Bash and git".
ALLOWED_TOOLS = "[Read, Glob, Grep]"
MAX_TURNS = 80
TIMEOUT = 1200

NEXT_REPORT = """\
GENPROMPT-REPORT · Repo: ledgerlite (the current directory) · Branch: feat/s-02-csv-export · \
HEAD: 988bf1d · Prompt: slice-s-02-csv-export · Gates: npm test → 10 pass, 0 fail; \
npm run lint → 0 problems · Status: partial

Checkpoint A of slice S-02 is done and committed (988bf1d "feat: S-02 checkpoint A, CSV rows for
line items"): src/csv.js has quote() and toCsvRows(), with tests in test/csv.test.js.
Deferred to checkpoint B: the TOTAL row and the --csv flag in src/cli.js. I did not touch the CLI.
No push, no PR. Working tree clean."""

# name → spec. `variant` picks the scaffold; `cap` is the §4.21 tier cap in block lines.
SPEC: dict[str, dict] = {
    "slice": {
        "variant": "base",
        "cap": 260, "cap_multi": 320,
        "request": "/genprompt:slice Slice S-02, scope: CSV export as described in docs/ROADMAP.md "
                   "(a --csv flag, RFC 4180 quoting, one row per line item plus a TOTAL row) "
                   f"{FLAGS}",
        "label": r"\bD\b",
        "scope_fail": "it also tells the worker to build S-03 tax lines or S-04 multi-currency, "
                      "or to fix unrelated code without saying it is out of scope",
        "artifact": "the TOTAL row is built on invoiceTotal(), and src/invoice.js:14 starts the "
                    "subtotal loop at i = 1, so the first line item is dropped; "
                    "test/invoice.test.js has no multi-line invoice test, so `npm test` stays "
                    "green despite that",
    },
    "fix": {
        "variant": "base",
        "cap": 200,
        "request": "/genprompt:fix invoice totals are too low: `npm start -- examples/sample.json` "
                   "prints TOTAL 40.50 EUR, but 2x12.50 + 40.00 + 5.00 = 70.00 minus 10% is "
                   f"63.00 EUR {FLAGS}",
        "label": r"\bL\b",
        "scope_fail": "it also asks for the CSV export, tax lines or a refactor of src/cli.js",
        "artifact": "src/invoice.js:14 (`for (let i = 1; ...`) skips the first line item; "
                    "test/invoice.test.js only checks an empty invoice and single lineTotal "
                    "calls, so `npm test` is green while the bug is live; examples/sample.json "
                    "reproduces 40.50 vs 63.00",
    },
    "redesign": {
        "variant": "base",
        "cap": 200,
        "request": "/genprompt:redesign src/cli.js: split argument parsing, validation and "
                   "printing into small functions; keep the CLI's output and exit codes identical "
                   f"{FLAGS}",
        "label": r"\bA\b",
        "scope_fail": "it lets the worker change src/invoice.js or src/format.js behaviour, "
                      "add dependencies, or change output and exit codes",
        "artifact": "no test covers src/cli.js (test/ has only invoice.test.js and "
                    "format.test.js), so behaviour must be pinned first, e.g. by characterisation "
                    "tests over examples/sample.json and the exit codes 0/1/2 in src/cli.js",
    },
    "next-hybrid": {
        "variant": "s02a",
        "cap": 260,
        "request": f"/genprompt:next {FLAGS}\n\n{NEXT_REPORT}",
        "label": r"J\s*\+\s*D",
        "scope_fail": "it starts S-03 or S-04, or re-does checkpoint A instead of continuing "
                      "with checkpoint B",
        "artifact": "the report says `npm test` gives 10 passes, but the test files declare 9 "
                    "tests (4 in test/invoice.test.js, 2 in test/format.test.js, 3 in "
                    "test/csv.test.js), so that number must be labelled reported, not confirmed, "
                    "or flagged as a mismatch; also src/invoice.js:14 makes any TOTAL row wrong",
    },
    "commit": {
        "variant": "s02dirty",
        "cap": 200,
        "request": "/genprompt:commit S-02 CSV export (checkpoint B) is finished in the working "
                   f"tree; commit it on the current branch and do not push {FLAGS}",
        "label": r"\bH\b",
        "scope_fail": "it lets the worker sweep in scratch-probe.js or .env, use `git add -A` / "
                      "`git add .`, push, or commit to main",
        "artifact": "docs/CSV-EXPORT.md documents a --csv flag that src/cli.js does not "
                    "implement; test/csv.test.js pins `TOTAL,,,0`, which is only true because "
                    "src/invoice.js:14 skips the first line; scratch-probe.js is a scratch file",
    },
    "plan": {
        "variant": "base",
        "cap": 350,
        "request": "/genprompt:plan S-03 tax lines from docs/ROADMAP.md: a per-line VAT rate and "
                   f"a tax subtotal, totals still in integer cents {FLAGS}",
        "label": r"\bF\b",
        "scope_fail": "it tells the worker to write production code, or plans S-02 or S-04 "
                      "instead of S-03",
        "artifact": "any tax subtotal built on subtotal() inherits src/invoice.js:14, which "
                    "skips the first line item; CLAUDE.md says new docs go in docs/ as "
                    "upper-case kebab, so the plan doc name is checkable",
    },
    # E-06b: two commit cases. "commit" (above) is the refusal case: the work is unfinished, so
    # the right output is a refusal or a gated verify+commit. "commit-finished" is committable
    # work. It joined the baseline set after the Phase-1 run; its first score is in CP4.md.
    "commit-finished": {
        "variant": "s02finished",
        "cap": 200,
        "request": "/genprompt:commit S-02 CSV export (checkpoint B) is finished in the working "
                   f"tree; commit it on the current branch and do not push {FLAGS}",
        "label": r"\bH\b",
        "scope_fail": "it lets the worker sweep in scratch-probe.js or .env, use `git add -A` / "
                      "`git add .`, push, or commit to main",
        "artifact": "scratch-probe.js is an untracked scratch file (its line 1 says so) and .env "
                    "is gitignored, so both must stay out of the commit; the gates must be re-run "
                    "before committing rather than trusted from the request",
    },
}

# Cases outside the baseline set carry the tag "extra" (run with run.py --tag extra).
EXTRA: dict[str, dict] = {
    # E-16: monorepo scoping. Run in CP5 once workspace detection lands; no baseline yet.
    "slice-monorepo": {
        "variant": "mono",
        "cap": 260, "cap_multi": 320,
        "package": "packages/ledger-core", "sibling": "ledger-web",
        "request": "/genprompt:slice Slice C-02, scope: rounding modes for splitCents in "
                   "ledger-core as described in docs/ROADMAP.md (`largest-remainder` and "
                   f"`first-gets-rest`, unknown modes throw) {FLAGS}",
        "label": r"\bD\b",
        "scope_fail": "it lets the worker edit packages/ledger-web, run ledger-web's scripts "
                      "(test, lint or build) or the unfiltered root scripts, or starts W-05",
        "artifact": "the root `npm test` / `npm run lint` run every workspace, ledger-web included, "
                    "so a green root run proves nothing about ledger-core alone; splitCents in "
                    "packages/ledger-core/src/money.js has no mode parameter yet, and "
                    "packages/ledger-core/test/money.test.js covers only the largest-remainder "
                    "split",
    },
}

# Archetype letters and the archive filename's command words, for doctor --prompt's length tier.
ARCHIVE_META = {"slice": ("D", "slice"), "fix": ("L", "fix"), "redesign": ("A", "redesign"),
                "next-hybrid": ("J+D", "next+slice"), "commit": ("H", "commit"),
                "plan": ("F", "plan"), "commit-finished": ("H", "commit"),
                "slice-monorepo": ("D", "slice")}
VARIANT_ROOT = {"mono": EVALS / "fixtures" / "tallyhub"}

VARIANT_CALLS = {
    "base": ["base_repo"],
    "s02a": ["base_repo", "s02_checkpoint_a"],
    "s02dirty": ["base_repo", "s02_checkpoint_a", "s02_uncommitted"],
    "s02finished": ["base_repo", "subtotal_fix_merged", "s02_checkpoint_a", "s02_finished"],
    "mono": ["mono_repo"],
}
VARIANT_OVERLAYS = {"base": [], "s02a": ["s02-checkpoint-a"],
                    "s02dirty": ["s02-checkpoint-a", "s02-uncommitted"],
                    "s02finished": ["subtotal-fix", "s02-checkpoint-a", "s02-finished"],
                    "mono": []}
# Facts that differ per variant (SHAs from `python evals/run.py --print-shas`).
VARIANT_SHAS = {
    "base": "",
    "s02a": ", 988bf1d \"feat: S-02 checkpoint A ...\" on feat/s-02-csv-export (checked out)",
    "s02dirty": ", 988bf1d \"feat: S-02 checkpoint A ...\" on feat/s-02-csv-export (checked out); "
                "uncommitted: src/csv.js, test/csv.test.js modified, docs/CSV-EXPORT.md, "
                "scratch-probe.js untracked, .env ignored",
    "s02finished": ", f59ebef \"fix: count the first line item in subtotal\" and its merge "
                   "c14ba10 on main, b45f80e \"feat: S-02 checkpoint A ...\" on "
                   "feat/s-02-csv-export (checked out); uncommitted: src/cli.js, src/csv.js, "
                   "test/csv.test.js modified, docs/CSV-EXPORT.md and scratch-probe.js untracked, "
                   ".env ignored; npm test gives 11 passing tests and lint is clean",
}
DEFECT = {
    "s02finished": "- The once-planted defect is fixed: src/invoice.js:14 now starts at i = 0 "
                   "(commit f59ebef), and test/invoice.test.js covers a multi-line invoice.",
}


def fixture_files(variant: str) -> dict[str, int]:
    """Relative path → line count of every file in the scaffolded workspace for this variant."""
    files: dict[str, int] = {}
    for root in [VARIANT_ROOT.get(variant, FIXTURE)] + [OVERLAYS / o for o in VARIANT_OVERLAYS[variant]]:
        for p in sorted(root.rglob("*")):
            if p.is_file():
                files[p.relative_to(root).as_posix()] = len(
                    p.read_text(encoding="utf-8").splitlines())
    if variant in ("s02dirty", "s02finished"):
        files[".env"] = 1
    return dict(sorted(files.items()))


def facts(variant: str) -> str:
    listing = "\n".join(f"- {path} ({n} lines)" for path, n in fixture_files(variant).items())
    if variant == "mono":
        return f"""\
Ground truth about the made-up npm-workspaces monorepo "tallyhub" (the run's working directory):
- Root package.json: workspaces ["packages/*"]; scripts test (`npm run test --workspaces
  --if-present`) and lint (`npm run lint --workspaces --if-present`), which run EVERY workspace.
- packages/ledger-core/package.json (IN scope): scripts test (`node --test`), lint
  (`node scripts/lint.js`). No build script.
- packages/ledger-web/package.json (OUT of scope): scripts test, lint and build.
- CLAUDE.md: Claude works in packages/ledger-core only; packages/ledger-web belongs to the web
  team, never edit it or run its scripts; run the gates of the package you changed (the root
  scripts run every workspace); never commit to main; feat/<slug> or fix/<slug>; Conventional
  Commits; stage by explicit path; never push without the maintainer's OK.
- docs/ROADMAP.md: C-02 (ledger-core) adds rounding modes to splitCents; W-05 is ledger-web's.
- Correct gates for this task are ledger-core's own: e.g. `npm test -w ledger-core` /
  `npm run lint -w ledger-core` (or `--workspace=ledger-core`, or the same scripts run from
  packages/ledger-core). Bare root `npm test` / `npm run lint` would also run ledger-web.
- Git repo in a temp directory; one commit ef6113e on main. Citing .git files is legitimate.
- A path cited relative to the in-scope package counts as that package's file: `src/money.js:12`
  or `test/money.test.js:6` mean packages/ledger-core/src/money.js and
  packages/ledger-core/test/money.test.js. Check its line number against that file below.
- Files in the workspace, with line counts:
{listing}"""
    sha_extra = VARIANT_SHAS[variant]
    defect = DEFECT.get(variant, "- Planted defect: src/invoice.js:14 starts the subtotal loop at "
                                 "i = 1, dropping the first line.")
    return f"""\
Ground truth about the made-up repo "ledgerlite" (the run's working directory):
- package.json scripts: test (`node --test`), lint (`node scripts/lint.js`), start
  (`node src/cli.js`). There is no build, typecheck or format script.
- CLAUDE.md: never commit to main; branches feat/<slug> or fix/<slug>; Conventional Commits;
  stage by explicit path; never push or open a PR without the maintainer's OK; run `npm test`
  and `npm run lint` before every commit; new docs go in docs/<TOPIC>.md.
{defect}
- The workspace is a git repo in a temp directory, so its absolute path is a temp path. Citing
  git's own files (.git/HEAD, .git/logs/HEAD, refs) is legitimate. Real commits: 9c672ba
  "chore: scaffold ledgerlite", 82de56a "feat: S-01 ...", 4c804d4 the S-01 merge on main{sha_extra}.
- Files in the workspace, with line counts:
{listing}"""


def g(name: str, front: str, body: str = "") -> tuple[str, str]:
    return f"graders/{name}.md", f"---\n{front.strip()}\n---\n" + (f"\n{body.strip()}\n" if body else "")


def case_files(name: str, spec: dict) -> dict[str, str]:
    variant = spec["variant"]
    out: dict[str, str] = {}
    header = "<!-- generated by evals/build_cases.py; edit the spec there, not this file -->\n"
    out["prompt.md"] = (
        f"---\nname: {name}\ndescription: genprompt {name} against the "
        f"{VARIANT_ROOT.get(variant, FIXTURE).name} fixture\n"
        f"tags: [{'extra' if name in EXTRA else 'baseline'}, {name}]\nruns: 1\n"
        f"max_turns: {MAX_TURNS}\n"
        f"timeout_seconds: {TIMEOUT}\nallowed_tools: {ALLOWED_TOOLS}\n---\n\n"
        f"{spec['request']}\n")
    out["case.yaml"] = (f"# generated by evals/build_cases.py\nschema_version: \"1.1\"\n"
                        f"name: {name}\ncontext:\n  scaffold_script: scaffold.sh\n")
    out["scaffold.sh"] = (
        "#!/usr/bin/env bash\n# generated by evals/build_cases.py\nset -euo pipefail\n"
        'source "$(dirname "${BASH_SOURCE[0]}")/../../fixtures/scaffold-lib.sh"\n'
        + "".join(f"{call}\n" for call in VARIANT_CALLS[variant]))
    graders = [
        g("lock-present", "type: regex\npattern: \"TARGET LOCK\""),
        g("no-generator-marker", "type: regex\npattern: \"\\\\[generator:\"\nmatch: not_contains"),
        g("dry-run-declared", "type: regex\npattern: \"DRY RUN\""),
        g("protocol-loaded", "type: regex\npattern: \"GENPROMPT-PROTOCOL v3 LOADED\"\n"
                             "target: trace"),
        # The lock's Archetype line must name the expected letter(s), e.g. "Archetype   L: Fix".
        g("archetype-label", "type: regex\npattern: '"
          + r"Archetype[^\n]{0,30}?" + spec["label"] + "'"),
        g("no-write", "type: tool_used\ntool: Write\nmin: 0\nmax: 0"),
        g("no-edit", "type: tool_used\ntool: Edit\nmin: 0\nmax: 0"),
        *([
            # Monorepo: the lock must say monorepo and name the sibling as out of scope.
            g("lock-monorepo", "type: regex\npattern: 'monorepo'\nflags: i"),
            g("lock-sibling-out", "type: regex\npattern: '"
              + spec["sibling"] + r"[^\n]{0,60}\bOUT\b|\bOUT\b[^\n]{0,80}" + spec["sibling"]
              + "'\nflags: i"),
        ] if spec.get("sibling") else []),
        g("rubric-grounding", "type: llm", f"""\
{header}You are grading a worker prompt that a prompt generator wrote for a made-up repo.

{facts(variant)}

PASS if every file path and `path:line` the response cites is in the list above, with a line
number no larger than that file's line count; every gate command it gives uses a script that
package.json defines (or is plain `node`/`git`); its claims about the code agree with the ground
truth; and anything it could not check is marked [UNVERIFIED] instead of asserted.
FAIL if it cites a file that is not in the list, a line past the end of a file, a script that does
not exist (such as `npm run build` or a type check), or states something that contradicts the
ground truth as fact."""),
        g("rubric-scope", "type: llm", f"""\
{header}You are grading a worker prompt that a prompt generator wrote for this request:

{spec['request']}

PASS if the prompt bounds scope negatively: it says what to do only, what not to start yet, and
names out-of-scope items by path, ID or command.
FAIL if scope is only described positively, or if {spec['scope_fail']}."""),
        g("rubric-skepticism", "type: llm", f"""\
{header}You are grading a worker prompt that a prompt generator wrote for a made-up repo.

{facts(variant)}

PASS if the prompt tells the worker to distrust a specific claim or green signal and names a
concrete falsifying artifact from THIS repo that the worker can check. Examples of real artifacts
here: {spec['artifact']}. Any other artifact that really exists in the files above also counts.
FAIL if the skepticism is generic ("be careful", "verify your work") with no artifact from this
repo, or if the artifact it names does not exist in the files above."""),
    ]
    out.update(dict(graders))
    return out


def control_files() -> dict[str, str]:
    """A negative control: the model echoes a deliberately broken prompt. Every grader that can
    see the defect must FAIL here, or the grader measures nothing (run.py checks this)."""
    bad = (EVALS / "fixtures" / "samples" / "bad-emission.md").read_text(encoding="utf-8")
    files = case_files("slice", SPEC["slice"])
    files["prompt.md"] = (
        "---\nname: control-bad-emission\ndescription: negative control, every grader should "
        "fail\ntags: [control]\nruns: 1\nmax_turns: 6\nmodel: haiku\n"
        "allowed_tools: [Read, Glob, Write]\n---\n\n"
        "Do two things. First, use the Write tool to create a file named note.txt containing the "
        "word scratch. Second, reply with the text between the BEGIN and END lines below, "
        "verbatim, and nothing else.\n\nBEGIN\n" + bad + "END\n")
    files["case.yaml"] = files["case.yaml"].replace("name: slice", "name: control-bad-emission")
    return files


def build() -> dict[Path, str]:
    out: dict[Path, str] = {}
    for name, spec in {**SPEC, **EXTRA}.items():
        for rel, text in case_files(name, spec).items():
            out[CASES / name / rel] = text
    for rel, text in control_files().items():
        out[EVALS / "controls" / "bad-emission" / rel] = text
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if the generated files drifted")
    args = ap.parse_args()
    want = build()
    roots = [CASES, EVALS / "controls"]
    have = {p for r in roots if r.exists() for p in r.rglob("*") if p.is_file()}
    drift = [p for p, t in want.items()
             if not p.exists() or p.read_text(encoding="utf-8") != t]
    extra = sorted(have - set(want))
    if args.check:
        for p in drift:
            print(f"DRIFT {p.relative_to(EVALS)}")
        for p in extra:
            print(f"EXTRA {p.relative_to(EVALS)}")
        print(f"build_cases --check: {len(drift)} drifted, {len(extra)} extra, {len(want)} files")
        return 1 if drift or extra else 0
    for p in extra:
        p.unlink()
    for p, t in want.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t, encoding="utf-8", newline="\n")
    print(f"build_cases: wrote {len(want)} files ({len(drift)} changed, {len(extra)} removed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
