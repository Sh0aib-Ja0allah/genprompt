"""genprompt archive writer: write one prompt file and its shard row, deterministically.

Usage:  python3 tools/archive.py [--dry-run] [<parts.json> | -]      (no file, or '-', reads stdin)

The generator composes the parts; this tool does the writing, so the archive follows §10
(guide/06-library.md) and PROTOCOL Step 6 every time instead of depending on the model.

Input: one JSON object.
  required  key, date, archetype, slug, task
  prompt    repo, path, follows (default "-"), and the body: either "body" (everything after
            line 1) or the parts "header_table", "grounding", "prompt" (the fenced block, fences
            included), "self_check", and optional "rule" (the transferable rule)
  optional  flags, via, lock (written as trailing header fields when given)
  status    archetype "none" writes only a status row (file "-"); task must start "status:"

What it does:
  1. checks the fields (key, date, letters, slug, task: <= 200 chars, no '|', '·' or em-dash)
  2. composes <home>/generated-prompts/<key>/<date>-<cmd>[+<cmd>]-<slug>.md with the exact
     line-1 header, and runs doctor's per-file lint (the same code as `doctor.py --prompt`)
  3. refuses to overwrite an existing file (an archive file is a record)
  4. writes the file, appends the 5-field row to by-repo/<key>.tsv (writing the three §10 header
     lines first for a new shard), then re-runs the lint on the file as written

Nothing is written if a field check or the lint fails. --dry-run writes nothing and prints what it
would write. GENPROMPT_HOME overrides the genprompt home (default ~/.genprompt).

Exit codes: 0 archived (or dry run clean) · 1 validation failed · 2 bad input · 3 refused
(the file already exists). Every failure is printed; success is never reported after a FAIL.
Standard library only.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

_spec = importlib.util.spec_from_file_location("genprompt_doctor", Path(__file__).resolve().parent / "doctor.py")
doctor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(doctor)

KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
EXIT_OK, EXIT_INVALID, EXIT_INPUT, EXIT_EXISTS = 0, 1, 2, 3


def say(msg: str = "") -> None:
    sys.stdout.write(f"{msg}\n")


def load_parts(arg: str | None) -> dict:
    raw = sys.stdin.read() if arg in (None, "-") else Path(arg).read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("the input must be one JSON object")
    return {k: (v.strip() if isinstance(v, str) and k not in BODY_PARTS + ("body",) else v)
            for k, v in data.items()}


BODY_PARTS = ("header_table", "grounding", "prompt", "self_check", "rule")


def field_problems(p: dict, cmd_by_letter: dict[str, str]) -> list[str]:
    out = []
    status = p.get("archetype") == "none"
    need = ["key", "date", "archetype", "slug", "task"] + ([] if status else ["repo", "path"])
    out += [f"missing field: {k}" for k in need if not p.get(k)]
    if out:
        return out
    if not KEY_RE.match(p["key"]):
        out.append(f"key {p['key']!r} is not lowercase kebab-case (§10.1)")
    if not doctor.DATE_RE.match(p["date"]):
        out.append(f"date {p['date']!r} is not YYYY-MM-DD")
    if not doctor.SLUG_RE.match(p["slug"]):
        out.append(f"slug {p['slug']!r} is not lowercase kebab-case, 60 characters at most")
    if not status:
        letters = p["archetype"].split("+")
        if not doctor.LABEL_RE.match(p["archetype"]) or any(x not in cmd_by_letter for x in letters):
            out.append(f"archetype {p['archetype']!r} is not known letters joined by +")
        if not (p.get("body") or p.get("prompt")):
            out.append("missing the body: give 'body', or the parts with at least 'prompt'")
    elif not p["task"].startswith("status:"):
        out.append("a status row's task must start with 'status:'")
    task = p["task"]
    if len(task) > doctor.TASK_CAP:
        out.append(f"task is {len(task)} characters (max {doctor.TASK_CAP})")
    for bad, name in (("|", "'|'"), ("·", "a middle dot"), ("—", "an em-dash"), ("\n", "a newline")):
        if bad in task:
            out.append(f"task contains {name}")
    for k in ("repo", "path", "follows", "flags", "via", "lock"):
        if isinstance(p.get(k), str) and (" | " in p[k] or "-->" in p[k] or "\n" in p[k]):
            out.append(f"{k} contains ' | ', '-->' or a newline, which would break the line-1 header")
    return out


def header_line(p: dict) -> str:
    fields = [("key", p["key"]), ("repo", p["repo"]), ("path", p["path"]), ("date", p["date"]),
              ("archetype", p["archetype"]), ("follows", p.get("follows") or "-")]
    fields += [(k, p[k]) for k in doctor.HEADER_OPTIONAL if p.get(k)]
    return "<!-- genprompt v3: " + " | ".join(f"{k}={v}" for k, v in fields) + " -->"


def compose(p: dict) -> str:
    if p.get("body"):
        body = p["body"].strip("\n")
    else:
        body = "\n\n".join(p[k].strip("\n") for k in BODY_PARTS if p.get(k))
    return f"{header_line(p)}\n\n{body}\n"


def file_name(p: dict, cmd_by_letter: dict[str, str]) -> str:
    cmds = "+".join(cmd_by_letter[x] for x in p["archetype"].split("+"))
    return f"{p['date']}-{cmds}-{p['slug']}.md"


def shard_text(shard: Path, p: dict, row_fields: list[str]) -> tuple[str, str]:
    """(full new shard text, the appended row). Appends below the last line (§10.3)."""
    if shard.exists():
        old = shard.read_text(encoding="utf-8-sig")
        sep = doctor.shard_separator(old.splitlines())
        row = ("\t" if sep == "\t" else " | ").join(row_fields)
        return (old if old.endswith("\n") or not old else old + "\n") + row + "\n", row
    row = " | ".join(row_fields)
    head = (f"# genprompt shard: {p['key']}  (path: {p.get('path') or '-'})\n"
            "# Fields: date | archetype | slug | file | task (<=200 chars)\n"
            "# schema: v3\n")
    return head + row + "\n", row


def report_lint(results) -> int:
    for check, ok, detail in results:
        say(f"{'PASS' if ok else 'FAIL'}  {check:20} {detail}")
    return sum(1 for _c, ok, _d in results if not ok)


def main(argv: list[str]) -> int:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")
    dry = "--dry-run" in argv
    rest = [a for a in argv if a != "--dry-run"]
    if len(rest) > 1 or any(a.startswith("--") for a in rest):
        say("usage: archive.py [--dry-run] [<parts.json> | -]")
        return EXIT_INPUT
    try:
        p = load_parts(rest[0] if rest else None)
    except (OSError, ValueError) as exc:
        say(f"FAIL  input  {exc}")
        return EXIT_INPUT

    cmd_by_letter = doctor.cmd_map()
    if not cmd_by_letter:
        say("FAIL  setup  cannot load the archetype table from tools/build_shims.py")
        return EXIT_INPUT
    problems = field_problems(p, cmd_by_letter)
    for msg in problems:
        say(f"FAIL  fields  {msg}")
    if problems:
        say("NOT ARCHIVED: fix the fields above.")
        return EXIT_INVALID

    archive = Path(doctor.ARCHIVE)
    shard = archive / "by-repo" / f"{p['key']}.tsv"
    status = p["archetype"] == "none"
    target = None if status else archive / p["key"] / file_name(p, cmd_by_letter)
    row_fields = [p["date"], p["archetype"], p["slug"], target.name if target else "-", p["task"]]
    new_shard, row = shard_text(shard, p, row_fields)

    text = ""
    if target is not None:
        text = compose(p)
        fails = report_lint(doctor.lint_prompt(text, target.name, cmd_by_letter))
        if fails:
            say(f"NOT ARCHIVED: {fails} lint check(s) failed. Fix the prompt and run again.")
            return EXIT_INVALID
        if target.exists():
            say(f"REFUSED  {target} already exists; an archive file is a record and is never overwritten.")
            return EXIT_EXISTS

    if dry:
        say(f"DRY RUN: nothing written.")
        if target is not None:
            say(f"would write  {target}  ({len(text.splitlines())} lines)")
            say(f"line 1       {text.splitlines()[0]}")
        say(f"would append {shard}{'' if shard.exists() else '  (new shard, with the 3 header lines)'}")
        say(f"row          {row}")
        return EXIT_OK

    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "x", encoding="utf-8", newline="\n") as fh:   # "x": never overwrite
            fh.write(text)
    shard.parent.mkdir(parents=True, exist_ok=True)
    shard.write_text(new_shard, encoding="utf-8", newline="\n")

    # Re-validate what is on disk: the file, and that the row parses back into the same 5 fields.
    fails = 0
    if target is not None:
        fails += report_lint(doctor.lint_prompt(target.read_text(encoding="utf-8"), target.name, cmd_by_letter))
    last = [ln for ln in shard.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")][-1]
    parsed = doctor.split_row(last, doctor.shard_separator(shard.read_text(encoding="utf-8").splitlines()))
    if parsed != row_fields:
        say(f"FAIL  shard-row  the appended row parses back as {parsed!r}")
        fails += 1
    if fails:
        say(f"ARCHIVE WRITTEN BUT INVALID: {fails} check(s) failed on disk. Report this as a FAIL.")
        return EXIT_INVALID
    if target is not None:
        say(f"ARCHIVED  {target}")
    say(f"ROW       {shard.name}: {row}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
