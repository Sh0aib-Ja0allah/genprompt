"""genprompt doctor: integrity check for the rules suite and the prompt archive.

Usage:  python3 tools/doctor.py [--suite] [--archive] [--verbose]
        (no scope flag = both; on Windows the interpreter is usually `python`)

The suite is this plugin folder (the rules + commands/). The archive is ~/.genprompt/generated-prompts,
which lives outside the plugin, so plugin updates never touch it.

Severity:
  ERROR  a v3 rule is broken, or something is dangling or unreadable. Exit code 1.
  WARN   worth fixing soon (a stale profile, an unresolved follows link).
  INFO   legacy (pre-v3) drift, counted rather than listed unless --verbose.

A row or prompt file is held to v3 rules when ANY of these is true: it sits below a shard's
'# --- v3 ---' marker, its shard is a pure v3 shard, its date is on or after V3_START, or the file
carries the v3 line-1 header. Standard library only; it never writes anything.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True

HOME = Path(__file__).resolve().parent.parent       # the plugin root (the rules suite)
ARCHIVE = Path.home() / ".genprompt" / "generated-prompts"
SHARDS = ARCHIVE / "by-repo"
COMMANDS = HOME / "commands"
V3_START = "2026-09-24"
PROFILE_MAX_AGE_DAYS = 14
TASK_CAP = 200
MIN_PROMPT_LINES = 15
V3_MARKER = "# --- v3 ---"
V3_HEADER_RE = re.compile(r"^<!-- genprompt v3: (.+) -->\s*$")
LABEL_RE = re.compile(r"^(none|[A-Z](\+[A-Z])*)$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FILE_RE = re.compile(r"^(?:[a-z0-9-]+/)?\d{4}-\d{2}-\d{2}-[a-z]+(?:\+[a-z]+)*-[a-z0-9-]+\.md$")
SELF_CHECK_RE = re.compile(r"^\|\s*#\s*\|\s*Item\s*\|\s*Verdict\s*\|\s*Reason\s*\|", re.M)
RUNTIME_EXCLUDE = {"history", "examples", "commands", ".git", ".claude-plugin", ".github",
                   "generated-prompts", ".ruff_cache", "__pycache__"}
PROFILE_KEYS = ("repo", "path", "key", "derived", "stamp")
BANNED = [
    (re.compile(r"\{\{[A-Z_]+\}\}"), "retired {{PLACEHOLDER}} syntax"),
]
# The suite ships to other machines, so a runtime file must never name one user's home directory.
PERSONAL_PATH = (re.compile(r"\b[A-Za-z]:[\\/]+Users[\\/]+(?!<)[\w.-]+|/(?:Users|home)/(?!<)[\w.-]+/"),
                 "a user-specific absolute path (use ~/ or a <placeholder>)")

findings: list[tuple[str, str, str]] = []
info_counts: Counter[str] = Counter()
VERBOSE = False


def say(msg: str = "") -> None:
    sys.stdout.write(f"{msg}\n")


def add(sev: str, area: str, msg: str) -> None:
    if sev == "INFO":
        info_counts[msg.split(":")[0]] += 1
        if not VERBOSE:
            return
    findings.append((sev, area, msg))


def read(path: Path, area: str) -> str | None:
    """Read UTF-8 (a BOM is tolerated). Missing or undecodable files become ERRORs, not crashes."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        add("ERROR", area, f"missing file: {path}")
    except UnicodeDecodeError as exc:
        add("ERROR", area, f"not valid UTF-8 ({exc.reason} at byte {exc.start}): {path}")
    except OSError as exc:
        add("ERROR", area, f"unreadable ({exc.strerror}): {path}")
    return None


