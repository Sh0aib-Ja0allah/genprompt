"""genprompt doctor: integrity check for the rules suite and the prompt archive.

Usage:  python3 tools/doctor.py [--suite] [--archive] [--verbose]
        (no scope flag = both; on Windows the interpreter is usually `python`)
        python3 tools/doctor.py --prompt <archive file>   (per-file lint: PASS/FAIL per check)
        GENPROMPT_HOME=<dir> overrides the genprompt home (default ~/.genprompt); tests use it.

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
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True

HOME = Path(__file__).resolve().parent.parent       # the plugin root (the rules suite)


def genprompt_home(env: dict | None = None) -> Path:
    """The genprompt home: GENPROMPT_HOME when set and non-blank, else ~/.genprompt. Always absolute
    (`~` expanded, a relative value resolved against the cwd), because every tool and the generator
    need absolute paths. The ONE place a tool resolves the home (E-21): archive.py calls it too.
    Tests and probes set GENPROMPT_HOME to a sandbox; normal runs leave it unset."""
    raw = (os.environ if env is None else env).get("GENPROMPT_HOME", "").strip()
    home = Path(raw).expanduser() if raw else Path.home() / ".genprompt"
    return home if home.is_absolute() else home.resolve()


GENPROMPT_HOME = genprompt_home()
ARCHIVE = GENPROMPT_HOME / "generated-prompts"
SHARDS = ARCHIVE / "by-repo"
COMMANDS = HOME / "commands"
V3_START = "2026-09-24"
PROFILE_MAX_AGE_DAYS = 90   # §2.9 hard ceiling; freshness itself is the file@sha stamps (doctor cannot run git in a repo)
TASK_CAP = 200
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
        if rel.parts[0] in RUNTIME_EXCLUDE or rel.name == "CHANGELOG.md" or "fixtures" in rel.parts:
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
    check_protocol_size()
    check_write_grants([cmd for _l, cmd, *_ in bs.ARCHETYPES] + [bs.ENTRY])

    picker =read(HOME / "archetypes" / "README.md", "suite") or ""
    grammar = read(HOME / "guide" / "08-grammar.md", "suite") or ""
    for _letter, cmd, *_ in bs.ARCHETYPES:
        if f"`:{cmd}`" not in picker:
            add("ERROR", "suite", f"picker (archetypes/README.md) does not list :{cmd}")
        if f"/genprompt:{cmd}" not in grammar:
            add("ERROR", "suite", f"grammar (guide/08-grammar.md) does not list /genprompt:{cmd}")
    for cmd, *_ in bs.UTILITIES:
        if f"/genprompt:{cmd}" not in grammar:
            add("ERROR", "suite", f"grammar does not list utility /genprompt:{cmd}")
    for flag in re.findall(r"--[a-z-]+", bs.FLAGS + " " + getattr(bs, "SPLIT_FLAG", "")):
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


# E-22: PROTOCOL's write boundary, kept here independently of tools/build_shims.py so that widening
# a shim's Write/Edit scope in the generator alone fails the suite. Paths are under ~/.genprompt/.
# Prompt-emitting commands (every archetype and :auto) write the archive and the archive.py parts
# file; :learn only its personal rules; :profile only the card; every other command writes nothing.
WRITE_BOUNDARY_EMIT = ("generated-prompts/**", "tmp/**")
WRITE_BOUNDARY = {"learn": ("local-rules.md",), "profile": ("generated-prompts/by-repo/**",)}
WRITE_TOOL_RE = re.compile(r"\b(Write|Edit|MultiEdit|NotebookEdit)\b(?:\(([^)]*)\))?")


def write_grants_of(text: str) -> set[str]:
    """The write-capable grants in a command file's allowed-tools line, e.g. 'Write(~/x/**)'."""
    m = re.search(r"^allowed-tools:(.*)$", text, re.M)
    if not m:
        return set()
    return {f"{tool}({path})" if path else tool for tool, path in WRITE_TOOL_RE.findall(m.group(1))}


def expected_write_grants(cmd: str, emitters: list[str]) -> set[str]:
    scopes = WRITE_BOUNDARY_EMIT if cmd in emitters else WRITE_BOUNDARY.get(cmd, ())
    return {f"{tool}(~/.genprompt/{s})" for s in scopes for tool in ("Write", "Edit")}


def check_write_grants(emitters: list[str], commands: Path = COMMANDS) -> None:
    for p in sorted(commands.glob("*.md")):
        text = read(p, "suite")
        if text is None:
            continue
        got, want = write_grants_of(text), expected_write_grants(p.stem, emitters)
        for g in sorted(got - want):
            add("ERROR", "suite", f"commands/{p.name}: write grant {g} is outside PROTOCOL's write "
                                  f"boundary for :{p.stem} (allowed: {', '.join(sorted(want)) or 'none'})")
        for g in sorted(want - got):
            add("ERROR", "suite", f"commands/{p.name}: write grant {g} is missing for :{p.stem}")


# E-09c: every archetype command @-includes PROTOCOL.md, so its size is paid on every emission.
# Budget: 1.2.0 (E-11b) was 16,800; E-09f cut PROTOCOL to 14,010 bytes, so 14,600 keeps the same
# ~600 B headroom. Raise it only with a reason.
PROTOCOL_MAX_BYTES = 14_600


def check_protocol_size(path: Path = HOME / "PROTOCOL.md", limit: int = PROTOCOL_MAX_BYTES) -> None:
    """WARN when PROTOCOL.md grows past the core budget; move read-on-demand detail to its section."""
    if not path.is_file():
        return
    size = path.stat().st_size
    if size > limit:
        add("WARN", "suite", f"PROTOCOL.md is {size} bytes, over the {limit}-byte core budget: move "
                             f"read-on-demand detail to its owning section with a 'Read only when' pointer")


# E-18b: the Agensi bundle that tools/build_skill_bundle.py WOULD build must match the repo. No zip is
# built (dist/ is not committed and CI should stay fast): SKILL.md text and the file list are
# derived in memory, and the file list comes from a tree walk, so doctor still runs no subprocess.
BUNDLE_REQUIRED = ("PROTOCOL.md", "LICENSE", "README.md", "CHANGELOG.md", ".claude-plugin/plugin.json",
                   ".claude-plugin/marketplace.json", "archetypes/README.md", "guide/00-index.md",
                   "stacks/stack-matrix.md", "stacks/workspaces.md", "tools/doctor.py", "tools/build_shims.py", "tools/archive.py")
BUNDLE_BANNED = (".github/", "evals/", "tools/tests/", "assets/", "dist/", ".git/")


def check_bundle(root: Path = HOME, skill: str | None = None, names: list[str] | None = None) -> None:
    """The bundle's SKILL.md version and counts equal plugin.json and the build_shims tables, and its
    file set is the intended one: every runtime file (commands, archetypes, guide incl. blocks,
    utilities, stacks, the three tools) is in, nothing from CI, evals, tests, assets or dist."""
    try:
        spec = importlib.util.spec_from_file_location("bundle_for_doctor", root / "tools" / "build_skill_bundle.py")
        bundle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bundle)
        bs = load_build_shims()
        meta = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - a broken bundle tool is itself the finding
        add("ERROR", "suite", f"bundle: cannot load tools/build_skill_bundle.py or plugin.json ({exc})")
        return
    if skill is None:
        skill = bundle.skill_md(meta, bs)
    if names is None:
        names = bundle.bundle_files(root, use_git=False)
    m = re.search(r"^version: (\S+)$", skill, re.M)
    if not m or m.group(1) != meta.get("version"):
        add("ERROR", "suite", f"bundle: SKILL.md version {m.group(1) if m else '(none)'} != plugin.json "
                              f"{meta.get('version')}")
    for label, n in (("archetypes", len(bs.ARCHETYPES)), ("utilities", len(bs.UTILITIES))):
        if f"## The {n} {label}" not in skill:
            add("ERROR", "suite", f"bundle: SKILL.md does not say '## The {n} {label}' (build_shims has {n})")
    listed = re.findall(r"^\| [A-Z] \| `/genprompt:([a-z]+)` \|", skill, re.M)
    if listed != [a.cmd for a in bs.ARCHETYPES]:
        add("ERROR", "suite", "bundle: SKILL.md's archetype table differs from build_shims ARCHETYPES")
    have = set(names)
    for rel in BUNDLE_REQUIRED:
        if rel not in have:
            add("ERROR", "suite", f"bundle: {rel} would be missing from the bundle")
    # every ladder file the stack matrix routes to must exist and ship (stacks/ladders/<stack>.md)
    matrix = root / "stacks" / "stack-matrix.md"
    named = set(re.findall(r"`(stacks/ladders/[\w.-]+\.md)`", matrix.read_text(encoding="utf-8"))) \
        if matrix.is_file() else set()
    if not named:
        add("ERROR", "suite", "bundle: stacks/stack-matrix.md names no stacks/ladders/<stack>.md file")
    for rel in sorted(named):
        if not (root / rel).is_file():
            add("ERROR", "suite", f"bundle: stacks/stack-matrix.md routes to {rel}, which does not exist")
        elif rel not in have:
            add("ERROR", "suite", f"bundle: ladder {rel} would be missing from the bundle")
    for p in sorted((root / "stacks" / "ladders").glob("*.md")):
        if p.relative_to(root).as_posix() not in named:
            add("ERROR", "suite", f"bundle: {p.relative_to(root).as_posix()} is not routed from stacks/stack-matrix.md")
    for sub in ("commands", "archetypes", "guide", "utilities", "stacks"):
        for p in sorted((root / sub).rglob("*.md")):
            rel = p.relative_to(root).as_posix()
            if rel not in have:
                add("ERROR", "suite", f"bundle: runtime file {rel} would be missing from the bundle")
    for rel in sorted(have):
        if rel.startswith(BUNDLE_BANNED) or "__pycache__" in rel or rel.endswith(".pyc"):
            add("ERROR", "suite", f"bundle: {rel} would be shipped but is not part of the skill")


def check_release(root: Path = HOME, archetype_count: int | None = None) -> None:
    """Version sync: plugin.json, both marketplace.json versions and the top released CHANGELOG
    heading must agree ("## Unreleased" is skipped), and any "<N> archetypes" claim in the manifest
    descriptions must match the build_shims table."""
    if archetype_count is None:
        try:
            archetype_count = len(load_build_shims().ARCHETYPES)
        except Exception:  # noqa: BLE001 - check_suite already reports a broken build_shims
            archetype_count = None
    places: list[tuple[str, str]] = []           # (where, version)
    descs: list[tuple[str, str]] = []            # (where, description)
    for name in ("plugin.json", "marketplace.json"):
        rel = f".claude-plugin/{name}"
        text = read(root / ".claude-plugin" / name, "suite")
        if text is None:
            continue
        try:
            data = json.loads(text)
        except ValueError as exc:
            add("ERROR", "suite", f"{rel} is not valid JSON: {exc}")
            continue
        if name == "plugin.json":
            places.append((f"{rel} version", str(data.get("version", ""))))
            descs.append((f"{rel} description", str(data.get("description", ""))))
            continue
        places.append((f"{rel} metadata.version", str(data.get("metadata", {}).get("version", ""))))
        for i, plug in enumerate(data.get("plugins", [])):
            places.append((f"{rel} plugins[{i}].version", str(plug.get("version", ""))))
            descs.append((f"{rel} plugins[{i}].description", str(plug.get("description", ""))))
    changelog = read(root / "CHANGELOG.md", "suite")
    if changelog is not None:
        m = re.search(r"^## (\d+\.\d+\.\d+)\b", changelog, re.M)
        places.append(("CHANGELOG.md top released heading", m.group(1) if m else ""))
    if places:
        ref_where, ref_ver = places[0]
        for where, ver in places:
            if not ver:
                add("ERROR", "suite", f"no version found in {where}")
            elif ver != ref_ver and ref_ver:
                add("ERROR", "suite", f"version mismatch: {ref_where} is {ref_ver} but {where} is {ver}")
    if archetype_count is not None:
        for where, desc in descs:
            for m in re.finditer(r"\b(\d+) archetypes\b", desc):
                if int(m.group(1)) != archetype_count:
                    add("ERROR", "suite", f"{where} says {m.group(1)} archetypes but "
                                          f"tools/build_shims.py ARCHETYPES has {archetype_count}")


def shard_separator(lines: list[str]) -> str:
    """Pick one separator for a whole shard: tab when most data rows have 4+ tabs, else '|'.

    Deciding per shard (not per row) keeps a stray '|' in a tab shard's task text from shifting
    that row's fields; it then fails the specific "'|' inside the task text" check instead.
    """
    data = [ln for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    tabbed = sum(1 for ln in data if ln.count("\t") >= 4)
    return "\t" if data and tabbed * 2 > len(data) else "|"


def split_row(raw: str, sep: str = "|") -> list[str]:
    s = raw.strip()
    if sep == "\t":
        return [f.strip() for f in s.split("\t")]
    return [f.strip() for f in re.split(r"\s*\|\s*", s, maxsplit=4)]


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
    sep = shard_separator(lines)
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        fields = split_row(raw, sep)
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


# ---------------------------------------------------------------------------------------------
# Per-file lint (doctor --prompt, and tools/archive.py after it writes). The mechanical rows of
# the self-check (§6 rows 8, 15, 16, 21, 22) are checked here so the generator does not grade
# itself. --archive does not run these: most of the existing archive predates them.
#
# Severity, calibrated on the real v3 archive (2026-10-05 onward):
#   FAIL  the record is broken: invalid line-1 header, no/unclosed/split fence or a stub block,
#         no self-check table (§10.2, §4.21 "exactly one fenced block", row 22). Exit 1.
#   WARN  advisory: the rule allows the case, or the check is a heuristic (line width: §4.21 wraps
#         block lines at 100 except a lone unbreakable token, but 565+ archived prompts predate
#         that rule, so a long line is a WARN, not a FAIL; length: §4.21 allows an overrun with a
#         reason; placeholders, terminal imperative, gate labels, filename words). Never blocks.
#   Length and the stub test count a long line as ceil(len/100) lines: doctor's own measure, so a
#   prompt written in long lines (older archive files) is neither undercounted nor called a stub.
# ---------------------------------------------------------------------------------------------
PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
HEADER_KEYS = ("key", "repo", "path", "date", "archetype", "follows")
HEADER_OPTIONAL = ("flags", "via", "lock")           # E-05 fields: optional, trailing, in this order
# The E-05 vocabulary (PROTOCOL Step 6 item 2). Required for new prompts (a WARN from the lint when
# missing or unknown); files archived before it lack the fields and stay valid in --archive.
VIA_VALUES = ("argument", "continuation", "cwd", "ask")
LOCK_VALUES = ("go", "auto", "accepted", "corrected")   # go/auto skipped the wait: not confirmed locks
STAT_FLAGS = ("--go", "--brief", "--dry-run", "--verbose", "--unattended")


def known_flags() -> set[str]:
    try:
        bs = load_build_shims()
        return set(re.findall(r"--[a-z-]+", bs.FLAGS + " " + getattr(bs, "SPLIT_FLAG", "")))
    except Exception:  # noqa: BLE001 - fall back to the flags the stats know
        return set(STAT_FLAGS) | {"--repo", "--attended", "--follows", "--split"}


def vocab_problems(meta: dict[str, str], flags_known: set[str] | None = None) -> list[str]:
    """Missing or unknown flags/via/lock values in a parsed header (empty list = all good)."""
    out = []
    flags = meta.get("flags")
    if not flags:
        out.append("flags missing (flag names space-separated, or -)")
    elif flags != "-":
        known = flags_known if flags_known is not None else known_flags()
        bad = [f for f in flags.split() if f not in known]
        if bad:
            out.append(f"unknown flag(s) {' '.join(bad)}")
    via = meta.get("via")
    if not via:
        out.append(f"via missing ({'|'.join(VIA_VALUES)})")
    elif via not in VIA_VALUES:
        out.append(f"via={via} is not {'|'.join(VIA_VALUES)}")
    lock = meta.get("lock")
    if not lock:
        out.append(f"lock missing ({'|'.join(LOCK_VALUES)})")
    elif lock not in LOCK_VALUES:
        out.append(f"lock={lock} is not {'|'.join(LOCK_VALUES)}")
    return out
LINE_WIDTH = 100
MIN_BLOCK_LINES = 5      # counted lines (doctor counts ceil(len/100) per line) below which the block is a stub
# §4.21 tier caps (guide/03-blocks.md); check_tiers() keeps this map equal to the table.
TIER_CAPS = {"Delta": 120, "Focused": 200, "Slice": 260, "Program": 350}
TIER_OF = {**dict.fromkeys("EJ", "Delta"), **dict.fromkeys("ABCHKLMOPUVWX", "Focused"),
           "D": "Slice", **dict.fromkeys("FGINQRST", "Program")}
SLICE_MULTI_CAP = 320                                 # D with several checkpoints
MEASURED_LARGE = 1.2                                  # +20% when self-check row 21 names it
PLACEHOLDER_RE = re.compile(r"<(?![/!=\-])([^<>\n]{1,80})>")
HTML_TAGS = {"a", "abbr", "article", "aside", "b", "body", "br", "button", "code", "div", "em",
             "footer", "form", "h1", "h2", "h3", "h4", "head", "header", "html", "i", "img", "input",
             "label", "li", "link", "main", "meta", "nav", "ol", "option", "p", "pre", "script",
             "section", "select", "small", "span", "strong", "style", "svg", "table", "td",
             "template", "textarea", "th", "title", "tr", "ul", "video"}
IMPERATIVE_VERBS = ("start", "begin", "continue", "proceed", "resume", "go", "stop", "report",
                    "read", "run", "work", "reply", "return", "wait", "send", "do", "don't", "then",
                    "now", "confirm", "finish", "open", "fix", "implement", "write", "commit")
GATE_LABEL_RE = re.compile(r"\((?:script|contract|derived)\b|test: NONE|no gates?\b", re.I)
# PROTOCOL Step 6 item 3: the chat-side verdict line, exactly (archived files hold the full table
# instead and normally have no such line, so the check only runs where a verdict-like line exists).
VERDICT_RE = re.compile(r"^Self-check: (\d+) PASS · (\d+) N/A · (\d+) FAIL "
                        r"\((?:full table in the archive file|full table: --verbose)\)$")
# A verdict-like line: it names the self-check with a count, or gives pass AND N/A counts. Test
# results ("516 passed, 2 failed") carry no N/A, so grounding notes do not match.
VERDICT_LIKE_RE = re.compile(r"self[- ]?check\b[^\n]*\d|\b\d+\s+(?:pass(?:ed)?)\b[^\n]*\b\d+\s+"
                             r"(?:\w+\s+)?(?:N/A|not applicable)", re.I)


def verdict_check(lines: list[str], block_span: tuple[int, int] | None) -> tuple[str, str] | None:
    """(status, detail) for the chat verdict line, or None when the text has no verdict-like line.
    Table rows, headings and the fenced prompt itself are never read as a verdict line."""
    lo, hi = block_span if block_span else (-1, -1)
    cands = [(i, ln.strip()) for i, ln in enumerate(lines)
             if not (lo <= i <= hi) and i > 0 and ln.strip() and not ln.lstrip().startswith(("|", "#", "<!--"))
             and VERDICT_LIKE_RE.search(ln)]
    if not cands:
        return None
    exact = [(i, VERDICT_RE.match(s)) for i, s in cands if VERDICT_RE.match(s)]
    if not exact:
        i, s = cands[0]
        return WARN, (f"line {i + 1} paraphrases the verdict ({s[:50]!r}); PROTOCOL Step 6 item 3 wants exactly "
                      f"'Self-check: <n> PASS · <n> N/A · <n> FAIL (full table in the archive file)'")
    i, m = exact[0]
    n_pass, n_na, n_fail = (int(g) for g in m.groups())
    total = n_pass + n_na + n_fail
    # With a verdict line the chat shows only the FAIL and N/A rows (PROTOCOL Step 6 item 3, E-08),
    # so a table beside it is partial: the counts are checked against the §6 checklist, and the
    # shown rows against N/A + FAIL (or all rows, when the full table is printed instead).
    shown = sum(1 for j, ln in enumerate(lines) if re.match(r"^\|\s*\d+\s*\|", ln) and not (lo <= j <= hi))
    want = checklist_rows()
    if want and total != want:
        return WARN, (f"line {i + 1}: the verdict counts add up to {total}, but the §6 checklist has "
                      f"{want} rows (guide/04-checklist.md)")
    if shown and shown not in (n_na + n_fail, total):
        return WARN, (f"line {i + 1}: {shown} self-check rows are shown, but the verdict has "
                      f"{n_na} N/A + {n_fail} FAIL = {n_na + n_fail} (the chat shows only those rows)")
    detail = f"line {i + 1}: exact verdict line" + (f", counts cover the {want} checklist rows" if want else "")
    if shown:
        detail += f", {shown} shown row(s) match " + ("N/A + FAIL" if shown == n_na + n_fail else "the full table")
    return PASS, detail


def checklist_rows(root: Path = HOME) -> int:
    """The number of §6 self-check rows in guide/04-checklist.md (0 if it cannot be read)."""
    try:
        text = (root / "guide" / "04-checklist.md").read_text(encoding="utf-8-sig")
    except OSError:
        return 0
    return sum(1 for ln in text.splitlines() if re.match(r"^\|\s*\d+\s*\|", ln))


def is_placeholder(inner: str) -> bool:
    """A leftover generator placeholder such as <area to assess> or <script|contract>, as opposed
    to code (<div class="x">, <html lang>, Map<String, Int>, a regex like <A|Bc>, a <= b) or an
    e-mail/URL in angle brackets."""
    s = inner.strip()
    if not s or not s[0].isalpha() or "=" in s or "@" in s or "://" in s or "\\" in s:
        return False
    if s.split()[0].lower() in HTML_TAGS:                       # an HTML tag with attributes
        return False
    if re.fullmatch(r"[A-Z]\w*(\s*,\s*[A-Z]\w*)+", s):        # generic type arguments
        return False
    if "|" in s and " " not in s and not s.islower():          # a regex alternation such as A|Bc
        return False
    return bool(re.search(r"[ |…]|\.\.\.", s))


def has_imperative(line: str) -> bool:
    """Principle 12: the block ends with a terminal imperative. True when any sentence of the last
    line starts with an imperative verb, or the line says 'now'."""
    if re.search(r"\bnow\b", line, re.I):
        return True
    for sentence in re.split(r"(?<=[.;:!?])\s+|\s+[–-]\s+", line):
        words = re.findall(r"[A-Za-z']+", sentence)
        if words and words[0].lower() in IMPERATIVE_VERBS:
            return True
    return False


def parse_header(line: str) -> tuple[dict[str, str] | None, list[str]]:
    """Parse the v3 line-1 header. Returns (meta or None, problems)."""
    m = V3_HEADER_RE.match(line)
    if not m:
        return None, ["line 1 is not '<!-- genprompt v3: key=… | … -->'"]
    pairs = [kv.split("=", 1) for kv in m.group(1).split(" | ")]
    if any(len(p) != 2 for p in pairs):
        return None, ["a header field is not key=value"]
    keys = [k.strip() for k, _ in pairs]
    meta = {k.strip(): v.strip() for k, v in pairs}
    problems = []
    if tuple(keys[:len(HEADER_KEYS)]) != HEADER_KEYS:
        problems.append(f"fields must start {', '.join(HEADER_KEYS)} in that order (got {', '.join(keys)})")
    extra = keys[len(HEADER_KEYS):]
    if extra != [k for k in HEADER_OPTIONAL if k in extra]:
        problems.append(f"optional trailing fields must be a subset of {', '.join(HEADER_OPTIONAL)} "
                        f"in that order (got {', '.join(extra)})")
    if meta.get("date") and not DATE_RE.match(meta["date"]):
        problems.append(f"date={meta['date']} is not YYYY-MM-DD")
    arch = meta.get("archetype", "")
    if not re.fullmatch(r"[A-Z](\+[A-Z])*", arch):
        problems.append(f"archetype={arch!r} is not letters joined by +")
    if any(not meta.get(k) for k in HEADER_KEYS):
        problems.append("empty value in " + ", ".join(k for k in HEADER_KEYS if not meta.get(k)))
    return meta, problems


def tier_cap(letters: list[str], body: list[str], self_check: str) -> tuple[int, str]:
    """The block's line cap: the largest tier among the label's letters (§4.21)."""
    caps = []
    for letter in letters:
        tier = TIER_OF.get(letter)
        if tier is None:
            continue
        cap = TIER_CAPS[tier]
        if letter == "D" and sum(1 for ln in body if re.match(r"^\s*CHECKPOINT\b", ln)) >= 2:
            cap = SLICE_MULTI_CAP
        caps.append((cap, f"{letter}:{tier}"))
    cap, why = max(caps) if caps else (TIER_CAPS["Focused"], "default:Focused")
    row21 = next((ln for ln in self_check.splitlines() if re.match(r"^\|\s*21\s*\|", ln)), "")
    if re.search(r"measured[- ]large", row21, re.I):
        cap, why = int(cap * MEASURED_LARGE), why + " +20% measured-large (row 21)"
    return cap, why


def lint_prompt(text: str, filename: str | None = None,
                cmd_by_letter: dict[str, str] | None = None) -> list[tuple[str, str, str]]:
    """Run the per-file checks. Returns [(check, PASS|WARN|FAIL, detail)], one entry per check."""
    res: list[tuple[str, str, str]] = []
    lines = text.splitlines()

    # header (FAIL): line 1 must be a valid v3 header whose date matches the filename
    meta, problems = parse_header(lines[0] if lines else "")
    name = Path(filename).name if filename else ""
    if meta is not None and name:
        if not name.startswith(f"{meta.get('date', '')}-"):
            problems.append(f"filename {name} does not start with date={meta.get('date')}")
        if not FILE_RE.match(name):
            problems.append(f"filename {name} is not <date>-<cmd>[+<cmd>]-<slug>.md")
    res.append(("header", FAIL if problems else PASS, "; ".join(problems) or "valid v3 line-1 header"))

    # filename words (WARN): §10.1 names every archetype's command word, dominant first
    if meta is not None and name and cmd_by_letter and not problems:
        cmds = "+".join(cmd_by_letter.get(x, "?") for x in meta.get("archetype", "").split("+"))
        ok = name.startswith(f"{meta['date']}-{cmds}-")
        res.append(("filename-words", PASS if ok else WARN,
                    f"<date>-{cmds}-<slug>.md" if ok else
                    f"archetype={meta['archetype']} implies <date>-{cmds}-<slug>.md (§10.1)"))

    # one fence (FAIL when the record is broken; WARN for an extra snippet outside the prompt)
    blocks = fences(text)
    body: list[str] = []
    end = len(lines)
    fence_fail, fence_warn = [], []
    if not blocks:
        fence_fail.append("no fenced prompt")
    else:
        ticks, _start, end, body = max(blocks, key=lambda b: len(b[3]))
        if end >= len(lines):
            fence_fail.append("the fence is never closed (truncated prompt)")
        if any(t == 3 and any(re.match(r"^\s*`{3,}\S", ln) for ln in b) for t, _s, _e, b in blocks):
            fence_fail.append("a 3-backtick outer fence nests a fence, so the pasted prompt is cut off "
                              "(use 4 backticks)")
        counted_body = sum(max(1, -(-len(ln) // LINE_WIDTH)) for ln in body)
        if counted_body < MIN_BLOCK_LINES:     # width-aware: a short prompt written in long lines is fine
            fence_fail.append(f"the block has {counted_body} counted lines: a stub, not the full prompt")
        if len(blocks) > 1 and not fence_fail:
            fence_warn.append(f"{len(blocks)} top-level fenced blocks; §4.21 wants exactly one")
    status = FAIL if fence_fail else WARN if fence_warn else PASS
    res.append(("one-fence", status, "; ".join(fence_fail + fence_warn) or f"1 block, {len(body)} lines"))

    # leftover generator placeholders (WARN: heuristic; §4.0 wants worker-side variables as {…})
    found = []
    for n, ln in enumerate(body, 1):
        found += [f"block line {n}: <{m.group(1)}>" for m in PLACEHOLDER_RE.finditer(ln) if is_placeholder(m.group(1))]
    found += [f"line {n}: [generator:" for n, ln in enumerate(lines, 1) if "[generator:" in ln]
    res.append(("placeholders", WARN if found else PASS,
                ("; ".join(found[:5]) + (f" (+{len(found) - 5} more)" if len(found) > 5 else "")
                 + " (§4.0: fill it, or write a worker-side variable as {…})")
                if found else "no <…> generator placeholder or [generator: left"))

    # line width (WARN: §4.21 wraps block lines at 100; only a lone unbreakable token, such as an
    # absolute path, URL or command with no space in it, may run past on a line of its own. A WARN,
    # not a FAIL, because most of the archive predates the rule.)
    wide = [(n, len(ln)) for n, ln in enumerate(body, 1)
            if len(ln) > LINE_WIDTH and len(ln.split()) > 1]
    res.append(("line-width", WARN if wide else PASS,
                f"{len(wide)} block line(s) over {LINE_WIDTH} chars, e.g. line {wide[0][0]} ({wide[0][1]}); "
                f"§4.21: wrap at {LINE_WIDTH}, only a lone unbreakable token may run past"
                if wide else f"all block lines <= {LINE_WIDTH} chars, or a lone unbreakable token"))

    # length (WARN: §4.21 allows an overrun with a reason in self-check row 21)
    tail = "\n".join(lines[end + 1:])
    letters = (meta or {}).get("archetype", "").split("+")
    counted = sum(max(1, -(-len(ln) // LINE_WIDTH)) for ln in body)
    cap, why = tier_cap(letters, body, tail)
    res.append(("length", PASS if counted <= cap else WARN, f"{counted} counted lines, cap {cap} ({why})"))

    # terminal imperative (WARN: principle 12; the verb test is a heuristic)
    last = next((ln.strip() for ln in reversed(body) if ln.strip()), "")
    if body:
        res.append(("terminal-imperative", PASS if has_imperative(last) else WARN,
                    "the block ends with an imperative" if has_imperative(last) else
                    "the last block line is not an imperative (principle 12: 'Start with Part A now.')"))

    # gates labelled (WARN: row 8; read-only prompts may legitimately carry none)
    labelled = bool(GATE_LABEL_RE.search("\n".join(body)))
    res.append(("gates-labelled", PASS if labelled else WARN,
                "gates carry (script|contract|derived), or test: NONE is stated" if labelled else
                "no gate labelled (script), (contract) or (derived), and no 'test: NONE' (row 8)"))

    # header vocabulary (WARN: required for new prompts, PROTOCOL Step 6 item 2; never blocks)
    if meta is not None:
        vp = vocab_problems(meta)
        res.append(("header-vocab", WARN if vp else PASS,
                    "; ".join(vp) if vp else f"flags={meta['flags']} via={meta['via']} lock={meta['lock']}"))

    # report line (WARN, new convention: a prompt that asks for a report names GENPROMPT-REPORT)
    joined = "\n".join(body)
    if re.search(r"\bREPORT\b", joined):
        has = "GENPROMPT-REPORT" in joined
        res.append(("report-line", PASS if has else WARN,
                    "the report spec names a GENPROMPT-REPORT line" if has else
                    "the prompt asks for a report but has no GENPROMPT-REPORT line"))

    # chat verdict line (WARN; only where a verdict-like line exists, never on table-only files)
    span = None
    if blocks:
        _t, b_start, b_end, _b = max(blocks, key=lambda b: len(b[3]))
        span = (b_start, b_end)
    vc = verdict_check(lines, span)
    if vc:
        res.append(("verdict-line", vc[0], vc[1]))

    # self-check table after the block (FAIL: row 22, §10.2)
    has_table = bool(SELF_CHECK_RE.search(tail))
    res.append(("self-check", PASS if has_table else FAIL,
                "table present after the block" if has_table else
                "no | # | Item | Verdict | Reason | table after the block"))
    return res


def cmd_map() -> dict[str, str]:
    try:
        return {letter: cmd for letter, cmd, *_ in load_build_shims().ARCHETYPES}
    except Exception:  # noqa: BLE001 - the filename check degrades; check_suite reports the cause
        return {}


def check_tiers(root: Path = HOME) -> None:
    """Keep TIER_CAPS / TIER_OF equal to the §4.21 table in guide/03-blocks.md."""
    text = read(root / "guide" / "03-blocks.md", "suite")
    if text is None:
        return
    rows = re.findall(r"^\|\s*(Delta|Focused|Slice|Program)\s*\|\s*(\d+)[^|]*\|\s*([^|]+)\|", text, re.M)
    if len(rows) != len(TIER_CAPS):
        add("ERROR", "suite", f"guide/03-blocks.md §4.21: found {len(rows)} tier rows, doctor knows {len(TIER_CAPS)}")
    for tier, cap, letters in rows:
        if TIER_CAPS.get(tier) != int(cap):
            add("ERROR", "suite", f"§4.21 says {tier} cap {cap}; tools/doctor.py TIER_CAPS says {TIER_CAPS.get(tier)}")
        listed = set(re.findall(r"\b([A-Z])\b", letters))
        mapped = {k for k, v in TIER_OF.items() if v == tier}
        if listed != mapped:
            add("ERROR", "suite", f"§4.21 lists {tier} = {','.join(sorted(listed))}; tools/doctor.py TIER_OF has "
                                  f"{','.join(sorted(mapped))}")


def run_prompt_lint(path_arg: str) -> int:
    p = Path(path_arg)
    try:
        text = p.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        say(f"FAIL  read  cannot read {p}: {exc}")
        return 1
    results = lint_prompt(text, p.name, cmd_map())
    for check, status, detail in results:
        say(f"{status}  {check:20} {detail}")
    n = Counter(status for _c, status, _d in results)
    say()
    say(f"Prompt lint: {n[PASS]} PASS, {n[WARN]} WARN, {n[FAIL]} FAIL  ({p.name})")
    return 1 if n[FAIL] else 0


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
    counted = sum(max(1, -(-len(ln) // LINE_WIDTH)) for ln in body)   # width-aware, as in lint_prompt
    if counted < MIN_BLOCK_LINES:      # the same stub rule as lint_prompt, so the two agree
        add("ERROR", "archive", f"{rel}: longest fenced block has {counted} counted lines; the full prompt is missing")
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
                add("WARN", "archive", f"profile {prof.name} is {age} days old, past the {PROFILE_MAX_AGE_DAYS}-day "
                                       f"ceiling (§2.9): re-derive it even if its stamps still match")
        except ValueError:
            add("WARN", "archive", f"profile {prof.name}: derived date missing or invalid")
        if not re.search(r"\S+@[0-9a-f]{6,}", front.get("stamp", "")):
            add("WARN", "archive", f"profile {prof.name}: stamp is not <file>@<sha> (cannot be checked)")


def measure_header(stats: dict, fields: str) -> None:
    """Count the E-05 fields of one v3 header. Files without them are counted, never flagged."""
    meta = {k.strip(): v.strip() for k, v in (kv.split("=", 1) for kv in fields.split(" | ") if "=" in kv)}
    if not any(meta.get(k) for k in HEADER_OPTIONAL):
        stats["unmeasured"] += 1
        return
    stats["measured"] += 1
    stats["via"][meta.get("via") or "(missing)"] += 1
    stats["lock"][meta.get("lock") or "(missing)"] += 1
    flags = meta.get("flags") or "-"
    for f in (flags.split() if flags != "-" else []):
        stats["flags"][f] += 1


def measure_lines(stats: dict) -> list[str]:
    """The stats block: via, lock outcome (with the correction rate) and flag use."""
    n, old = stats["measured"], stats["unmeasured"]
    out = [f"Measured (flags/via/lock in the header): {n} file(s); {old} older file(s) predate the fields"]
    if not n:
        return out
    out.append("    via:   " + ", ".join(f"{k} {stats['via'][k]}" for k in (*VIA_VALUES, "(missing)")
                                     if stats["via"][k]) +
               "".join(f", {k} {v} (unknown)" for k, v in stats["via"].items()
                       if k not in VIA_VALUES and k != "(missing)"))
    lk = stats["lock"]
    waited = lk["accepted"] + lk["corrected"]
    rate = f"{100 * lk['corrected'] / waited:.0f}% of {waited} confirmed locks" if waited else "no confirmed locks yet"
    out.append("    lock:  " + ", ".join(f"{k} {lk[k]}" for k in (*LOCK_VALUES, "(missing)") if lk[k]) +
               "".join(f", {k} {v} (unknown)" for k, v in lk.items() if k not in LOCK_VALUES and k != "(missing)") +
               f"; correction rate {rate}")
    out.append("    flags: " + ", ".join(f"{f} {stats['flags'][f]}/{n}" for f in STAT_FLAGS) +
               "".join(f", {f} {c}/{n}" for f, c in sorted(stats["flags"].items()) if f not in STAT_FLAGS))
    return out


def check_archive(letters_by_word: dict[str, str]) -> dict:
    stats: dict = {"rows": Counter(), "arche": Counter(), "latest": {}, "files": 0,
                   "via": Counter(), "lock": Counter(), "flags": Counter(), "measured": 0, "unmeasured": 0}
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
        if header is not None:
            measure_header(stats, header.group(1))
        if rp not in referenced:
            add("ERROR" if is_v3 else "INFO", "archive", f"file with no shard row: {rel}")
        if is_v3:
            check_prompt_file(p, rel, header, referenced.get(rp), all_names)
        elif not first or not first[0].startswith("<!-- genprompt"):
            add("INFO", "archive", f"legacy file without line-1 header: {rel}")
    check_profiles(dt.date.today())
    return stats


# ---------------------------------------------------------------------------------------------
# --suggest-fixes: a PRINT-ONLY repair plan for the --archive ERRORs (and legacy label drift).
# It reads exactly what --archive reads and writes nothing, ever. A fix is "derivable" only when
# the correct value follows from the archive itself (the file's line-1 header, the shard row, a
# file that exists); everything else is "manual" and no content is invented.
# ---------------------------------------------------------------------------------------------
FILE_MSG = re.compile(r"^(?P<rel>[^:]+\.md): (?P<rest>.*)$")
ROW_MSG = re.compile(r"^(?:(?:shard fields != 5|task over \d+ chars|em-dash or middle dot in row): )?"
                     r"(?P<shard>[a-z0-9-]+\.tsv):(?P<ln>\d+)(?:: (?P<rest>.*)| \(.*\))?$")


def fit_task(task: str) -> str:
    """The shard-row form of a task (§10.3): no '|', '·', em-dash or newline, at most TASK_CAP."""
    for bad, good in (("\n", " "), ("|", "/"), ("·", "-"), ("—", "-")):
        task = task.replace(bad, good)
    return task if len(task) <= TASK_CAP else task[: TASK_CAP - 3].rstrip() + "..."


def file_meta(p: Path) -> dict[str, str] | None:
    text = read(p, "archive") if p.is_file() else None
    first = text.splitlines()[0] if text else ""
    meta, problems = parse_header(first)
    return meta if meta is not None and not problems else None


def now_line(p: Path) -> str | None:
    """The task as the prompt states it: the NOW: line inside the fenced block."""
    text = read(p, "archive") or ""
    blocks = fences(text)
    if not blocks:
        return None
    body = max(blocks, key=lambda b: len(b[3]))[3]
    for ln in body:
        m = re.match(r"^\s*NOW:\s*(.+)$", ln)
        if m:
            return fit_task(m.group(1).strip())
    return None


def shard_path_line(key: str) -> str | None:
    """The repo path for a shard header, from the first prompt file in <key>/ with a valid header."""
    for p in sorted((ARCHIVE / key).glob("*.md")) if (ARCHIVE / key).is_dir() else []:
        meta = file_meta(p)
        if meta and meta.get("path"):
            return meta["path"]
    return None


def name_parts(name: str) -> tuple[str, str, str] | None:
    """(date, cmds, slug) from <date>-<cmd>[+<cmd>]-<slug>.md."""
    m = re.match(r"^(\d{4}-\d{2}-\d{2})-([a-z]+(?:\+[a-z]+)*)-([a-z0-9-]+)\.md$", name)
    return m.groups() if m else None


def plan_row(shard: str, ln: int, msgs: list[str], cmd_by_letter: dict[str, str]) -> dict:
    path = SHARDS / shard
    lines = (read(path, "archive") or "").splitlines()
    raw = lines[ln - 1] if 0 < ln <= len(lines) else ""
    sep = shard_separator(lines)
    f = split_row(raw, sep)
    key = shard[:-4]
    item = {"where": f"by-repo/{shard}:{ln}", "errors": msgs, "before": raw, "kind": "manual"}

    if any(m.startswith("shard fields != 5") for m in msgs):
        tab = raw.split("\t")
        if len(tab) == 5 and LABEL_RE.match(tab[1].strip()) and (tab[3].strip().endswith(".md") or tab[3].strip() == "-"):
            item.update(kind="derivable", cls="tab-separated row in a ' | ' shard",
                        after=" | ".join(x.strip() for x in tab))
        else:
            item.update(cls="foreign row (not a genprompt row)",
                        fix="this row was not written by genprompt (its fields are not date, letters, slug, "
                            "file, task). Move it out of the shard, for example into a note, or delete it.")
        return item

    if len(f) != 5:
        item.update(cls="unparseable row", fix="the row does not split into 5 fields; rewrite it by hand.")
        return item
    date, label, slug, fref, task = f
    new = list(f)
    notes, manual, classes = [], [], []
    if label == "none" and fref != "-":
        if fref in {"none", "(none)", ""}:
            new[3] = "-"
            classes.append("status row file")
            notes.append("status row: file 'none' becomes '-'")
        else:
            meta = file_meta(ARCHIVE / key / fref)
            if meta:
                new[1] = meta["archetype"]
                classes.append("status row with a file")
                notes.append(f"label 'none' becomes {meta['archetype']} (from the file's line-1 header)")
            else:
                manual.append("a status row names a file that does not exist or has no header: either set "
                              "the file to '-' (a status row) or restore the file")
    if label != "none" and fref == "-":
        hits = sorted((ARCHIVE / key).glob(f"{date}-*-{slug}.md")) if (ARCHIVE / key).is_dir() else []
        if len(hits) == 1:
            new[3] = hits[0].name
            classes.append("prompt row without a file")
            notes.append("file '-' becomes the one archived file with this date and slug")
        elif task.lower().startswith("status:"):
            new[1] = "none"
            classes.append("prompt row without a file")
            notes.append("a 'status:' task with no file is a status row: label becomes 'none'")
        else:
            manual.append(f"label {label} with no file: either it is a status row (label 'none', task "
                          f"'status: …') or its prompt file is missing; only you know which")
    if any(m.startswith(("task over", "em-dash or middle dot")) or "'|' inside the task" in m for m in msgs):
        fitted = fit_task(task)
        if fitted != task:
            new[4] = fitted
            classes.append("task too long")
            notes.append(f"task shortened to {len(fitted)} characters / separators replaced (the detail stays in the file)")
    handled = ("task over", "em-dash", "row points to a missing file", "a status row must have", "file '-' is not",
               "'|' inside")
    other = [m for m in msgs if not any(h in m for h in handled)]
    manual += [f"no automatic fix: {m}" for m in other]
    if manual or not notes:
        item.update(cls="row needs a decision", fix="; ".join(manual or ["no automatic fix known"]))
        if notes:
            item["partial"] = notes
        return item
    item.update(kind="derivable", cls=" + ".join(dict.fromkeys(classes)),
                after=(" | " if sep != "\t" else "\t").join(new), notes=notes)
    return item


def plan_file(rel: str, msgs: list[str], cmd_by_letter: dict[str, str], rows_by_file: dict) -> dict:
    p = ARCHIVE / rel
    key = rel.split("/")[0] if "/" in rel else ""
    item = {"where": rel, "errors": msgs, "kind": "manual"}
    text = read(p, "archive") or ""
    lines = text.splitlines()
    m0 = msgs[0]
    if m0.startswith("file with no shard row"):
        meta = file_meta(p)
        parts = name_parts(p.name)
        task = now_line(p)
        if meta and parts and task and key:
            row = " | ".join([meta["date"], meta["archetype"], parts[2], p.name, task])
            shard = SHARDS / f"{key}.tsv"
            where = f"append below the last line of by-repo/{key}.tsv" if shard.exists() else \
                f"create by-repo/{key}.tsv with the three §10 header lines (path: {meta.get('path')}), then"
            item.update(kind="derivable", cls="file with no shard row", fix=f"{where}:", after=row,
                        notes=["task taken from the prompt's NOW: line"])
        else:
            why = "no valid line-1 header" if not meta else "no NOW: line to take the task from" if not task \
                else "the filename is not <date>-<cmd>-<slug>.md"
            item.update(cls="file with no shard row", fix=f"write its shard row by hand ({why}).")
            if meta and parts:
                item["after"] = " | ".join([meta["date"], meta["archetype"], parts[2], p.name,
                                            "<the task in one line, 200 characters at most>"])
        return item
    if "no self-check table" in m0 or "no fenced prompt" in m0 or "the full prompt is missing" in m0:
        cls = "no self-check table" if "self-check" in m0 else "no fenced prompt" if "no fenced" in m0 else "stub prompt"
        item.update(cls=cls, fix="cannot be repaired automatically (the missing content is not in the archive); "
                                 "leave it as a flagged record, or move it to ~/.genprompt/history/ with its row.")
        return item
    if "3-backtick outer fence" in m0:
        blocks = fences(text)
        outer = max(blocks, key=lambda b: len(b[3])) if blocks else None
        item.update(cls="3-backtick outer fence", fix="cannot be repaired automatically: the nested fence closed the "
                    "outer one, so where the prompt really ends is a judgement. Change the outer fence to 4 "
                    f"backticks by hand (it opens at line {outer[1] + 1 if outer else '?'}).")
        return item
    if "v3 file without the line-1 header" in m0:
        row = rows_by_file.get(p.name)
        path_ = shard_path_line(key) if key else None
        parts = name_parts(p.name)
        if row and parts and path_:
            repo = Path(path_.replace("\\", "/")).name
            hdr = (f"<!-- genprompt v3: key={key} | repo={repo} | path={path_} | date={parts[0]} | "
                   f"archetype={row[1]} | follows=- -->")
            item.update(kind="derivable", cls="missing line-1 header", fix="insert as the new line 1:", after=hdr,
                        notes=["from the shard row and the shard's path; follows is unknown, so '-'"])
        else:
            item.update(cls="missing line-1 header", fix="write the line-1 header by hand (no shard row or path to derive it from).")
        return item
    m = re.search(r"header date=(\S+) does not match the filename date", m0)
    if m:
        row = rows_by_file.get(p.name)
        fdate = p.name[:10]
        if row and row[0] == fdate and lines:
            item.update(kind="derivable", cls="header date vs filename", before=lines[0],
                        after=lines[0].replace(f"date={m.group(1)}", f"date={fdate}"),
                        notes=["the shard row agrees with the filename date"])
        else:
            item.update(cls="header date vs filename", fix="the header, filename and shard row disagree; decide which date is right.")
        return item
    item.update(cls="file needs a decision", fix="; ".join(f"no automatic fix: {x}" for x in msgs))
    return item


def plan_shard_header(shard: str, msg: str) -> dict:
    path = SHARDS / shard
    key = shard[:-4]
    lines = (read(path, "archive") or "").splitlines()
    head = []
    for ln in lines:
        if ln.strip() and not ln.startswith("#"):
            break
        head.append(ln)
    dates = [ln[:10] for ln in lines if ln.strip() and not ln.startswith("#")]
    path_ = shard_path_line(key)
    item = {"where": f"by-repo/{shard}", "errors": [msg], "kind": "manual", "cls": "shard header"}
    if dates and min(dates) >= V3_START and path_:
        item.update(kind="derivable", before="\n".join(head),
                    after=f"# genprompt shard: {key}  (path: {path_})\n"
                          "# Fields: date | archetype | slug | file | task (<=200 chars)\n# schema: v3",
                    fix=f"replace the {len(head)} comment line(s) at the top with:",
                    notes=["every row is dated on or after the v3 start, so it is a pure v3 shard (no marker needed)"])
    else:
        item["fix"] = "rows predate v3 or no path is known: write the legacy header and the marker by hand (§10.3)."
    return item


def legacy_label_drift(letters_by_word: dict[str, str]) -> list[tuple[str, str, str]]:
    """(where, before label, after label) for legacy rows whose label is a command word."""
    out = []
    for shard in sorted(SHARDS.glob("*.tsv")) if SHARDS.is_dir() else []:
        for ln, fields, is_v3, _raw in shard_rows(shard):
            if is_v3 or len(fields) < 2 or LABEL_RE.match(fields[1]):
                continue
            words = re.split(r"\s*\+\s*", fields[1].strip())
            letters = [w if w in letters_by_word.values() else letters_by_word.get(w.lower()) for w in words]
            if all(letters):
                out.append((f"by-repo/{shard.name}:{ln}", fields[1], "+".join(letters)))
    return out


def suggest_fixes() -> int:
    """Print the repair plan. Reads only; never writes. Always exit 0."""
    cmd_by_letter = cmd_map()
    letters_by_word = {cmd: letter for letter, cmd in cmd_by_letter.items()}
    stats = check_archive(letters_by_word)
    errors = [msg for sev, _area, msg in findings if sev == "ERROR"]
    if stats.get("empty"):
        say(f"No archive at {ARCHIVE}: nothing to fix.")
        return 0
    rows_by_file: dict[str, list[str]] = {}
    for shard in sorted(SHARDS.glob("*.tsv")):
        for _ln, fields, _v3, _raw in shard_rows(shard):
            if len(fields) == 5 and fields[3].endswith(".md"):
                rows_by_file.setdefault(fields[3].split("/")[-1], fields)
    findings.clear()            # shard_rows() above re-added structural findings; the plan uses `errors`

    by_row: dict[tuple[str, int], list[str]] = {}
    by_file: dict[str, list[str]] = {}
    plans, unclassified = [], []
    for msg in errors:
        if msg.startswith("file with no shard row: "):
            by_file.setdefault(msg.split(": ", 1)[1], []).insert(0, msg)
            continue
        m = ROW_MSG.match(msg)
        if m:
            by_row.setdefault((m.group("shard"), int(m.group("ln"))), []).append(msg)
            continue
        m = re.match(r"^(?P<shard>[a-z0-9-]+\.tsv): (no '# schema:' header line|legacy shard must contain.*)$", msg)
        if m:
            plans.append(plan_shard_header(m.group("shard"), msg) if "no '# schema:'" in msg else
                         {"where": f"by-repo/{m.group('shard')}", "errors": [msg], "kind": "manual",
                          "cls": "shard marker", "fix": "fix the '# --- v3 ---' marker by hand (§10.3)."})
            continue
        m = FILE_MSG.match(msg)
        if m:
            by_file.setdefault(m.group("rel"), []).append(msg)
            continue
        unclassified.append(msg)
    plans += [plan_row(s, ln, msgs, cmd_by_letter) for (s, ln), msgs in sorted(by_row.items())]
    # one plan per file ERROR: a file with no shard row may also lack its self-check, and each
    # needs its own verdict
    plans += [plan_file(rel, [msg], cmd_by_letter, rows_by_file)
              for rel, msgs in sorted(by_file.items()) for msg in msgs]
    plans += [{"where": "-", "errors": [m], "kind": "manual", "cls": "other", "fix": "no automatic fix known."}
              for m in unclassified]

    say("genprompt doctor --suggest-fixes: a PRINT-ONLY plan. Nothing has been or will be written.")
    say(f"Archive: {ARCHIVE}")
    say(f"BACK UP FIRST: copy the whole {GENPROMPT_HOME} folder to a dated folder such as "
        f"{GENPROMPT_HOME}-backup-{dt.date.today().isoformat()} before applying anything.")
    say()
    for kind in ("derivable", "manual"):
        group = [x for x in plans if x["kind"] == kind]
        say(f"== {kind.upper()} ({len(group)}) ==")
        for x in group:
            say(f"[{kind}] {x['cls']}  {x['where']}")
            for e in x["errors"]:
                say(f"    error:  {e}")
            if x.get("fix"):
                say(f"    fix:    {x['fix']}")
            for n in x.get("notes", []) + x.get("partial", []):
                say(f"    note:   {n}")
            if "before" in x and kind == "derivable":
                for i, b in enumerate(x["before"].splitlines() or [""]):
                    say(f"    {'before:' if i == 0 else '       '} {b}")
            if "after" in x:
                for i, a in enumerate(x["after"].splitlines()):
                    say(f"    {'after: ' if i == 0 else '       '} {a}")
        say()
    drift = legacy_label_drift(letters_by_word)
    say(f"== LEGACY LABEL DRIFT (INFO, optional; derivable) : {len(drift)} row(s) ==")
    say("    Legacy rows whose label is a command word; the letter form is derivable. §10.5: normalise "
        "shard rows only with a snapshot in ~/.genprompt/history/ first.")
    for where, before, after in drift if VERBOSE else []:
        say(f"    {where}: {before} -> {after}")
    if drift and not VERBOSE:
        say("    (add --verbose to list them)")
    say()
    covered = sum(len(x["errors"]) for x in plans)
    per = Counter((x["cls"], x["kind"]) for x in plans)
    say("Summary")
    say(f"  doctor --archive ERRORs: {len(errors)}; covered by this plan: {covered}")
    say(f"  fixes: {sum(1 for x in plans if x['kind'] == 'derivable')} derivable, "
        f"{sum(1 for x in plans if x['kind'] == 'manual')} manual "
        f"(a fix can cover several ERRORs on one row or file)")
    for (cls, kind), n in sorted(per.items(), key=lambda kv: (kv[0][1], -kv[1], kv[0][0])):
        say(f"    {kind:9} {n:4}  {cls}")
    say(f"  legacy label drift (INFO, optional): {len(drift)} row(s)")
    return 0


def main(argv: list[str]) -> int:
    global VERBOSE
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")
    if argv and argv[0] == "--prompt":
        if len(argv) != 2:
            say("usage: doctor.py --prompt <archive file>")
            return 2
        return run_prompt_lint(argv[1])
    if "--suggest-fixes" in argv:
        extra = [a for a in argv if a not in ("--suggest-fixes", "--verbose")]
        if extra:
            say("usage: doctor.py --suggest-fixes [--verbose]")
            return 2
        VERBOSE = "--verbose" in argv
        return suggest_fixes()
    allowed = {"--suite", "--archive", "--verbose"}
    unknown = [a for a in argv if a not in allowed]
    if unknown:
        say(f"unknown argument(s): {' '.join(unknown)}   usage: doctor.py [--suite] [--archive] [--verbose]"
            f" | doctor.py --prompt <file>")
        return 2
    VERBOSE = "--verbose" in argv
    scoped = {"--suite", "--archive"} & set(argv)
    run_suite = not scoped or "--suite" in scoped
    run_archive = not scoped or "--archive" in scoped
    stats = None
    letters_by_word: dict[str, str] = {}
    if run_suite:
        check_suite()
        check_release()
        check_tiers()
        check_bundle()
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
        for line in measure_lines(stats):
            say(line if line.startswith("  ") else f"  {line}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
