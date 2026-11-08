"""Build the Agensi skill bundle (a zip with a SKILL.md) from the suite, deterministically.

Usage:  python tools/build_skill_bundle.py [--out <dir>]      (default: dist/agensi/, gitignored)

Agensi lists skills as "a .zip with a SKILL.md inside". genprompt is a plugin whose commands use
${CLAUDE_PLUGIN_ROOT}, so the bundle adds a SKILL.md that names "the folder containing this
SKILL.md" as the genprompt root and points the agent at the rulebook, the same way BOOTSTRAP.md
does for chats without the plugin. The layout matches the 1.0.0 upload: one top-level genprompt/
folder holding SKILL.md plus the suite (the 1.0.0 zip was the whole repo minus .github/).

Nothing in SKILL.md is typed by hand: the version, description and licence come from
.claude-plugin/plugin.json, and the command list and counts from the tables in
tools/build_shims.py, so the listing cannot drift from the release (1.1.0's said "22-row").

Contents: every git-tracked file except .github/, evals/, tools/tests/, assets/ and the git
dotfiles (CI, the eval harness, the unit tests and README images are not part of the skill).
Never anything from ~/.genprompt. The zip is deterministic: sorted entries, a fixed timestamp,
fixed permissions and compression, LF text as stored in git, so two builds have the same sha256.

Writes <out>/genprompt-agensi-<version>.zip and <out>/genprompt-agensi-<version>-SKILL.md (a loose
copy for the listing form), then prints both paths, the file count and the zip's sha256.
Standard library only.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
TOP = "genprompt"                                         # the zip's single top-level folder
EXCLUDE_PREFIXES = (".github/", "evals/", "tools/tests/", "assets/")
EXCLUDE_FILES = {".gitignore", ".gitattributes", "SKILL.md"}
FIXED_TIME = (2026, 1, 1, 0, 0, 0)                        # zip timestamps carry no build time
FILE_MODE = 0o100644 << 16


def load_build_shims():
    spec = importlib.util.spec_from_file_location("build_shims_for_bundle", ROOT / "tools" / "build_shims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def plugin_meta() -> dict:
    return json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))


def bundle_files(root: Path = ROOT) -> list[str]:
    """Repo-relative POSIX paths that go into the bundle, sorted."""
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True)
        tracked = [p for p in out.stdout.decode("utf-8").split("\0") if p]
    except (OSError, subprocess.CalledProcessError):           # not a git checkout: walk the tree
        tracked = [p.relative_to(root).as_posix() for p in root.rglob("*")
                   if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts]
    keep = [p for p in tracked
            if not p.startswith(EXCLUDE_PREFIXES) and p not in EXCLUDE_FILES and (root / p).is_file()]
    return sorted(keep)


def skill_md(meta: dict, bs) -> str:
    """SKILL.md, derived from plugin.json and the build_shims tables."""
    arche = list(bs.ARCHETYPES)
    utils = list(bs.UTILITIES)
    n_cmds = 1 + len(arche) + len(utils)
    lines = [
        "---",
        f"name: {meta['name']}",
        f"description: {json.dumps(meta['description'], ensure_ascii=False)}",
        f"license: {meta.get('license', 'MIT')}",
        f"version: {meta['version']}",
        "---",
        "",
        f"# genprompt {meta['version']}",
        "",
        meta["description"],
        "",
        "## Setup",
        "",
        "The genprompt root is **the folder that contains this SKILL.md**. Wherever the rules say",
        "`${CLAUDE_PLUGIN_ROOT}`, use that folder. Your own writable folder is `~/.genprompt/` (the",
        "prompt archive and your personal rules); every repository, and the genprompt root, stays",
        "read-only.",
        "",
        "Before generating a prompt, read:",
        "1. `PROTOCOL.md`: the runtime steps; it always applies",
        "2. `archetypes/README.md`: the picker (which archetype fits a request)",
        "3. `guide/00-index.md`: where every other rule lives",
        "4. `~/.genprompt/local-rules.md`: personal rules, if the file exists",
        "",
        "Then read the one archetype file the request needs, `archetypes/<letter>-<command>.md`, and",
        "only the guide sections you use. With the Claude Code plugin installed, the same rules load",
        f"through its {n_cmds} slash commands instead (`/plugin marketplace add {meta.get('repository', '').split('github.com/')[-1]}`).",
        "",
        f"## The {len(arche)} archetypes",
        "",
        "| Letter | Command | What it generates |",
        "|---|---|---|",
    ]
    lines += [f"| {a.letter} | `/genprompt:{a.cmd}` | {a.desc} |" for a in arche]
    lines += [
        "",
        f"`/genprompt:{bs.ENTRY}` picks the archetype from the request.",
        "",
        f"## The {len(utils)} utilities (no worker prompt)",
        "",
        "| Command | What it does |",
        "|---|---|",
    ]
    lines += [f"| `/genprompt:{u.cmd}` | {u.desc} |" for u in utils]
    lines += [
        "",
        "## Integrity",
        "",
        "`python tools/doctor.py --suite` checks this bundle (0 ERROR expected). Prompts are archived",
        "only through `tools/archive.py`, which writes under `~/.genprompt/` and nowhere else.",
        "",
        f"Source and issues: {meta.get('homepage', '')} · licence: {meta.get('license', 'MIT')}.",
        "",
    ]
    return "\n".join(lines)


def build(out_dir: Path) -> dict:
    meta = plugin_meta()
    bs = load_build_shims()
    skill = skill_md(meta, bs)
    files = bundle_files()
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"genprompt-agensi-{meta['version']}.zip"
    entries = [(f"{TOP}/SKILL.md", skill.encode("utf-8"))]
    entries += [(f"{TOP}/{p}", (ROOT / p).read_bytes()) for p in files]
    entries.sort(key=lambda e: e[0])
    with zipfile.ZipFile(zpath, "w") as zf:
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = FILE_MODE
            info.create_system = 3                                  # same header on every OS
            zf.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    loose = out_dir / f"genprompt-agensi-{meta['version']}-SKILL.md"
    loose.write_text(skill, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(zpath.read_bytes()).hexdigest()
    return {"zip": zpath, "skill": loose, "files": len(entries), "sha256": digest,
            "version": meta["version"], "names": [n for n, _ in entries]}


def main(argv: list[str]) -> int:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")
    if argv and (argv[0] != "--out" or len(argv) != 2):
        sys.stdout.write("usage: build_skill_bundle.py [--out <dir>]\n")
        return 2
    out = Path(argv[1]) if argv else ROOT / "dist" / "agensi"
    r = build(out)
    sys.stdout.write(f"bundle   {r['zip']}\n")
    sys.stdout.write(f"SKILL.md {r['skill']}\n")
    sys.stdout.write(f"version  {r['version']} · {r['files']} files\n")
    sys.stdout.write(f"sha256   {r['sha256']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