def load_build_shims():
    spec = importlib.util.spec_from_file_location("build_shims", HOME / "tools" / "build_shims.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load tools/build_shims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def runtime_md() -> list[Path]:
    out = []
    for p in HOME.rglob("*.md"):
        rel = p.relative_to(HOME)
        if rel.parts[0] in RUNTIME_EXCLUDE or rel.name == "CHANGELOG.md":
            continue
        out.append(p)
    return out


def section_ids() -> set[str]:
    ids: set[str] = {"9"}  # §9 is PROTOCOL.md itself
    head = re.compile(r"^#{1,4} (\d+(?:\.\d+)?)(?:[–-](\d+(?:\.\d+)?))?[.:\s]")
    arch = re.compile(r"^# 5\.([A-Z]):")
    for p in list((HOME / "guide").glob("*.md")) + list((HOME / "archetypes").glob("*.md")):
        text = read(p, "suite") or ""
        for line in text.splitlines():
            m = head.match(line)
            if m:
                ids.add(m.group(1))
                lo, hi = m.group(1), m.group(2)
                if hi:
                    ids.add(hi)
                    if "." in lo and "." in hi and lo.split(".")[0] == hi.split(".")[0]:
                        for n in range(int(lo.split(".")[1]), int(hi.split(".")[1]) + 1):
                            ids.add(f"{lo.split('.')[0]}.{n}")
            m = arch.match(line)
            if m:
                ids.add(f"5.{m.group(1)}")
    return ids


def scan_banned(text: str, where: str, area: str, extra: tuple = ()) -> None:
    for rx, why in [*BANNED, *extra]:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            add("ERROR", area, f"{where}:{line}: banned string ({why}): {m.group(0)!r}")


def check_suite() -> None:
    try:
        bs = load_build_shims()
    except Exception as exc:  # noqa: BLE001 - report any import failure as a finding
        add("ERROR", "suite", f"tools/build_shims.py failed to load: {exc}")
        return
    for err in bs.table_errors():
        add("ERROR", "suite", f"build_shims: {err}")
    for letter, cmd, stem, *_ in bs.ARCHETYPES:
        text = read(HOME / "archetypes" / f"{stem}.md", "suite")
        if text is not None and not text.startswith(f"# 5.{letter}:"):
            add("ERROR", "suite", f"archetypes/{stem}.md does not start with '# 5.{letter}:' ({cmd})")
    known = {f"{r[2]}.md" for r in bs.ARCHETYPES} | {"README.md"}
    for f in (HOME / "archetypes").glob("*.md"):
        if f.name not in known:
            add("ERROR", "suite", f"archetype file with no command in build_shims: archetypes/{f.name}")
    for cmd, *_ in bs.UTILITIES:
        if not (HOME / "utilities" / f"{cmd}.md").exists():
            add("ERROR", "suite", f"utility spec missing: utilities/{cmd}.md")

    exp = bs.expected()
    for path, text in exp.items():
        cur = read(path, "suite") if path.exists() else None
        if cur is None:
            add("ERROR", "suite", f"shim missing: {path} (run tools/build_shims.py)")
            continue
        if cur != text:
            add("ERROR", "suite", f"shim differs from generator: {path} (run tools/build_shims.py)")
        for inc in re.findall(r"^@(.+)$", cur, re.M):
            if not Path(inc.strip().replace("${CLAUDE_PLUGIN_ROOT}", str(HOME))).is_file():
                add("ERROR", "suite", f"{path.name}: @-include target does not exist: {inc.strip()}")
    for p in sorted(set(COMMANDS.glob("*.md")) - set(exp)):
        add("ERROR", "suite", f"unmanaged command file: {p.relative_to(HOME).as_posix()}")
    protocol = read(HOME / "PROTOCOL.md", "suite")
    if protocol is not None and "GENPROMPT-PROTOCOL v3 LOADED" not in protocol:
        add("ERROR", "suite", "PROTOCOL.md lost its load marker line")

    picker = read(HOME / "archetypes" / "README.md", "suite") or ""
    grammar = read(HOME / "guide" / "08-grammar.md", "suite") or ""
    for _letter, cmd, *_ in bs.ARCHETYPES:
        if f"`:{cmd}`" not in picker:
            add("ERROR", "suite", f"picker (archetypes/README.md) does not list :{cmd}")
        if f"/genprompt:{cmd}" not in grammar:
            add("ERROR", "suite", f"grammar (guide/08-grammar.md) does not list /genprompt:{cmd}")
    for cmd, *_ in bs.UTILITIES:
        if f"/genprompt:{cmd}" not in grammar:
            add("ERROR", "suite", f"grammar does not list utility /genprompt:{cmd}")
    for flag in re.findall(r"--[a-z-]+", bs.FLAGS):
        if flag not in grammar:
            add("ERROR", "suite", f"flag {flag} is in the shims but not in guide/08-grammar.md")

    ids = section_ids()
    sec_ref = re.compile(r"§(5\.[A-Z]|\d+(?:\.\d+)?)")
    file_ref = re.compile(r"\b((?:guide|archetypes|stacks|utilities|tools|examples)[\\/][\w.\-]+\.(?:md|py))")
    for p in runtime_md() + [p for p in exp if p.exists()]:
        text = read(p, "suite")
        if text is None:
            continue
        where = p.relative_to(HOME).as_posix()
        for m in sec_ref.finditer(text):
            ref = m.group(1)
            if ref in ids:
                continue
            if ref.startswith("5.") and ref[2:].isalpha():
                add("ERROR", "suite", f"{where}: §{ref} is not an archetype")
            elif ref.split(".")[0] not in ids:
                add("ERROR", "suite", f"{where}: §{ref} does not resolve to a section")
            else:
                add("WARN", "suite", f"{where}: §{ref} only resolves to its parent section")
        for m in file_ref.finditer(text):
            rel = m.group(1).replace("\\", "/")
            if not (HOME / rel).exists():
                add("ERROR", "suite", f"{where}: file reference {rel} does not exist")
        scan_banned(text, where, "suite", (PERSONAL_PATH,))


def split_row(raw: str) -> list[str]:
    s = raw.strip()
    if "|" in s:
        return [f.strip() for f in re.split(r"\s*\|\s*", s, maxsplit=4)]
    return [f.strip() for f in s.split("\t")]


def shard_rows(path: Path):
    """Yield (lineno, fields, is_v3, raw). Records shard-structure problems as findings."""
    text = read(path, "archive")
    if text is None:
        return
    lines = text.splitlines()
    schema = next((ln.strip() for ln in lines[:6] if ln.startswith("# schema:")), "")
    pure_v3 = schema == "# schema: v3"
    markers = [i for i, ln in enumerate(lines) if ln.strip() == V3_MARKER]
    if not schema:
        add("ERROR", "archive", f"{path.name}: no '# schema:' header line")
    elif not pure_v3 and len(markers) != 1:
        add("ERROR", "archive", f"{path.name}: legacy shard must contain exactly one '{V3_MARKER}' line "
                                f"(found {len(markers)})")
    marker_at = markers[0] if markers else len(lines)
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        fields = split_row(raw)
        is_v3 = pure_v3 or i > marker_at or (bool(fields) and fields[0] >= V3_START
                                             and bool(DATE_RE.match(fields[0])))
        yield i + 1, fields, is_v3, raw


def resolve_row_file(key: str, ref: str, is_v3: bool) -> Path | None:
    if ref in {"-", "(none)", ""}:
        return None
    ref = ref.replace("\\", "/")
    if "/" in ref:
        cands = [ARCHIVE / ref]
    elif is_v3:
        cands = [ARCHIVE / key / ref]
    else:
        cands = [ARCHIVE / key / ref, ARCHIVE / ref]
    for c in cands:
        if c.is_file():
            return c
    return cands[0]


def fences(text: str) -> list[tuple[int, int, int, list[str]]]:
    """(ticks, open_line, close_line, body) for each backtick fence, CommonMark-style."""
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(`{3,})([^`]*)$", lines[i].rstrip())
        if not m:
            i += 1
            continue
        ticks = len(m.group(1))
        j = i + 1
        while j < len(lines):
            c = re.match(r"^(`{3,})\s*$", lines[j].rstrip())
            if c and len(c.group(1)) >= ticks:
                break
            j += 1
        out.append((ticks, i, j, lines[i + 1:j]))
        i = j + 1
    return out


