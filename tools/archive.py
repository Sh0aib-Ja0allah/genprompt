"""genprompt archive writer: write one prompt file and its shard row, deterministically.

Usage:  python3 tools/archive.py [--dry-run | --replace] [<parts.json> | -]   (default: stdin)
        python3 tools/archive.py --where   (print the resolved home; read-only, see below)

The generator composes the parts; this tool does the writing, so the archive follows §10
(guide/06-library.md) and PROTOCOL Step 6 every time instead of depending on the model.

Input: one JSON object.
  required  key, date, archetype, slug, task
  prompt    repo, path, follows (default "-"), and the body: either "body" (everything after
            line 1) or the parts "header_table", "grounding", "prompt" (the fenced block, fences
            included), "self_check", and optional "rule" (the transferable rule)
  vocab     flags, via, lock: required for every new prompt (values pinned in PROTOCOL Step 6
            item 2), written as trailing header fields; a missing or unknown value is a WARN from
            the lint (header-vocab), never a block
  sent      only with --send (guide/06-library.md §10.8): the bare session name the prompt was sent
            to, or "copy" when the user declined; omitted otherwise (E-12)
  status    archetype "none" writes only a status row (file "-"); task must start "status:"

Order: WRITE FIRST, THEN VALIDATE. The prompt is already printed in chat and may already be pasted
to a worker, so a gap in the archive (a broken follows chain) is worse than a flagged file.
  1. structural fields (key, date, letters, slug, repo/path) must be usable to name the record;
     if not, nothing can be written (exit 2). The task is normalised to fit the row (§10.3:
     <= 200 chars, no '|', '·', em-dash or newline) and each change is printed as WARN.
  2. writes <home>/generated-prompts/<key>/<date>-<cmd>[+<cmd>]-<slug>.md with the exact line-1
     header and appends the 5-field row below the last line of by-repo/<key>.tsv (a new shard
     first gets the three §10 header lines).
  3. runs doctor's per-file lint (the same code as `doctor.py --prompt`) on the file as written
     and checks that the row parses back into the same 5 fields.
  FAIL -> "ARCHIVED WITH ERRORS" with every failure, exit 1. WARN only -> exit 0.

An existing file is never overwritten by accident (exit 3, nothing written). --replace is the
deliberate fix-and-re-archive path: it overwrites that same file and rewrites its shard row in
place (never a second row). --dry-run writes nothing and prints what it would write plus the lint.
GENPROMPT_HOME overrides the genprompt home (default ~/.genprompt), through doctor.genprompt_home().
--where prints `home <absolute path>` and `local-rules <path> (present|absent)` and writes nothing,
so the generator can learn the home from the one script it may already run (E-21).

Exit codes: 0 archived (warnings allowed) · 1 archived with errors (or dry run with errors) ·
2 bad input, nothing written · 3 refused: the file exists and --replace was not given.
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
EXIT_OK, EXIT_ERRORS, EXIT_INPUT, EXIT_EXISTS = 0, 1, 2, 3
BODY_PARTS = ("header_table", "grounding", "prompt", "self_check", "rule")
USAGE = "usage: archive.py [--dry-run | --replace] [<parts.json> | -]  |  archive.py --where"


def say(msg: str = "") -> None:
    sys.stdout.write(f"{msg}\n")


def load_parts(arg: str | None) -> dict:
    raw = sys.stdin.read() if arg in (None, "-") else Path(arg).read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("the input must be one JSON object")
    return {k: (v.strip() if isinstance(v, str) and k not in BODY_PARTS + ("body",) else v)
            for k, v in data.items()}


def structural_problems(p: dict, cmd_by_letter: dict[str, str]) -> list[str]:
    """Problems that make it impossible to name or place the record. Nothing is written."""
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
    for k in ("repo", "path", "follows", "flags", "via", "lock", "sent"):
        if isinstance(p.get(k), str) and (" | " in p[k] or "-->" in p[k] or "\n" in p[k]):
            out.append(f"{k} contains ' | ', '-->' or a newline, which would break the line-1 header")
    return out


def normalise_task(task: str) -> tuple[str, list[str]]:
    """Make the task fit a shard row (§10.3). Returns (task, what changed)."""
    notes = []
    for bad, good, name in (("\r", "", "carriage return"), ("\n", " ", "newline"), ("|", "/", "'|'"),
                            ("·", "-", "middle dot"), ("—", "-", "em-dash")):
        if bad in task:
            task = task.replace(bad, good)
            notes.append(f"replaced {name}")
    if len(task) > doctor.TASK_CAP:
        task = task[: doctor.TASK_CAP - 3].rstrip() + "..."
        notes.append(f"cut to {doctor.TASK_CAP} characters")
    return task, notes


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


def new_shard_text(shard: Path, p: dict, row_fields: list[str], replace_file: str | None) -> tuple[str, str, str]:
    """(new shard text, the row, 'appended'|'replaced'|'new shard'). Rows go below the last line
    (§10.3); with replace_file, the existing row for that file is rewritten in place instead."""
    if not shard.exists():
        row = " | ".join(row_fields)
        head = (f"# genprompt shard: {p['key']}  (path: {p.get('path') or '-'})\n"
                "# Fields: date | archetype | slug | file | task (<=200 chars)\n"
                "# schema: v3\n")
        return head + row + "\n", row, "new shard"
    old = shard.read_text(encoding="utf-8-sig")
    lines = old.splitlines()
    sep = doctor.shard_separator(lines)
    row = ("\t" if sep == "\t" else " | ").join(row_fields)
    if replace_file:
        hits = [i for i, ln in enumerate(lines)
                if ln.strip() and not ln.startswith("#") and len(f := doctor.split_row(ln, sep)) >= 4
                and f[3] == replace_file]
        if hits:
            lines[hits[0]] = row
            for i in reversed(hits[1:]):          # an earlier duplicate is folded into one row
                del lines[i]
            return "\n".join(lines) + "\n", row, "replaced"
    return (old if old.endswith("\n") or not old else old + "\n") + row + "\n", row, "appended"


def report_lint(results) -> tuple[int, int]:
    for check, status, detail in results:
        say(f"{status}  {check:20} {detail}")
    return (sum(1 for _c, s, _d in results if s == doctor.FAIL),
            sum(1 for _c, s, _d in results if s == doctor.WARN))


def main(argv: list[str]) -> int:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")
    if "--where" in argv:
        if argv != ["--where"]:
            say(USAGE)
            return EXIT_INPUT
        home = doctor.genprompt_home()
        rules = home / "local-rules.md"
        say(f"home {home.as_posix()}")
        say(f"local-rules {rules.as_posix()} ({'present' if rules.is_file() else 'absent'})")
        return EXIT_OK
    dry, replace = "--dry-run" in argv, "--replace" in argv
    rest = [a for a in argv if a not in ("--dry-run", "--replace")]
    if len(rest) > 1 or any(a.startswith("--") for a in rest) or (dry and replace):
        say(USAGE)
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
    problems = structural_problems(p, cmd_by_letter)
    for msg in problems:
        say(f"FAIL  fields  {msg}")
    if problems:
        say("NOT ARCHIVED: these fields name the record, so nothing could be written. Fix them and re-run.")
        return EXIT_INPUT
    p["task"], notes = normalise_task(p["task"])
    for note in notes:
        say(f"WARN  task  {note}")

    archive = doctor.genprompt_home() / "generated-prompts"      # resolved per run (E-21)
    shard = archive / "by-repo" / f"{p['key']}.tsv"
    target = None if p["archetype"] == "none" else archive / p["key"] / file_name(p, cmd_by_letter)
    row_fields = [p["date"], p["archetype"], p["slug"], target.name if target else "-", p["task"]]
    if target is not None and target.exists() and not replace and not dry:
        say(f"REFUSED  {target} already exists; an archive file is a record. Use --replace to fix "
            f"and re-archive it under the same name.")
        return EXIT_EXISTS
    shard_new, row, how = new_shard_text(shard, p, row_fields,
                                         target.name if (replace and target is not None) else None)
    text = compose(p) if target is not None else ""

    if dry:
        say("DRY RUN: nothing written.")
        fails = 0
        if target is not None:
            exists = " (exists: needs --replace)" if target.exists() else ""
            say(f"would write  {target}  ({len(text.splitlines())} lines){exists}")
            say(f"line 1       {text.splitlines()[0]}")
            fails, _warns = report_lint(doctor.lint_prompt(text, target.name, cmd_by_letter))
        say(f"would update {shard} ({how})")
        say(f"row          {row}")
        return EXIT_ERRORS if fails else EXIT_OK

    # 1. write the record
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    shard.parent.mkdir(parents=True, exist_ok=True)
    shard.write_text(shard_new, encoding="utf-8", newline="\n")

    # 2. validate what is on disk: the file, and that the row parses back into the same 5 fields
    fails = warns = 0
    if target is not None:
        fails, warns = report_lint(doctor.lint_prompt(target.read_text(encoding="utf-8"), target.name, cmd_by_letter))
    shard_lines = shard.read_text(encoding="utf-8").splitlines()
    sep = doctor.shard_separator(shard_lines)
    rows = [doctor.split_row(ln, sep) for ln in shard_lines if ln.strip() and not ln.startswith("#")]
    if row_fields not in rows:
        say(f"FAIL  shard-row            the row does not parse back as {row_fields!r}")
        fails += 1
    elif target is not None and sum(1 for r in rows if len(r) >= 4 and r[3] == target.name) != 1:
        say(f"FAIL  shard-row            {target.name} has more than one row in {shard.name}")
        fails += 1

    where = f"{target}" if target is not None else f"status row in {shard.name}"
    if fails:
        say(f"ARCHIVED WITH ERRORS: {where} was written, but {fails} check(s) FAILED (listed above). "
            f"Report the archive row as FAIL; fix the prompt and re-run with --replace.")
        return EXIT_ERRORS
    say(f"ARCHIVED  {where}" + (f"  ({warns} warning(s))" if warns else ""))
    say(f"ROW       {shard.name} ({how}): {row}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