def check_prompt_file(p: Path, rel: str, header: re.Match[str] | None, row_label: str | None,
                      all_names: set[str]) -> None:
    text = read(p, "archive")
    if text is None:
        return
    if header is None:
        add("ERROR", "archive", f"{rel}: v3 file without the line-1 header")
    blocks = fences(text)
    if not blocks:
        add("ERROR", "archive", f"{rel}: no fenced prompt (a stub breaks the chain)")
        return
    ticks, _start, end, body = max(blocks, key=lambda b: len(b[3]))
    if len(body) < MIN_PROMPT_LINES:
        add("ERROR", "archive", f"{rel}: longest fenced block has {len(body)} lines; the full prompt is missing")
    if ticks == 3 and any(re.match(r"^`{3}", ln) for ln in body):
        add("ERROR", "archive", f"{rel}: 3-backtick outer fence contains a nested fence; the pasted "
                                f"prompt is truncated (use a 4-backtick outer fence)")
    tail = "\n".join(text.splitlines()[end + 1:])
    if not SELF_CHECK_RE.search(tail):
        add("ERROR", "archive", f"{rel}: no self-check table (| # | Item | Verdict | Reason |) after the prompt")
    if header is None:
        return
    meta = dict(kv.split("=", 1) for kv in header.group(1).split(" | ") if "=" in kv)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    folder = rel.split("/")[0] if "/" in rel else ""
    if meta.get("key") and folder and meta["key"] != folder:
        add("ERROR", "archive", f"{rel}: header key={meta['key']} but the file is in folder {folder}/")
    if meta.get("date") and not p.name.startswith(meta["date"]):
        add("ERROR", "archive", f"{rel}: header date={meta['date']} does not match the filename date")
    if row_label and meta.get("archetype") and meta["archetype"] != row_label:
        add("ERROR", "archive", f"{rel}: header archetype={meta['archetype']} but the shard row says {row_label}")
    fol = meta.get("follows", "-")
    if fol not in {"-", "", "none"} and fol.split("/")[-1] not in all_names:
        add("WARN", "archive", f"{rel}: follows={fol} not found in the archive")


def check_profiles(today: dt.date) -> None:
    for prof in sorted(SHARDS.glob("*.profile.md")):
        text = read(prof, "archive")
        if text is None:
            continue
        scan_banned(text, f"by-repo/{prof.name}", "archive")
        front = dict(re.findall(r"^(\w+):\s*(.*)$", text.split("---")[1] if text.startswith("---") else "",
                                re.M))
        missing = [k for k in PROFILE_KEYS if not front.get(k)]
        if missing:
            add("ERROR", "archive", f"profile {prof.name}: missing field(s) {', '.join(missing)}")
        key = prof.name[: -len(".profile.md")]
        if front.get("key") and front["key"] != key:
            add("ERROR", "archive", f"profile {prof.name}: key={front['key']} does not match the filename")
        if not (SHARDS / f"{key}.tsv").exists():
            add("WARN", "archive", f"profile {prof.name}: no shard {key}.tsv")
        try:
            age = (today - dt.date.fromisoformat(front.get("derived", ""))).days
            if age > PROFILE_MAX_AGE_DAYS:
                add("WARN", "archive", f"profile {prof.name} is {age} days old (max {PROFILE_MAX_AGE_DAYS})")
        except ValueError:
            add("WARN", "archive", f"profile {prof.name}: derived date missing or invalid")
        if not re.search(r"\S+@[0-9a-f]{6,}", front.get("stamp", "")):
            add("WARN", "archive", f"profile {prof.name}: stamp is not <file>@<sha> (cannot be checked)")


def check_archive(letters_by_word: dict[str, str]) -> dict:
    stats: dict = {"rows": Counter(), "arche": Counter(), "latest": {}, "files": 0}
    if not SHARDS.is_dir():
        stats["empty"] = True       # a fresh install: nothing archived yet is not an error
        return stats
    referenced: dict[Path, str | None] = {}
    v3_files: set[Path] = set()
    for shard in sorted(SHARDS.glob("*.tsv")):
        key = shard.stem
        if key != key.lower():
            add("ERROR", "archive", f"shard key not lowercase: {shard.name}")
        for ln, fields, is_v3, raw in shard_rows(shard):
            where = f"{shard.name}:{ln}"
            stats["rows"][key] += 1
            date = fields[0] if fields else ""
            if DATE_RE.match(date):
                stats["latest"][key] = max(stats["latest"].get(key, ""), date)
            if len(fields) >= 2:
                for tok in re.findall(r"[A-Za-z]+", fields[1]):
                    letter = tok if tok in letters_by_word.values() else letters_by_word.get(tok.lower())
                    stats["arche"][letter or ("none" if tok == "none" else "other")] += 1
            file_field = fields[3] if len(fields) >= 4 else ""
            if not is_v3:
                file_field = next((f for f in fields if f.endswith(".md")), file_field)
            target = resolve_row_file(key, file_field, is_v3)
            if target is not None:
                if target.is_file():
                    rp = target.resolve()
                    referenced.setdefault(rp, fields[1] if is_v3 and len(fields) > 1 else None)
                    if is_v3:
                        v3_files.add(rp)
                else:
                    add("ERROR", "archive", f"{where}: row points to a missing file: {file_field}")
            sev = "ERROR" if is_v3 else "INFO"
            if len(fields) != 5:
                add(sev, "archive", f"shard fields != 5: {where} ({len(fields)} fields)")
                continue
            task = fields[4]
            if len(task) > TASK_CAP:
                add(sev, "archive", f"task over {TASK_CAP} chars: {where} ({len(task)})")
            if "—" in raw or "·" in raw:
                add(sev, "archive", f"em-dash or middle dot in row: {where}")
            if not is_v3:
                continue
            label, slug, fref = fields[1], fields[2], fields[3]
            if not DATE_RE.match(date):
                add("ERROR", "archive", f"{where}: date {date!r} is not YYYY-MM-DD")
            if not LABEL_RE.match(label):
                add("ERROR", "archive", f"{where}: archetype label {label!r} is not letters joined by + (or 'none')")
            if not SLUG_RE.match(slug):
                add("ERROR", "archive", f"{where}: slug {slug!r} is not lowercase kebab-case (max 60)")
            if label == "none" and fref != "-":
                add("ERROR", "archive", f"{where}: a status row must have file '-'")
            if label != "none" and not FILE_RE.match(fref):
                add("ERROR", "archive", f"{where}: file {fref!r} is not <date>-<cmd>[+<cmd>]-<slug>.md")
            if not task:
                add("ERROR", "archive", f"{where}: empty task")
            if "|" in task:
                add("ERROR", "archive", f"{where}: '|' inside the task text")

    for folder in sorted(p for p in ARCHIVE.iterdir() if p.is_dir() and p.name != "by-repo"):
        if folder.name.startswith("."):
            continue
        if folder.name != folder.name.lower():
            add("ERROR", "archive", f"folder key not lowercase: {folder.name}")
        if not (SHARDS / f"{folder.name}.tsv").exists():
            add("ERROR", "archive", f"folder with no shard: {folder.name}")
    prompt_files = [p for p in ARCHIVE.rglob("*.md")
                    if p.name not in {"README.md", "INDEX.md"} and "by-repo" not in p.parts
                    and not any(part.startswith(".") for part in p.relative_to(ARCHIVE).parts)]
    stats["files"] = len(prompt_files)
    all_names = {p.name for p in prompt_files}
    for p in prompt_files:
        rp = p.resolve()
        rel = p.relative_to(ARCHIVE).as_posix()
        text = read(p, "archive")
        if text is None:
            continue
        first = text.splitlines()[:1]
        header = V3_HEADER_RE.match(first[0]) if first else None
        in_folder = "/" in rel
        dated_v3 = in_folder and p.name[:10] >= V3_START and bool(DATE_RE.match(p.name[:10]))
        is_v3 = header is not None or rp in v3_files or dated_v3
        if rp not in referenced:
            add("ERROR" if is_v3 else "INFO", "archive", f"file with no shard row: {rel}")
        if is_v3:
            check_prompt_file(p, rel, header, referenced.get(rp), all_names)
        elif not first or not first[0].startswith("<!-- genprompt"):
            add("INFO", "archive", f"legacy file without line-1 header: {rel}")
    check_profiles(dt.date.today())
    return stats


def main(argv: list[str]) -> int:
    global VERBOSE
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")
    allowed = {"--suite", "--archive", "--verbose"}
    unknown = [a for a in argv if a not in allowed]
    if unknown:
        say(f"unknown argument(s): {' '.join(unknown)}   usage: doctor.py [--suite] [--archive] [--verbose]")
        return 2
    VERBOSE = "--verbose" in argv
    scoped = {"--suite", "--archive"} & set(argv)
    run_suite = not scoped or "--suite" in scoped
    run_archive = not scoped or "--archive" in scoped
    stats = None
    letters_by_word: dict[str, str] = {}
    if run_suite:
        check_suite()
    if run_archive:
        try:
            bs = load_build_shims()
            letters_by_word = {cmd: letter for letter, cmd, *_ in bs.ARCHETYPES}
        except Exception:  # noqa: BLE001 - stats degrade gracefully; the suite check reports it
            letters_by_word = {}
        stats = check_archive(letters_by_word)
    for sev in ("ERROR", "WARN", "INFO"):
        for s, area, msg in findings:
            if s == sev:
                say(f"{sev:5}  [{area}] {msg}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    say()
    say(f"Summary: {errors} ERROR, {warns} WARN, {sum(info_counts.values())} INFO (legacy)")
    for kind, n in info_counts.most_common():
        say(f"  INFO x{n:<4} {kind}")
    if stats and stats.get("empty"):
        say()
        say(f"Library: no archive yet at {ARCHIVE} (the first archived prompt creates it)")
    elif stats:
        say()
        say(f"Library: {stats['files']} prompt files,{sum(stats['rows'].values())} shard rows, "
            f"{len(stats['rows'])} shards")
        for key, n in stats["rows"].most_common():
            say(f"  {key:22} {n:4} rows   latest {stats['latest'].get(key, '?')}")
        top = ", ".join(f"{k}:{v}" for k, v in stats["arche"].most_common(16))
        say(f"  archetypes (legacy words mapped to letters): {top}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
