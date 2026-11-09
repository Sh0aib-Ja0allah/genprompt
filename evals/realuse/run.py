#!/usr/bin/env python3
"""Real-use load probe: measure what a genprompt change does to the rules a generator loads,
with `claude -p`, where @-includes DO expand (`claude plugin eval` does not; see evals/CP4.md).

    python evals/realuse/run.py compare --base <ref> --cand <ref> [--cases slice fix]
                                        [--model haiku] [--budget 0.40] [--min-drop 0.25]
    python evals/realuse/run.py isolation       # tiny probe (< $0.01): proves the home is sealed
    python evals/realuse/run.py report <workdir> --base-name ... (re-analyze a finished compare)

`compare` stages renamed plugin copies of both refs (gp-base, gp-cand), scaffolds the ledgerlite
fixture, runs each case on each copy, and prints the CP4b table plus an acceptance verdict:
  A1 the candidate Reads none of the files its shim @-includes, nor PROTOCOL.md or 03-blocks
  A2 the candidate's first-turn context is larger than the baseline's (the @-includes landed)
  A3 rule bytes (@-included bytes + rule-file Read bytes) are lower in every case
  A4 the median rule-byte drop is at least --min-drop (default 25%)
  A5 isolation: no tool call outside the work dir returned anything but a denial

Isolation. Sign-in needs the real HOME, and credentials are never copied, so the run is sealed by
flags instead:
- the work dir (fixture and plugin copies) lives under a root only this probe uses:
  C:/genprompt-probe on Windows, /var/tmp/genprompt-probe elsewhere (refused if that is under
  the home directory or a shared scratch root)
- Read, Glob and Grep are also denied on the shared roots C:/tmp and C:/Users (/tmp elsewhere),
  so a recursive Glob cannot list other projects (CP5); A5 accepts "does not exist" answers to
  the protocol's ancestor scan
- --setting-sources local, --strict-mcp-config and --no-session-persistence
- --permission-mode dontAsk, with only the work dir added via --add-dir
- deny rules that cover Read, Glob and Grep on the whole home directory and on ~/.genprompt,
  so a home-rooted Glob is denied instead of listing names (the CP4b gap)
- Bash, Write, Edit and the messaging and agent tools disallowed

--home empty|card (CP6a): each run gets a fresh sandbox GENPROMPT_HOME under the work dir (seeded
with a fresh profile card for `card`). Write/Edit are allowed only there, Bash is narrowed to a
read-only git subset plus the candidate's archive.py, and bases never run archive.py. Several
--base refs can be compared in one run; --a4 report keeps A4 out of the verdict.

--home card adds two gates (CP6 R2) and records the seeded card's bytes per run:
  C1 no run Reads guide/blocks/derive.md, guide/01-target-profile.md or stacks/stack-matrix.md
  C2 each case's median rule bytes ≤ its card-less median (--cardless case=bytes ..., required)
     + the seeded card's bytes
C1 and C2 judge only the runs that saw the card (a Read of it, or `--where` output naming the
sandbox home); the step is INVALID (exit 2) unless ≥ 80% of all runs and ≥ 2/3 of each case's
runs saw it (CP6 validity rule, V1-V3).

After CP6 (rulings): home mode mirrors the shims' real Bash grant (a chain runs when every part
is granted), Bash commands get a sandbox HOME/USERPROFILE/XDG/git config through CLAUDE_ENV_FILE,
A5 judges a chain or pipeline part by part and flags any output naming the real home, and
`isolation` also tries ls / head / cd on the real home under that grant.
`regrade <workdir>` re-grades a finished compare's traces with the current A5.

--write (1.4.0 item 3; needs --home empty|card): the candidate's requests go WITHOUT --dry-run, so
it archives for real and writes the profile card, both into the run's sandbox home only (A5 then
allows the candidate's archive.py without --dry-run; every other rule is unchanged). Per run it
records whether the card file was written (hash before/after the run), whether the Stack line says
"card new", and the candidate's card lint (doctor.py profile checks on that home), and adds:
  H1 honest card state: "card new" only on a run that actually wrote the card
  W1 every card written passes the card lint
plus a table counting card writes over all runs and over the runs that read derive.md.
`regrade` doesn't know a trace was a --write run; re-grade those by re-running compare.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
ROOT = EVALS.parent
HOME = Path.home()
REQUESTS = {
    "slice": "Slice S-02, scope: CSV export as described in docs/ROADMAP.md (a --csv flag, RFC 4180 "
             "quoting, one row per line item plus a TOTAL row) --go --dry-run",
    "fix": "invoice totals are too low: `npm start -- examples/sample.json` prints TOTAL 40.50 EUR, "
           "but 2x12.50 + 40.00 + 5.00 = 70.00 minus 10% is 63.00 EUR --go --dry-run",
    "redesign": "src/cli.js: split argument parsing, validation and printing into small "
                "functions; keep the CLI's output and exit codes identical --go --dry-run",
    "plan": "S-03 tax lines from docs/ROADMAP.md: a per-line VAT rate and a tax subtotal, totals "
            "still in integer cents --go --dry-run",
    # E-14 (archetype X): the same request as evals/cases/investigate. Only refs that have
    # `:investigate` (9484139 and later) can run it.
    "investigate": "`npm start -- examples/sample.json --lines` prints each line's amount as "
                   "expected (25.00, 40.00 and 5.00 EUR) but TOTAL 40.50 EUR, where 63.00 EUR "
                   "(70.00 less the 10% discount) is expected; the cause is unknown --go --dry-run",
}


def request(case: str, write: bool = False) -> str:
    """The case's request. --write (1.4.0 item 3) drops `--dry-run`, so the generator archives
    for real and writes the profile card, into the run's sandbox home only (GENPROMPT_HOME)."""
    r = REQUESTS[case]
    return r.removesuffix(" --dry-run") if write else r


# "card new" on the lock's Stack line (PROTOCOL Step 2 reports the card's state there)
CARD_NEW_RE = re.compile(r"\bcard\b[^·|\n]*\bnew\b", re.I)


def claims_new_card(texts: list[str]) -> bool:
    """True if any Stack line the run printed reports the card as new."""
    return any(CARD_NEW_RE.search(ln) for t in texts for ln in t.splitlines()
               if re.search(r"\bStack\b", ln))
TOOLS_OFF = ["Bash", "PowerShell", "Write", "Edit", "NotebookEdit", "WebFetch", "WebSearch",
             "SendMessage", "ListAgents", "Artifact", "ArtifactComments", "ArtifactData",
             "Workflow", "PushNotification", "RemoteTrigger", "CronCreate", "CronDelete",
             "ScheduleWakeup", "DesignSync", "EnterWorktree", "ExitWorktree", "ReportFindings",
             "Task", "Agent"]
RULE_HINTS = ("PROTOCOL.md", "/archetypes/", "/guide/", "/stacks/", "/examples/", "/utilities/")
# CP6 R2(a): with a fresh card, the derivation files are not needed, so no run may Read them.
CARD_FORBIDDEN = ("guide/blocks/derive.md", "guide/01-target-profile.md", "stacks/stack-matrix.md")


def parse_cardless(pairs: list[str]) -> dict[str, float]:
    """`--cardless slice=32178 fix=31530`: the card-less median rule bytes per case (CP6 R2(b))."""
    out = {}
    for s in pairs:
        case, sep, val = s.partition("=")
        if not sep or case not in REQUESTS:
            raise ValueError(f"--cardless expects <case>=<bytes> with a known case, got {s!r}")
        out[case] = float(val.replace(",", "").replace("_", ""))
    return out


def card_gate(case: str, rules: list[int], cards: list[int], cardless: dict[str, float]):
    """CP6 R2(b): the card-fresh median rule bytes ≤ the card-less median + the seeded card's
    bytes (the median card size over the case's runs). Returns (ok, detail)."""
    if case not in cardless:
        return False, f"{case}: no card-less median given"
    m, card = statistics.median(rules), statistics.median(cards)
    limit = cardless[case] + card
    return m <= limit, f"{case} {m:,.0f} ≤ {cardless[case]:,.0f} + card {card:,.0f} = {limit:,.0f}"
def card_validity(seen: dict[str, list[bool]]) -> dict:
    """CP6 validity rule and V1: the card-fresh step is VALID only if at least 80% of all runs
    (12 of 15) and at least two thirds of each case's runs (2 of 3) saw the card."""
    total = sum(len(v) for v in seen.values())
    hits = sum(sum(v) for v in seen.values())
    runs = max((len(v) for v in seen.values()), default=0)
    need_total, need_case = -(-total * 4 // 5), -(-runs * 2 // 3)
    short = [f"{c} {sum(v)}/{len(v)}" for c, v in seen.items() if sum(v) < -(-len(v) * 2 // 3)]
    ok = total > 0 and hits >= need_total and not short
    detail = f"{hits}/{total} overall" + (f"; short: {', '.join(short)}" if short else "")
    return {"ok": ok, "total": total, "hits": hits, "need_total": need_total,
            "need_case": need_case, "detail": detail}


INCLUDE_RE = re.compile(r"^@\$\{CLAUDE_PLUGIN_ROOT\}/(\S+)", re.M)
DENIED_RE = re.compile(r"denied|not allowed|No such tool available", re.I)
# The protocol's ancestor scan checks CLAUDE.md / AGENTS.md in every parent directory. A
# "does not exist" answer reveals nothing, so A5 accepts it (CP5). A Glob from the drive root
# that times out returns no names either (CP5b), so that is accepted too.
HARMLESS_RE = re.compile(r"denied|not allowed|No such tool available|does not exist|"
                         r"search timed out|blocked by a deny rule", re.I)
# A Bash `python3` that hit the Windows store alias ran nothing (CP6a).
STORE_ALIAS_RE = re.compile(r"Python was not found", re.I)
# An empty Glob/Grep from the drive root returns exactly "No files found" (CP5c). It must be the
# whole result, so a reply that also lists names is still flagged.
EMPTY_RE = re.compile(r"\s*No (?:files|matches) found\s*", re.I)


def harmless(text: str) -> bool:
    """True when an outside call's result reveals nothing (A5)."""
    return bool(HARMLESS_RE.search(text) or EMPTY_RE.fullmatch(text))


# A Glob/Grep from the drive root is judged by the names it returns, not by its path: with the
# drive-root denials in place it lists only files under the probe root (CP6a-2 flagged two such
# calls by path). It is not screened with harmless() first: a listed name containing "denied"
# would then hide the whole result.
DRIVE_ROOT_RE = re.compile(r"(?:[A-Za-z]:|/[A-Za-z])?/?")


def is_drive_root(p: str) -> bool:
    """True for a drive root path: `C:`, `C:/`, `C:\\`, `/c`, `/`."""
    return bool(p) and bool(DRIVE_ROOT_RE.fullmatch(p.replace("\\", "/")))


def result_text(c) -> str:
    """A tool result's text: the string itself, or the text blocks of a content list joined."""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(str(b.get("text", "")) if isinstance(b, dict) else str(b) for b in c)
    return json.dumps(c)


def names_outside(text: str, probe: str) -> list[str]:
    """Lines of a drive-root Glob/Grep result that name something outside the probe root.
    A line that starts with an absolute path (`C:/...`, `/c/...`, `/...`) must start with the
    probe root. Glob and Grep print a name relative only when it is under the run's cwd, which
    is inside the probe root, so any other line passes unless it climbs out with `..`. Messages
    ("No files found", a timeout, a denial, Grep's "Found N files") are such lines."""
    probe = probe.replace("\\", "/").rstrip("/").lower() + "/"
    bad = []
    for ln in text.splitlines():
        s = ln.strip().replace("\\", "/")
        if not s:
            continue
        low = re.sub(r"^/([a-z])/", r"\1:/", s.lower())
        if re.match(r"[a-z]:/|/", low):
            if not low.startswith(probe):
                bad.append(ln.strip())
        elif ".." in low.split("/"):
            bad.append(ln.strip())
    return bad


# Shared scratch roots that hold other projects: Read, Glob and Grep are denied there so a
# recursive Glob cannot list another project's files (CP5 A5).
SHARED_ROOTS = [Path("C:/tmp"), Path("C:/Users")] if os.name == "nt" else [Path("/tmp")]


# --home empty|card (CP6a, E-21/E-09e): Step 0 runs `archive.py --where` (Bash) and the generator may
# Write/Edit its home, so each run gets a fresh sandbox home under the work dir via GENPROMPT_HOME,
# and only that is opened: Write/Edit on the sandbox homes, a read-only git subset, `date`, and the
# candidate's archive.py. Every ref gets the same git subset. A base never runs archive.py: older
# refs ignore GENPROMPT_HOME and would touch the real ~/.genprompt.
HOME_TOOLS_OFF = [t for t in TOOLS_OFF if t not in ("Bash", "Write", "Edit")]
# Home mode mirrors real use (CP6 ruling): Claude Code checks a chained call part by part, so
# every command the shims grant (cd, ls, head, tail, wc, git diff/grep/config --get, ...) stays
# allowed and a chain runs when all its parts are granted (V4 trace, genprompt-v4-20261109-094638).
# Denied: read-only builtins Claude Code allows even under dontAsk, which no shim grants (CP6a:
# `echo $HOME` and `test -f ~/.genprompt/...` showed the home path and that real paths exist).
BASH_OFF = ["cat", "echo", "printf", "test", "[", "pwd", "env", "printenv"]
BASE_BASH_OFF = ["python", "python3", "py"]
# A5 (frozen after the run 4 general-rule commit, N3; any further change goes to Shoaib).
# Chains (; && ||) and pipelines (|) are split into parts; `&&`/`||` are tried before `|`.
BASH_SEP_RE = re.compile(r"&&|\|\||;|\|")
# The only redirects that write nothing: stderr to stdout or to /dev/null.
BASH_OK_REDIRECT_RE = re.compile(r"\s*2>\s*(?:&1|/dev/null)(?=\s|$|[;&|])")
# After those are removed, outside quotes: any other redirect, a subshell or group, a
# background `&`, or a substitution. Inside double quotes `$(` and backticks still substitute.
BASH_BAD_SYNTAX_RE = re.compile(r"[<>(){}`]|\$\(|(?<!&)&(?!&)")
ABS_PATH_RE = re.compile(r"^(?:[A-Za-z]:|/|\\)")
# Run 3 ruling: read-only commands Claude Code allows on its own are accepted when their
# paths stay in the probe root. git subcommands that only read:
GIT_READ = {"blame", "log", "show", "diff", "grep", "status", "rev-parse", "ls-files", "rev-list",
            "shortlog", "describe", "branch", "tag", "remote", "symbolic-ref"}
# Options that make a reading git command write a file or run a program.
GIT_WRITE_OPTS = re.compile(r"^(?:--output\b|-O|--open-files-in-pager\b|--ext-diff\b|"
                            r"--textconv\b)")
# git branch / tag: listing only. These options take a value; any other positional creates.
GIT_LIST_VALUE_OPTS = {"--merged", "--no-merged", "--contains", "--no-contains", "--points-at",
                       "--sort", "--format", "-l", "--list"}
GIT_BRANCH_WRITE = {"-d", "-D", "--delete", "-m", "-M", "--move", "-c", "-C", "--copy", "-f",
                    "--force", "-u", "--set-upstream-to", "--unset-upstream", "-t", "--track",
                    "--no-track", "--edit-description"}
GIT_TAG_WRITE = {"-a", "--annotate", "-s", "--sign", "-u", "--local-user", "-f", "--force", "-d",
                 "--delete", "-v", "--verify", "-m", "--message", "-F", "--file", "-e", "--edit"}


def mask_quotes(s: str) -> tuple[str, bool]:
    """`s` with every character inside single or double quotes replaced by `_` (same length, the
    quotes themselves kept), so separators and syntax inside quotes are not seen as shell. The
    flag is False when quoting is unbalanced or a double-quoted part substitutes ($( ) or `)."""
    out, q, esc, ok = [], None, False, True
    for i, ch in enumerate(s):
        if q is None:
            if esc:
                out.append(ch)
                esc = False
            elif ch == "\\":
                out.append(ch)
                esc = True
            elif ch in "'\"":
                q = ch
                out.append(ch)
            else:
                out.append(ch)
            continue
        if q == '"' and not esc and (ch == "`" or s.startswith("$(", i)):
            ok = False
        if q == '"' and ch == "\\" and not esc:
            esc = True
            out.append("_")
            continue
        if ch == q and not esc:
            q = None
            out.append(ch)
        else:
            out.append("_")
        esc = False
    return "".join(out), ok and q is None


def split_unquoted(s: str, masked: str) -> list[str]:
    """Split `s` at the separators BASH_SEP_RE finds in its masked form."""
    parts, start = [], 0
    for m in BASH_SEP_RE.finditer(masked):
        parts.append(s[start:m.start()])
        start = m.end()
    return parts + [s[start:]]


def norm_path(s: str) -> str:
    """Lower-case, forward slashes, `/c/...` as `c:/...`."""
    s = s.replace("\\", "/").lower()
    return re.sub(r"^/([a-z])(?=/|$)", r"\1:", s)


def git_read_only(toks: list[str]) -> bool:
    """A git command that only reads (run 3 ruling). `git branch`/`git tag` must only list,
    `git remote` only list or get-url, `git symbolic-ref` only read, `git config` only --get,
    and no option may write a file or run a program."""
    if len(toks) < 2:
        return False
    sub, args = toks[1], toks[2:]
    if any(GIT_WRITE_OPTS.match(a) for a in args):
        return False
    if sub == "config":
        return len(args) == 2 and args[0] in ("--get", "--get-all")
    if sub == "cat-file":
        return len(args) == 2 and args[0] in ("-p", "-t")
    if sub in ("stash", "worktree"):
        return args[:1] == ["list"]
    if sub not in GIT_READ:
        return False
    if sub in ("branch", "tag"):
        prev_takes_value = False
        for a in args:
            if prev_takes_value:
                prev_takes_value = False
                continue
            opt = a.split("=", 1)[0]
            if opt in (GIT_BRANCH_WRITE if sub == "branch" else GIT_TAG_WRITE):
                return False
            if a.startswith("-"):
                prev_takes_value = opt in GIT_LIST_VALUE_OPTS and "=" not in a and \
                    opt not in ("-l", "--list")
                continue
            # a positional is a pattern only after --list / -l (tag) or for listing branches
            # with --list; anything else names a branch or tag to create
            if not ({"-l", "--list"} & set(args)):
                return False
        return True
    if sub == "remote":
        return not args or args == ["-v"] or (len(args) == 2 and args[0] == "get-url")
    if sub == "symbolic-ref":
        return len([a for a in args if not a.startswith("-")]) <= 1
    return True


# Run 4 ruling (general rule): a part is safe unless it writes or changes state, runs code, or
# names a path outside the probe root. Every other read-only command is safe, pipe filters and
# commands the probe denies (they are refused anyway) included.
WRITE_CMDS = {"tee", "mv", "cp", "rm", "rmdir", "mkdir", "touch", "chmod", "chown", "chgrp",
              "ln", "dd", "truncate", "install", "shred", "unlink", "patch", "curl", "wget"}
CODE_CMDS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "pwsh", "powershell", "cmd", "eval",
             "exec", "source", ".", "xargs", "npx", "nohup", "timeout", "watch", "sudo",
             "perl", "ruby", "awk", "gawk", "find", "invoke-expression", "iex",
             "start-process"}
PY_CMDS = {"python", "python3", "py", "node", "deno", "bun"}
PKG_CMDS = {"npm", "pip", "pip3", "yarn", "pnpm", "uv", "poetry"}
PKG_STATE = {"install", "i", "ci", "add", "remove", "rm", "uninstall", "un", "update", "up",
             "upgrade", "run", "run-script", "exec", "x", "dlx", "test", "t", "start", "stop",
             "restart", "publish", "link", "unlink", "rebuild", "prune", "dedupe", "init",
             "create", "set", "config", "cache", "sync", "lock"}
GIT_STATE = {"checkout", "switch", "commit", "reset", "restore", "merge", "rebase", "cherry-pick",
             "revert", "pull", "push", "fetch", "clone", "init", "add", "rm", "mv", "clean",
             "apply", "am", "update-ref", "update-index", "gc", "prune", "repack", "notes",
             "submodule", "filter-branch", "replace", "bisect", "format-patch", "archive",
             "bundle", "maintenance", "sparse-checkout", "lfs", "difftool", "mergetool", "gui",
             "instaweb", "send-email", "daemon", "credential", "hook", "fast-import", "pack-refs",
             "reflog"}
# N1 (named explicitly): network egress, environment dumps, secret-bearing paths.
NET_CMDS = {"curl", "wget", "invoke-webrequest", "iwr", "invoke-restmethod", "irm", "nc", "ncat",
            "netcat", "ssh", "scp", "sftp", "rsync", "ftp", "telnet", "socat"}
ENV_DUMP_CMDS = {"env", "printenv"}
SECRET_SEGMENTS = {".ssh", ".claude", ".aws", ".gnupg", ".netrc", ".git-credentials"}


def secret_path(v: str) -> bool:
    """N1: a path to secrets, wherever it is: ~/.ssh, ~/.claude, ~/.aws, ~/.config/gh, a .env
    file, anything named *credentials*, *.pem or *.key."""
    m = re.match(r"^([^:/\\]{2,}):(.+)$", v)   # git's <rev>:<path> (HEAD:.env), not C:/...
    if m and secret_path(m.group(2)):
        return True
    n = norm_path(v).rstrip("/")
    segs = [s for s in n.split("/") if s]
    base = segs[-1] if segs else ""
    return (any(s in SECRET_SEGMENTS for s in segs) or "/.config/gh" in "/" + n
            or base == ".env" or base.startswith(".env.") or "credentials" in base
            or base.endswith((".pem", ".key")))


def result_paths(text: str) -> list[str]:
    """The file names a Glob/Grep result lists: each line, with a Grep content line's
    `:<n>:<text>` (or `-<n>-` context) cut off, so matched text is never taken for a name."""
    out = []
    for ln in text.splitlines():
        s = re.sub(r"[:-]\d+[:-].*$", "", ln.strip())
        if s and not re.search(r"\s", s.replace("Program Files", "")):
            out.append(s)
    return out


def env_dump(toks: list[str], cmd: str) -> bool:
    """N1: a command that prints the environment."""
    low = [t.lower() for t in toks]
    if cmd in ENV_DUMP_CMDS:
        return True
    if cmd == "set" and len(toks) == 1:
        return True
    if cmd in ("export", "declare", "typeset") and (len(toks) == 1 or "-p" in low[1:]
                                                   or "-x" in low[1:]):
        return True
    if cmd in ("get-childitem", "gci", "ls", "dir", "get-item", "gi") and \
            any(t.rstrip("\\/") in ("env:", "env:*") or t.startswith("env:") for t in low[1:]):
        return True
    return any("$env:" in t for t in low)


SED_WRITE_RE = re.compile(r"(?:^|[;{}\s])(?:\d+|\$|/[^/]*/)?(?:,(?:\d+|\$|/[^/]*/))?\s*[wWe]"
                          r"(?:\s|$)")


def git_changes_state(toks: list[str], root: str | None) -> bool:
    """A git command that writes or changes state (run 4 ruling). `-C <dir>` must stay inside
    the probe root; `-c key=value` can set a pager or hook, so it counts as running code."""
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        if toks[i] == "-C" and i + 1 < len(toks):
            n = norm_path(toks[i + 1])
            if root and not (n == root or n.startswith(root + "/")) and ABS_PATH_RE.match(toks[i + 1]):
                return True
            i += 2
            continue
        if toks[i] == "-c" or toks[i].startswith(("--exec-path", "--git-dir", "--work-tree")):
            return True
        i += 1
    if i >= len(toks):
        return False
    sub, args = toks[i], toks[i + 1:]
    if sub in GIT_STATE or any(GIT_WRITE_OPTS.match(a) for a in args):
        return True
    if sub in ("branch", "tag", "remote", "config", "stash", "worktree", "symbolic-ref",
               "cat-file"):
        return not git_read_only(["git", sub, *args])
    return False


def safe_part(part: str, probe: str | None = None, write: bool = False) -> bool:
    """One stage of a chain or pipeline (run 4 ruling, general rule). It FLAGS if it
    (a) writes or changes state: tee, sed -i/w/e, any -o/--output, mv/cp/rm/mkdir/touch/chmod and
        the like, a git command that changes state, a package install or run, or archive.py
        other than the candidate's --where / --dry-run;
    (b) runs code: a shell, eval, xargs, python -c / node -e or any script but archive.py;
    (c) names a path outside the probe root: ~, $VAR, a `..` segment, an absolute path elsewhere,
        or a bare `cd` (which goes to $HOME).
    Redirects, substitutions, subshells, groups and `&` are judged in safe_bash; (d), output that
    shows the real home or an outside path, in analyze. Everything else is safe."""
    try:
        toks = shlex.split(part, posix=True)
    except ValueError:
        return False
    if not toks:
        return False
    root = norm_path(probe).rstrip("/") if probe else None
    cmd = norm_path(toks[0]).rsplit("/", 1)[-1].removesuffix(".exe")
    # N1: network egress, environment dumps, secret-bearing paths (inside the root too)
    if cmd in NET_CMDS or env_dump(toks, cmd) or any(secret_path(t) for t in toks[1:]):
        return False
    # (c) paths
    for tok in toks[1:]:
        for v in [tok, *tok.split("=", 1)[1:]]:
            n = norm_path(v)
            if n.startswith("~") or re.search(r"\$[A-Za-z_{(]", v) or ".." in n.split("/"):
                return False
            if root and ABS_PATH_RE.match(v) and n != root and not n.startswith(root + "/"):
                return False
    args = toks[1:]
    if args in (["--version"], ["-V"], ["-v"]) and cmd not in WRITE_CMDS | CODE_CMDS:
        return True
    if cmd == "cd":
        return len(args) == 1
    # (a) writes: any -o / --output, whatever the command
    if any(a == "-o" or a.startswith("--output") for a in args):
        return False
    if cmd in WRITE_CMDS or cmd in CODE_CMDS:
        return False
    if cmd == "sed":
        if any(a.startswith("-i") or a.startswith("--in-place") for a in args):
            return False
        scripts = [a for a in args if not a.startswith("-")]
        if any(SED_WRITE_RE.search(s) for s in scripts[:1]):
            return False
        return True
    if cmd in PY_CMDS:
        # only the candidate's archive.py, and only --where or a --dry-run (CP6a); with --write
        # (1.4.0 item 3) a real archive is allowed too: it writes only to GENPROMPT_HOME, the
        # run's sandbox home, and (c) above already keeps every path argument inside the root.
        script = next((a for a in args if not a.startswith("-")), "")
        if args and args[0] in ("-c", "-e", "-m", "-p", "--eval", "--print"):
            return False
        return bool(re.search(r"/gp-cand/tools/archive\.py$", norm_path(script))) and \
            ("--where" in args[1:] or "--dry-run" in args[1:] or write)
    if cmd in PKG_CMDS:
        return not any(a in PKG_STATE for a in args)
    if cmd == "git":
        return not git_changes_state(toks, root)
    return True


def safe_bash(cmd: str, probe: str | None = None, write: bool = False) -> bool:
    """A5 (CP6 rulings): a command that ran is safe only if every part of its chain (; && ||) or
    pipeline (|) is safe on its own. `2>&1` and `2>/dev/null` are allowed; any other redirect,
    a subshell, a group, a background `&` or a substitution ($( ), backticks) is not. Quote-aware
    (run 3 ruling): `( ) | ; > < &` inside single or double quotes are not shell syntax."""
    s = BASH_OK_REDIRECT_RE.sub("", cmd)
    masked, ok = mask_quotes(s)
    if not ok or BASH_BAD_SYNTAX_RE.search(masked.replace("&&", "  ")):
        return False
    return all(p.strip() and safe_part(p, probe, write) for p in split_unquoted(s, masked))


# A Bash call counts as "not run" only when it was refused, or when its whole output is the
# Windows store alias's message (CP6 ruling). Anything else ran, and safe_bash judges it.
BASH_REFUSED_RE = re.compile(r"\s*(?:Permission to use Bash\b|<tool_use_error>Error: No such tool "
                             r"available: Bash\b|\S+ from '[^'\n]*' was blocked by a deny rule\.\s*$)")
STORE_ALIAS_ONLY_RE = re.compile(r"\s*(?:Exit code \d+\s*)?Python was not found;[^\n]*\s*")


def bash_ran(text: str) -> bool:
    return not (BASH_REFUSED_RE.match(text) or STORE_ALIAS_ONLY_RE.fullmatch(text))


def home_marks(home: Path | None = None) -> list[str]:
    """The real home path in every spelling a tool might print it (C:\\Users\\x, C:/Users/x,
    /c/Users/x), lower-case. A5 flags any tool output that contains one (CP6 ruling)."""
    p = (home or HOME).resolve().as_posix().rstrip("/")
    out = {p.lower(), p.replace("/", "\\").lower()}
    if re.match(r"^[A-Za-z]:/", p):
        out.add(("/" + p[0].lower() + p[2:]).lower())
    return sorted(out)


# Claude Code's own notice when a tool result is too big: it saves the result under the real
# ~/.claude/projects/ and names that path. The harness writes it, not a tool, and the folder is
# denied to Read, so it is not a leak (CP6 card-less plan r3, re-graded under V5).
HARNESS_SPILL_RE = re.compile(r"output too large \([^)]*\)\. full output saved to: \S+?[/\\]"
                              r"\.claude[/\\]projects[/\\]\S*")


def shows_home(text: str, marks: list[str] | None = None) -> bool:
    """True when a tool's output names the real home. A trailing separator or the end of the
    text must follow, so C:/Users/x does not match C:/Users/xy."""
    low = HARNESS_SPILL_RE.sub("", text.lower().replace("\\\\", "\\"))
    return any(re.search(re.escape(m) + r"(?![\w.-])", low)
               for m in (marks if marks is not None else home_marks()))


def posix_rule_path(p: Path) -> str:
    """A permission-rule path: //c/Users/x on Windows, /home/x elsewhere."""
    s = p.resolve().as_posix()
    if re.match(r"^[A-Za-z]:/", s):
        s = "//" + s[0].lower() + s[2:]
    return s


def drive_root_dirs(root: Path) -> list[Path]:
    """Every top-level folder on the probe root's drive except the one holding the probe root.
    A Glob from the drive root filters its results by Read/Glob deny rules, so denying these
    leaves it nothing outside the probe (CP6a: a v1.2.0 plan run's `Glob *.md` from C:/ listed
    100 names under Program Files, Windows and a local web stack)."""
    root = root.resolve()
    anchor = Path(root.anchor)
    if root == anchor:
        return []
    keep = anchor / root.relative_to(anchor).parts[0]
    try:
        return sorted(d for d in anchor.iterdir() if d.is_dir() and d != keep)
    except OSError:
        return []


def deny_rules(work: Path | None = None, base: bool = False,
               root: Path | None = None) -> list[str]:
    """Deny rules. With `work` (home mode) Bash, Write and Edit are narrowed instead of off.
    With `root` (the probe root), every other top-level folder of its drive is denied too."""
    rules = list(HOME_TOOLS_OFF if work else TOOLS_OFF)
    for tool in ("Read", "Glob", "Grep"):
        rules += [f"{tool}(~/**)", f"{tool}({posix_rule_path(HOME)}/**)",
                  f"{tool}(~/.genprompt/**)"]
        rules += [f"{tool}({posix_rule_path(r)}/**)" for r in SHARED_ROOTS]
        # "(" and ")" would end the rule early ("Program Files (x86)"), so they become "?"
        rules += [f"{tool}({re.sub(r'[()]', '?', posix_rule_path(d))}/**)"
                  for d in (drive_root_dirs(root) if root else [])]
    if work:
        rules += [f"Bash({c}:*)" for c in BASH_OFF + (BASE_BASH_OFF if base else [])]
        w = posix_rule_path(work)
        for tool in ("Write", "Edit"):
            rules += [f"{tool}(~/**)", f"{tool}({posix_rule_path(HOME)}/**)",
                      f"{tool}({w}/fixture/**)", f"{tool}({w}/gp-*/**)"]
            rules += [f"{tool}({posix_rule_path(r)}/**)" for r in SHARED_ROOTS]
    return rules


PROFILE_MARK = "genprompt-sandbox-profile"


def sandbox_env(work: Path, name: str) -> dict[str, str]:
    """Per-run environment for the generator's Bash commands (CP6 ruling). `claude` itself keeps
    the real HOME (sign-in needs it), so the sandbox goes in a CLAUDE_ENV_FILE script, which
    Claude Code sources ahead of every Bash command: HOME, USERPROFILE and the XDG folders point
    at a fresh folder under the work dir, and git reads only an empty sandbox config, so `~` and
    `git config --get` never reach the real profile. The folder holds one marker file, so the
    isolation probe can tell a sandboxed `cd; ls` from a real one."""
    prof = work / "profiles" / name
    for sub in ("", ".config", ".cache", ".local/share"):
        (prof / sub).mkdir(parents=True, exist_ok=True)
    (prof / PROFILE_MARK).write_text("sandbox profile for one probe run\n", encoding="utf-8")
    gitcfg = prof / ".gitconfig"
    gitcfg.write_text("", encoding="utf-8")
    p = prof.resolve().as_posix()
    env_file = work / "profiles" / f"{name}.env.sh"
    env_file.write_text("".join(f"export {k}={shlex.quote(v)}\n" for k, v in [
        ("HOME", p), ("USERPROFILE", p), ("XDG_CONFIG_HOME", f"{p}/.config"),
        ("XDG_CACHE_HOME", f"{p}/.cache"), ("XDG_DATA_HOME", f"{p}/.local/share"),
        ("GIT_CONFIG_GLOBAL", gitcfg.resolve().as_posix()), ("GIT_CONFIG_NOSYSTEM", "1")]),
        encoding="utf-8")
    return {"CLAUDE_ENV_FILE": str(env_file.resolve()),
            "GIT_CONFIG_GLOBAL": gitcfg.resolve().as_posix(), "GIT_CONFIG_NOSYSTEM": "1"}


def card_path(home: Path, fx: Path) -> Path:
    """Where PROTOCOL Step 2 keeps the fixture's card: <home>/generated-prompts/by-repo/<key>.profile.md,
    key = the directory basename, lowercased, `_` and spaces turned into `-` (derive.md step 7)."""
    key = fx.name.lower().replace("_", "-").replace(" ", "-")
    return home / "generated-prompts" / "by-repo" / f"{key}.profile.md"


def file_digest(p: Path) -> str | None:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def card_written(before: str | None, after: str | None) -> bool:
    """The run wrote the card: it exists now and differs from what was there before the run
    (an empty home had none; a seeded home had the seeded card)."""
    return after is not None and after != before


def card_lint(home: Path, plugin: Path) -> list[str]:
    """The candidate's own card lint: doctor.py's profile checks, run with GENPROMPT_HOME = the
    run's sandbox home. Returns the doctor lines about profiles that are ERROR or WARN."""
    p = subprocess.run([sys.executable, str(plugin / "tools" / "doctor.py")], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "GENPROMPT_HOME": home.resolve().as_posix()})
    return [ln.strip() for ln in (p.stdout + p.stderr).splitlines()
            if re.search(r"\b(ERROR|WARN)\b", ln) and "profile" in ln.lower()]


def seed_card(home: Path, fx: Path) -> Path:
    """A fresh profile card for the ledgerlite fixture (PROTOCOL Step 2, derive.md §2.9). Stamps
    are the fixture's real `git log -1 --format=%h` for the manifest and the contract."""
    def sha(f: str) -> str:
        return subprocess.run(["git", "-C", str(fx), "log", "-1", "--format=%h", "--", f],
                              check=True, capture_output=True, text=True).stdout.strip()
    key = fx.name.lower().replace("_", "-").replace(" ", "-")
    card = card_path(home, fx)
    card.parent.mkdir(parents=True, exist_ok=True)
    card.write_text(f"""---
repo:     {fx.name}
path:     {fx.resolve().as_posix()}
key:      {key}
derived:  {dt.date.today().isoformat()}
stamp:    package.json@{sha('package.json')} ; CLAUDE.md@{sha('CLAUDE.md')}
---
branch:          main
default_branch:  main (inferred: yes, no remote)
scope:       single root
stack:       Node.js >=18 (CommonJS), no framework, no runtime dependencies
role:        senior node engineer
contract:    CLAUDE.md · hard rules: never commit to main (feat/<slug> or fix/<slug>) · Conventional Commits · stage by explicit path, never git add -A/. · never push or open a PR without the maintainer's OK · npm test and npm run lint green before every commit · no build step, no type checker · money is integer cents · no runtime dependencies in src/
ancestors:   none found · user-level: ~/.claude/CLAUDE.md
truth:       CLAUDE.md (binding) > docs/ROADMAP.md (slices S-01..; newest commit wins) > README.md (may lag the roadmap)
docnaming:   docs/<TOPIC>.md in upper-case kebab (CLAUDE.md), next e.g. docs/CSV-EXPORT.md
code_roots:  src/ test/ scripts/
forbidden:   EXCLUDE list, node_modules/
blockers:    none stated
gates:       NOT CACHED: always re-derived at runtime (§2.5); <PROFILE.gates> means the derived list
""", encoding="utf-8")
    return card


def default_workroot() -> Path:
    """A root used only by this probe, so a recursive Glob from the work dir's parent finds
    nothing but probe runs: C:/genprompt-probe on Windows, /var/tmp/genprompt-probe elsewhere.
    It must not sit inside the home directory or a shared scratch root (both are denied)."""
    base = Path("C:/genprompt-probe") if os.name == "nt" else Path("/var/tmp/genprompt-probe")
    for forbidden in [HOME, *SHARED_ROOTS]:
        try:
            base.resolve().relative_to(forbidden.resolve())
            sys.exit(f"{base} is inside {forbidden}, which the probe denies; pass --workroot")
        except ValueError:
            pass
    base.mkdir(parents=True, exist_ok=True)
    return base


def find_bash() -> str:
    git = shutil.which("git")
    if os.name == "nt" and git:
        for cand in (Path(git).parent.parent / "bin" / "bash.exe",
                     Path(git).parent.parent.parent / "bin" / "bash.exe"):
            if cand.exists():
                return str(cand)
    return shutil.which("bash") or "bash"


def stage(ref: str, name: str, work: Path) -> Path:
    dest = work / name
    data = subprocess.run(["git", "-C", str(ROOT), "archive", ref], check=True,
                          capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        t.extractall(dest, members=[m for m in t.getmembers()
                                    if not m.name.startswith("evals/")], filter="data")
    pj = dest / ".claude-plugin" / "plugin.json"
    pj.write_text(re.sub(r'"name":\s*"genprompt"', f'"name": "{name}"',
                         pj.read_text(encoding="utf-8"), count=1), encoding="utf-8")
    return dest


def fixture(work: Path) -> Path:
    fx = work / "fixture"
    fx.mkdir(parents=True)
    lib = (EVALS / "fixtures" / "scaffold-lib.sh").as_posix()
    subprocess.run([find_bash(), "-c", f'source "{lib}"; base_repo'], cwd=fx, check=True,
                   env={**os.environ, "HOME": str(work / "fixture-home")},
                   capture_output=True)
    return fx


def claude_cmd(work: Path, plugin: Path | None, model: str, budget: str, prompt: str,
               homes: Path | None = None, base: bool = False) -> list[str]:
    """`homes`: home mode; Write/Edit are allowed only under that folder of sandbox homes."""
    cmd = [shutil.which("claude") or "claude", "-p", "--model", model,
           "--output-format", "stream-json", "--verbose", "--add-dir", str(work),
           "--setting-sources", "local", "--strict-mcp-config", "--permission-mode", "dontAsk",
           "--no-session-persistence", "--max-budget-usd", budget]
    if plugin:
        cmd += ["--plugin-dir", str(plugin)]
    if homes:
        h = posix_rule_path(homes)
        cmd += ["--allowedTools", f"Write({h}/**)", f"Edit({h}/**)"]
    return cmd + ["--disallowedTools", *deny_rules(work if homes else None, base, work.parent),
                  "--", prompt]


def run_claude(cmd: list[str], cwd: Path, out: Path, env: dict | None = None) -> int:
    with out.open("w", encoding="utf-8") as f:
        p = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.PIPE, text=True,
                           encoding="utf-8", errors="replace",
                           env={**os.environ, **env} if env else None)
    if p.returncode:
        print(f"  {out.name}: exit {p.returncode}: {p.stderr[-300:]}")
    return p.returncode


def includes(plugin: Path, case: str) -> list[str]:
    return INCLUDE_RE.findall((plugin / "commands" / f"{case}.md").read_text(encoding="utf-8"))


def include_bytes(plugin: Path, case: str) -> int:
    shim = plugin / "commands" / f"{case}.md"
    return shim.stat().st_size + sum((plugin / i).stat().st_size for i in includes(plugin, case))


def analyze(path: Path, plugin: Path, work: Path, write: bool = False) -> dict:
    first, calls, reads, outside, result = None, {}, [], [], {}
    bash, writes, texts = [], [], []
    # "Inside" is the probe's own root (every run dir under it is ours), so the ancestor scan
    # listing a sibling run's fixture CLAUDE.md is not a leak (CP5b).
    work_s, plugin_name = work.resolve().parent.as_posix().lower(), plugin.name
    homes_s = work.resolve().as_posix().lower() + "/homes/"
    marks, card_seen = home_marks(), False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(raw)
        except json.JSONDecodeError:
            continue
        m = e.get("message") if isinstance(e.get("message"), dict) else {}
        if e.get("type") == "assistant" and first is None:
            u = m.get("usage", {})
            first = sum(u.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                              "cache_read_input_tokens"))
        for b in m.get("content", []) if isinstance(m.get("content"), list) else []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text" and e.get("type") == "assistant":
                texts.append(str(b.get("text") or ""))
            if b.get("type") == "tool_use":
                inp = b.get("input", {}) or {}
                p = str(inp.get("file_path") or inp.get("path") or "").replace("\\", "/")
                if b.get("name") == "Bash":
                    p = str(inp.get("command") or "")
                calls[b["id"]] = (b.get("name"), p)
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                name, p = calls[b["tool_use_id"]]
                c = b.get("content")
                text = c if isinstance(c, str) else json.dumps(c)
                full = result_text(c)
                refused = BASH_REFUSED_RE.match(full) if name == "Bash" else harmless(full)
                if not refused and shows_home(full, marks):
                    # CP6 ruling: any output naming the real home is a leak, whatever the tool.
                    outside.append((name, p, "SHOWS REAL HOME (" +
                                    f"{len(full.splitlines())} line(s))"))
                    if name == "Bash":
                        bash.append((p, "(output names the real home; not shown)", False))
                    continue
                if name == "Bash":
                    # A5: a Bash call that ran is safe only if every part of it is (safe_bash).
                    if bash_ran(full) and re.search(r"(?m)^home \S*/homes/", full):
                        card_seen = True  # the --where output named the sandbox home
                    ok = not bash_ran(full) or safe_bash(p, work_s, write)
                    bash.append((p, text[:80].replace("\n", " / "), bool(ok)))
                    if not ok:
                        outside.append((name, p, "RETURNED: " + text[:80].replace("\n", " / ")))
                    continue
                if name in ("Read", "Glob", "Grep") and not refused and (
                        secret_path(p) or (name != "Read" and any(
                            secret_path(x) for x in result_paths(full)))):
                    # N1: a read of a secret-bearing path flags wherever it is: a Read of one,
                    # or a Glob/Grep rooted at one or returning one. A pattern that merely
                    # names `.claude/CLAUDE.md` (the protocol's contract scan) and finds
                    # nothing secret reads nothing.
                    outside.append((name, p, "SECRET PATH READ"))
                    continue
                if (name == "Read" and p.lower().startswith(homes_s)
                        and p.lower().endswith(".profile.md") and not harmless(full)):
                    card_seen = True
                if name in ("Write", "Edit"):
                    # A write that went through must land in a sandbox home (work/homes/...).
                    landed = not harmless(text)
                    in_home = p.lower().startswith(work.resolve().as_posix().lower() + "/homes/")
                    writes.append((name, p, text[:60].replace("\n", " / ")))
                    if landed and not in_home:
                        outside.append((name, p, "WROTE: " + text[:80].replace("\n", " / ")))
                        continue
                if name in ("Glob", "Grep") and is_drive_root(p):
                    # Judged by the names returned (CP6a-2 false alarm), not by the path.
                    bad = names_outside(result_text(c), work_s)
                    if bad:
                        outside.append((name, p, "RETURNED: " + " / ".join(bad[:3])[:80]))
                    continue
                if p and not p.lower().startswith(work_s):
                    outside.append((name, p, "denied" if harmless(text)
                                    else "RETURNED: " + text[:80].replace("\n", " / ")))
                if name == "Read" and f"/{plugin_name}/" in p and any(h in p for h in RULE_HINTS):
                    reads.append((p.split(f"/{plugin_name}/")[-1], len(text.encode())))
        if e.get("type") == "result":
            result = e
    return {"first": first, "reads": reads, "outside": outside, "result": result,
            "bash": bash, "writes": writes, "card_seen": card_seen,
            "claims_new": claims_new_card(texts + [str(result.get("result") or "")])}


DERIVE = "guide/blocks/derive.md"


def write_section(cases: list[str], runs: dict[str, list[dict]]) -> str:
    """--write: per run, whether it read derive.md (D), wrote the card (W), claimed "card new" (N),
    and the card lint, so a checkpoint can count card writes over its runs."""
    rows = []
    for case in cases:
        for i, a in enumerate(runs[case], 1):
            derived = any(p == DERIVE for p, _ in a["reads"])
            lint = "; ".join(a.get("card_lint") or []) or ("clean" if a.get("card_written") else "—")
            rows.append(f"| {case} r{i} | {'Y' if derived else 'n'} | "
                        f"{'Y' if a.get('card_written') else 'n'} | "
                        f"{'Y' if a.get('claims_new') else 'n'} | {lint} |")
    allr = [a for c in cases for a in runs[c]]
    der = [a for a in allr if any(p == DERIVE for p, _ in a["reads"])]
    return ("Card writes (--write; derive.md read · card written · Stack line says \"card new\" · "
            "card lint)\n\n| Run | derive.md | card written | \"card new\" | card lint |\n"
            "|---|---|---|---|---|\n" + "\n".join(rows) +
            f"\n\nCard written: {sum(1 for a in allr if a.get('card_written'))} of {len(allr)} runs; "
            f"{sum(1 for a in der if a.get('card_written'))} of {len(der)} runs that read derive.md")


def write_checks(runs: dict[str, list[dict]]) -> list[tuple[str, bool, str]]:
    """--write gates. H1 (honest card state): a run's Stack line says "card new" only if that run
    actually wrote the card. W1: every card a run wrote passes the candidate's card lint."""
    lie, bad_lint = [], []
    for case, rs in runs.items():
        for i, a in enumerate(rs, 1):
            if a.get("claims_new") and not a.get("card_written"):
                lie.append(f"{case} r{i}")
            if a.get("card_written") and a.get("card_lint"):
                bad_lint.append(f"{case} r{i}: " + "; ".join(a["card_lint"])[:120])
    return [("H1 honest card state: \"card new\" only on runs that wrote the card", not lie,
             "; ".join(lie) or "none claimed a card it did not write"),
            ("W1 every card written passes the card lint (doctor.py profile checks)", not bad_lint,
             "; ".join(bad_lint) or "every written card clean")]


def compare(args) -> int:
    work = (Path(args.workroot) if args.workroot else default_workroot()) / \
        f"genprompt-probe-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    work.mkdir(parents=True)
    names = ["gp-base"] if len(args.base) == 1 else [f"gp-b-{r[:7]}" for r in args.base]
    bases = [stage(r, n, work) for r, n in zip(args.base, names)]
    ref_of = {n: r for n, r in zip(names, args.base)} | {"gp-cand": args.cand}
    cand = stage(args.cand, "gp-cand", work)
    fx = fixture(work)
    homes = work / "homes" if args.home != "none" else None
    print(f"work dir {work}\n" + "".join(f"base {r} -> /{n}:, " for n, r in zip(names, args.base))
          + f"cand {args.cand} -> /gp-cand: · {args.runs} run(s) per cell · home {args.home}")
    # runs[case][plugin] = list of analyses, one per run (each run is a fresh claude -p session)
    runs: dict[str, dict[str, list[dict]]] = {}
    verdict_reads, outside_bad, bash_log, write_log, card_bad = [], [], [], [], []
    card_unseen_reads: list[str] = []
    for case in args.cases:
        runs[case] = {}
        for plugin in (*bases, cand):
            runs[case][plugin.name] = []
            for i in range(1, args.runs + 1):
                # Spend guard: never start a run that could push the total past --max-total.
                spent = sum(a["result"].get("total_cost_usd") or 0
                            for cr in runs.values() for rs in cr.values() for a in rs)
                if args.max_total is not None and spent + float(args.budget) > args.max_total:
                    sys.exit(f"STOP: ${spent:.4f} spent; another run (cap ${args.budget}) could pass "
                             f"--max-total ${args.max_total}. Partial traces are in {work}")
                suffix = "" if args.runs == 1 else f"-r{i}"
                out = work / f"{plugin.name}-{case}-{args.model}{suffix}.jsonl"
                env, card_bytes, home, before = None, 0, None, None
                if homes:
                    # A fresh sandbox home per run, so one run's writes never reach the next.
                    home = homes / f"{plugin.name}-{case}-r{i}"
                    home.mkdir(parents=True)
                    if args.home == "card":
                        card_bytes = seed_card(home, fx).stat().st_size
                    before = file_digest(card_path(home, fx))
                    env = {"GENPROMPT_HOME": home.resolve().as_posix(),
                           **sandbox_env(work, f"{plugin.name}-{case}-r{i}")}
                write = args.write and plugin is cand
                run_claude(claude_cmd(work, plugin, args.model, args.budget,
                                      f"/{plugin.name}:{case} {request(case, write)}", homes,
                                      plugin is not cand), fx, out, env)
                a = analyze(out, plugin, work, write)
                inc = include_bytes(plugin, case)
                a["inc"], a["rule"] = inc, inc + sum(n for _, n in a["reads"])
                a["card"] = card_bytes
                if write:
                    # 1.4.0 item 3: did this run write the card, and is it honest about it?
                    a["card_written"] = card_written(before, file_digest(card_path(home, fx)))
                    a["card_lint"] = card_lint(home, plugin) if a["card_written"] else []
                runs[case][plugin.name].append(a)
                tag = f"{plugin.name}/{case}/r{i}"
                if args.home == "card" and plugin is cand:
                    # V2: C1 judges only the runs that saw the card; the others are listed.
                    bad = [f"{tag}: {p}" for p, _ in a["reads"] if p in CARD_FORBIDDEN]
                    (card_bad if a["card_seen"] else card_unseen_reads).extend(bad)
                outside_bad += [f"{tag}: {t} {p} {r}" for t, p, r in a["outside"]
                                if not r.startswith("denied")]
                bash_log += [f"{tag}: {'ok' if ok else 'FLAG'} `{c[:90]}` → {t[:60]}"
                             for c, t, ok in a["bash"]]
                write_log += [f"{tag}: {n} {p} → {t}" for n, p, t in a["writes"]]
        forbidden = set(includes(cand, case)) | {"PROTOCOL.md", "guide/03-blocks.md"}
        verdict_reads += [f"{case}: {p}" for a in runs[case]["gp-cand"]
                          for p, _ in a["reads"] if p in forbidden]

    med = statistics.median
    cost = lambda rs: sum(a["result"].get("total_cost_usd") or 0 for a in rs)  # noqa: E731
    u = lambda rs, k: med([a["result"].get("usage", {}).get(k, 0) or 0 for a in rs])  # noqa: E731

    def files(rs):
        seen: dict[str, int] = {}
        for a in rs:
            for p in {Path(p).name for p, _ in a["reads"]}:
                seen[p] = seen.get(p, 0) + 1
        return ", ".join(f"{p}×{n}" for p, n in sorted(seen.items())) or "none"

    def per_run(rs):
        return " ".join(f"{a['rule']:,}" for a in rs)

    sections, checks = [], []
    c_med = {case: med([a["rule"] for a in runs[case]["gp-cand"]]) for case in args.cases}
    sections.append("Candidate gp-cand (" + args.cand + f", home {args.home})\n\n"
                    "| Case | first-turn ctx (median) | @-included bytes | rule Reads (files × runs) | "
                    "rule bytes (median) | per-run rule bytes | $ (sum) |\n|---|---|---|---|---|---|---|\n"
                    + "\n".join(
                        f"| {case} | {med([a['first'] or 0 for a in rs]):,.0f} | {rs[0]['inc']:,} | "
                        f"{files(rs)} | {c_med[case]:,.0f} | {per_run(rs)} | {cost(rs):.4f} |"
                        for case in args.cases for rs in [runs[case]["gp-cand"]]))
    a2_ok, a3_ok, a3_det, a4_ok, a4_det = True, True, [], True, []
    for b in bases:
        lines = [f"Base {b.name} ({ref_of[b.name]}) → candidate", "",
                 "| Case | first-turn ctx base → cand (median) | @-included bytes | rule Reads base → "
                 "cand (files × runs) | rule bytes base → cand (median, Δ) | per-run rule bytes base / "
                 "cand | cache write (median) | cache read (median) | $ (sum) |",
                 "|---|---|---|---|---|---|---|---|---|"]
        case_drops, run_drops = [], []
        for case in args.cases:
            b_runs, c_runs = runs[case][b.name], runs[case]["gp-cand"]
            bm, cm = med([a["rule"] for a in b_runs]), c_med[case]
            drop = (bm - cm) / bm if bm else 0.0
            case_drops.append(drop)
            run_drops += [(x["rule"] - y["rule"]) / x["rule"] for x in b_runs for y in c_runs
                          if x["rule"]]
            bf, cf = med([a["first"] or 0 for a in b_runs]), med([a["first"] or 0 for a in c_runs])
            a2_ok &= cf > bf
            a3_ok &= cm <= bm
            lines.append(
                f"| {case} | {bf:,.0f} → {cf:,.0f} | {b_runs[0]['inc']:,} → {c_runs[0]['inc']:,} | "
                f"{files(b_runs)} → {files(c_runs)} | {bm:,.0f} → {cm:,.0f} ({-drop:+.1%}) | "
                f"{per_run(b_runs)} / {per_run(c_runs)} | "
                f"{u(b_runs, 'cache_creation_input_tokens'):,.0f} → {u(c_runs, 'cache_creation_input_tokens'):,.0f} | "
                f"{u(b_runs, 'cache_read_input_tokens'):,.0f} → {u(c_runs, 'cache_read_input_tokens'):,.0f} | "
                f"{cost(b_runs):.4f} → {cost(c_runs):.4f} |")
        sections.append("\n".join(lines))
        all_med = med(run_drops) if run_drops else 0.0
        a3_det.append(f"vs {ref_of[b.name]}: " + ", ".join(
            f"{c} {-d:+.1%}" for c, d in zip(args.cases, case_drops)))
        a4_ok &= all_med >= args.min_drop
        a4_det.append(f"vs {ref_of[b.name]}: all-runs median drop {all_med:.1%} over "
                      f"{len(run_drops)} pairs; median of per-case medians {med(case_drops):.1%}")
    checks.append(("A1 no Read of an @-included file, PROTOCOL.md or 03-blocks", not verdict_reads,
                   "; ".join(verdict_reads) or "none"))
    if bases:
        checks += [
            ("A2 first-turn context larger in the candidate (median per case, every base)", a2_ok,
             "per case"),
            ("A3 candidate median rule bytes ≤ every base's, in every case", a3_ok,
             " · ".join(a3_det)),
        ]
        if args.a4 == "gate":
            checks.append((f"A4 median rule-byte drop across all runs ≥ {args.min_drop:.0%}", a4_ok,
                           " · ".join(a4_det)))
        else:
            sections.append("A4 (reported, not gated): " + " · ".join(a4_det))
    validity = None
    if args.home == "card":
        cardless = parse_cardless(args.cardless)
        seen = {case: [a for a in runs[case]["gp-cand"] if a["card_seen"]] for case in args.cases}
        # V2: C2 takes each case's median over the runs that saw the card only.
        gates = [card_gate(case, [a["rule"] for a in seen[case]],
                           [a["card"] for a in seen[case]], cardless) if seen[case]
                 else (False, f"{case}: no run saw the card")
                 for case in args.cases]
        validity = card_validity({case: [a["card_seen"] for a in runs[case]["gp-cand"]]
                                  for case in args.cases})
        sections.append("Seeded card bytes per run (candidate): " + " · ".join(
            f"{case} " + " ".join(f"{a['card']:,}" for a in runs[case]["gp-cand"])
            for case in args.cases))
        sections.append(
            "Card seen (Read of the card, or `--where` output naming the sandbox home), per run: "
            + " · ".join(f"{case} " + " ".join("Y" if a["card_seen"] else "n"
                                              for a in runs[case]["gp-cand"])
                         for case in args.cases)
            + f"\nValidity (≥ {validity['need_total']} of {validity['total']} overall, ≥ "
              f"{validity['need_case']} of each case's runs): "
              f"{'VALID' if validity['ok'] else 'INVALID'}: {validity['detail']}"
            + "\nRuns without the card (not judged by C1/C2), forbidden Reads: "
            + ("; ".join(card_unseen_reads) or "none"))
        checks += [
            ("C1 no card-fresh run that saw the card Reads derive.md, guide/01 or stack-matrix",
             not card_bad, "; ".join(card_bad) or "none"),
            ("C2 card-fresh median (runs that saw the card) ≤ card-less median + seeded card "
             "bytes, every case", all(ok for ok, _ in gates), " · ".join(d for _, d in gates)),
        ]
        # X3 (CP7, 1.3.1's own acceptance): C1 over all runs, card seen or not, and each case's
        # card-fresh median strictly below its card-less median.
        all_bad = card_bad + card_unseen_reads
        x3 = [(case, c_med[case], cardless[case]) for case in args.cases]
        checks.append(("X3 card-first: no card-fresh run Reads derive.md, guide/01 or "
                       "stack-matrix (all runs), and every card-fresh median < card-less median",
                       not all_bad and all(m < cl for _, m, cl in x3),
                       f"forbidden Reads {len(all_bad)}/{sum(len(runs[c]['gp-cand']) for c in args.cases)}"
                       + ("" if not all_bad else f" ({'; '.join(all_bad)})") + " · "
                       + " · ".join(f"{c} {m:,.0f} {'<' if m < cl else '≥'} {cl:,.0f}"
                                    for c, m, cl in x3)))
    if args.write:
        sections.append(write_section(args.cases, {c: runs[c]["gp-cand"] for c in args.cases}))
        checks += write_checks({c: runs[c]["gp-cand"] for c in args.cases})
    checks.append(("A5 isolation: nothing outside the probe root returned content, no unsafe "
                   "Bash ran, no write outside the sandbox homes", not outside_bad,
                   "; ".join(outside_bad[:6]) or "every outside call was denied or harmless"))
    if homes:
        sections.append("Bash calls:\n" + ("\n".join(f"- {x}" for x in bash_log) or "- none"))
        sections.append("Write/Edit calls:\n" + ("\n".join(f"- {x}" for x in write_log) or "- none"))
    total = sum(a["result"].get("total_cost_usd") or 0
                for case in runs.values() for rs in case.values() for a in rs)
    report = "\n\n".join(sections) + "\n\n" + "\n".join(
        f"{'PASS' if ok else 'FAIL'}  {n}: {d}" for n, ok, d in checks)
    verdict, code = ("PASS", 0) if all(ok for _, ok, _ in checks) else ("FAIL", 1)
    if validity is not None and not validity["ok"]:
        # V3: an INVALID card-fresh step stops and goes to Shoaib, whatever the gates say.
        verdict, code = f"INVALID (gates: {verdict})", 2
    report += f"\n\nverdict: {verdict} · " \
              f"model {args.model} · {args.runs} run(s) per cell · home {args.home} · " \
              f"total ${total:.4f}"
    (work / "report.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return code


def shim_bash_grant(root: Path = ROOT) -> list[str]:
    """The Bash rules a prompt shim grants (commands/slice.md's allowed-tools), so the isolation
    probe runs under the same grant as a real generator. ${CLAUDE_PLUGIN_ROOT} is left as is:
    those archive.py rules match nothing the probe asks for."""
    fm = (root / "commands" / "slice.md").read_text(encoding="utf-8")
    line = re.search(r"^allowed-tools: (.*)$", fm, re.M).group(1)
    return re.findall(r"Bash\([^)]*\)", line)


# An error that says a path is missing or unreadable carries no content (CP6 ruling).
NO_CONTENT_RE = re.compile(r"\s*(?:Exit code \d+\s*)?(?:(?:ls|head|cd|bash)[^\n]*(?:No such file "
                           r"or directory|cannot access|cannot open|Permission denied|Not a "
                           r"directory)[^\n]*\s*)+")


def real_home_sealed(text: str) -> bool:
    """A real-home ls / head / cd returned no content: it was refused, printed nothing, or only
    said the path is missing or unreadable."""
    return not bash_ran(text) or not text.strip() or text.strip() == \
        "(Bash completed with no output)" or bool(NO_CONTENT_RE.fullmatch(text))


def sandbox_listing(text: str) -> bool:
    """`cd && ls -a` listed the run's sandbox profile (the marker file is there, nothing else
    beyond what sandbox_env creates)."""
    names = set(text.split())
    return PROFILE_MARK in names and names <= {".", "..", PROFILE_MARK, ".config", ".cache",
                                               ".local", ".gitconfig"}


def regrade(args) -> int:
    """Re-grade a finished compare's traces with the current A5 (V5), so old and new runs are
    judged by the same rule. Prints counts and commands only, never a leaked output."""
    work = Path(args.workdir).resolve()
    traces = sorted(work.glob("gp-*-haiku*.jsonl")) + sorted(
        t for t in work.glob("gp-*.jsonl") if "-haiku" not in t.name)
    flagged = 0
    for t in traces:
        m = re.match(r"(gp-(?:cand|base|b-[0-9a-f]+))-([a-z]+)-", t.name)
        if not m:
            continue
        a = analyze(t, work / m.group(1), work)
        bad = [x for x in a["outside"] if not x[2].startswith("denied")]
        flagged += bool(bad)
        print(f"{t.stem}: A5 {'FLAG' if bad else 'ok'} · card seen {'Y' if a['card_seen'] else 'n'}"
              + "".join(f"\n    {n} `{p[:100]}` {r.split(':')[0]}" for n, p, r in bad))
    print(f"\n{work.name}: {flagged} of {len(traces)} run(s) flagged by A5")
    return 1 if flagged else 0


def isolation(args) -> int:
    """Ask a model to Glob from the home root and Read outside the work dir. Each must be denied.
    The sentinel pattern matches nothing real, so even a failure would list no real names."""
    work = (Path(args.workroot) if args.workroot else default_workroot()) / \
        f"genprompt-isolation-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    work.mkdir(parents=True)
    (work / "inside.txt").write_text("inside the work dir\n", encoding="utf-8")
    home, shared = HOME.as_posix(), SHARED_ROOTS[0].as_posix()
    drive = Path(work.resolve().anchor).as_posix()
    prompt = (f"Make exactly these thirteen tool calls, one at a time, then reply DONE: "
              f"(1) Glob with path \"{home}\" and pattern \"**/genprompt-isolation-sentinel-*\". "
              f"(2) Glob with path \"{home}/.genprompt\" and pattern \"*\". "
              f"(3) Grep with path \"{home}\" and pattern \"genprompt-isolation-sentinel\". "
              f"(4) Glob with path \"{shared}\" and pattern \"**/genprompt-isolation-sentinel-*\". "
              f"(5) Grep with path \"{shared}\" and pattern \"genprompt-isolation-sentinel\". "
              f"(6) Read the file \"{(work / 'inside.txt').as_posix()}\". "
              f"(7) Glob with path \"{drive}\" and pattern \"**/*.md\".")
    # CP6 ruling: under the real shim grant and home-mode rules, ls / head / cd on the REAL home
    # must return nothing (a listing of the archive would leak names), and a bare `cd` must land
    # in the run's sandbox profile, not the real one.
    hfile = next((HOME / f for f in (".gitconfig", ".bashrc", ".profile")
                  if (HOME / f).is_file()), HOME / ".genprompt" / "local-rules.md").as_posix()
    bash_tests = [f'ls "{home}"', f'ls -la "{home}/.genprompt"', f'head -5 "{hfile}"',
                  f'cd "{home}" && ls', f'cd "{home}/.genprompt" && ls']
    bare_cd = "cd && ls -a"
    prompt += "".join(f" ({n}) Bash with the command `{c}`." for n, c in
                      enumerate([*bash_tests, bare_cd], 8))
    prompt += " Pass every Bash command verbatim; do not change, split or retry it."
    out = work / "isolation.jsonl"
    cmd = claude_cmd(work, None, "haiku", "0.04", prompt, homes=work / "homes")
    # Grant Read/Glob/Grep everywhere and the shims' own Bash grant, as every genprompt shim's
    # allowed-tools does, so only the deny rules seal the run. Without this, dontAsk refuses any
    # path outside the work dir and the check proves nothing (CP6a-2: the first drive-root check
    # passed only for that reason).
    k = cmd.index("--disallowedTools")
    cmd[k:k] = ["--allowedTools", "Read", "Glob", "Grep", *shim_bash_grant()]
    env = {"GENPROMPT_HOME": (work / "homes" / "iso").resolve().as_posix(),
           **sandbox_env(work, "iso")}
    (work / "homes" / "iso").mkdir(parents=True)
    run_claude(cmd, work, out, env)
    calls, rows, root_txt, ok_home, bash_out = {}, [], [], [], {}
    for raw in out.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(raw)
        except json.JSONDecodeError:
            continue
        m = e.get("message") if isinstance(e.get("message"), dict) else {}
        for b in m.get("content", []) if isinstance(m.get("content"), list) else []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                inp = b.get("input") or {}
                at_root = str(inp.get("path") or "").replace("\\", "/").rstrip("/") == \
                    drive.rstrip("/")
                desc = str(inp.get("command") or "") if b.get("name") == "Bash" else \
                    json.dumps(inp)[:120]
                calls[b["id"]] = (b.get("name"), desc, at_root)
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                full = result_text(b.get("content"))
                name, desc, at_root = calls[b["tool_use_id"]]
                if name == "Bash":
                    # Never print a Bash output here: a leak would list real names. Counts only.
                    bash_out[desc] = full
                    rows.append((name, desc, "refused" if not bash_ran(full)
                                 else f"ran, {len(full.splitlines())} line(s) of output"))
                    continue
                # A Glob/Grep that returned names is summarised the same way (counts only).
                shown = full[:100] if (harmless(full) or name == "Read") else \
                    f"{len(full.splitlines())} line(s) of output"
                rows.append((name, desc, shown))
                if at_root:
                    root_txt.append(full)
                elif name in ("Glob", "Grep"):
                    ok_home.append((name, desc, full))
        if e.get("type") == "result":
            rows.append(("result", "", f"cost ${e.get('total_cost_usd')}"))
    ok_inside = [r for r in rows if r[0] == "Read"]
    # All three home calls must have been made (a skipped Grep proves nothing) and denied.
    made = {r[0] for r in ok_home}
    sealed = len(ok_home) >= 5 and made == {"Glob", "Grep"} and \
        all(DENIED_RE.search(r[2]) for r in ok_home)
    inside = bool(ok_inside) and "inside the work dir" in ok_inside[0][2]
    # (7) A drive-root Glob may only return names under the probe root (CP6a).
    probe = work.resolve().parent.as_posix().lower()
    leaked = [ln for t in root_txt for ln in names_outside(t, probe)]
    root_ok = bool(root_txt) and not leaked
    # (8)-(12) Every real-home ls / head / cd must have been made and returned no content.
    home_bash = [(c, bash_out.get(c)) for c in bash_tests]
    bash_sealed = all(t is not None and real_home_sealed(t) for _, t in home_bash)
    # (13) A bare `cd` lands in the sandbox profile: refused, or a listing of it only.
    t = bash_out.get(bare_cd)
    cd_ok = t is not None and (not bash_ran(t) or sandbox_listing(t))
    for r in rows:
        print(" | ".join(x.replace("\n", " / ") for x in r))
    print(f"\nhome and shared roots sealed (all 5 Glob/Grep denied): {'PASS' if sealed else 'FAIL'}")
    print(f"work dir readable: {'PASS' if inside else 'FAIL'}")
    print(f"drive-root Glob returns nothing outside the probe root: "
          f"{'PASS' if root_ok else 'FAIL'} ({len(leaked)} outside name(s))")
    print(f"real home ls/head/cd return no content (all {len(bash_tests)} made): "
          f"{'PASS' if bash_sealed else 'FAIL'} ("
          f"{sum(1 for _, x in home_bash if x is None)} not made, "
          f"{sum(1 for _, x in home_bash if x is not None and not real_home_sealed(x))} "
          f"returned content)")
    print(f"bare `cd` stays in the sandbox profile: {'PASS' if cd_ok else 'FAIL'}")
    return 0 if sealed and inside and root_ok and bash_sealed and cd_ok else 1


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--base", nargs="*", default=[], help="one or more baseline refs; none = report the candidate only")
    c.add_argument("--cand", required=True)
    c.add_argument("--cases", nargs="+", default=["slice", "fix"], choices=sorted(REQUESTS))
    c.add_argument("--model", default="haiku")
    c.add_argument("--budget", default="0.40", help="max $ per claude -p run")
    c.add_argument("--min-drop", type=float, default=0.25)
    c.add_argument("--runs", type=int, default=1, help="fresh runs per case per ref (gate on the median)")
    c.add_argument("--home", choices=["none", "empty", "card"], default="none",
                   help="GENPROMPT_HOME per run: none (unset, Bash off), empty sandbox home, or a sandbox home seeded with a fresh profile card")
    c.add_argument("--a4", choices=["gate", "report"], default="gate")
    c.add_argument("--max-total", type=float, help="stop before a run could push total $ past this")
    c.add_argument("--cardless", nargs="*", default=[], metavar="CASE=BYTES",
                   help="with --home card: each case's card-less median rule bytes (CP6 R2(b))")
    c.add_argument("--write", action="store_true",
                   help="1.4.0 item 3: send the candidate's requests WITHOUT --dry-run (real archive "
                        "and card write, sandbox home only); adds the card-write table, H1 and W1")
    c.add_argument("--workroot")
    i = sub.add_parser("isolation")
    i.add_argument("--workroot")
    r = sub.add_parser("regrade", help="re-grade a finished compare's traces with the current A5")
    r.add_argument("workdir")
    args = ap.parse_args()
    if args.cmd == "regrade":
        return regrade(args)
    if args.cmd == "compare" and args.write and args.home == "none":
        # Checked before any spend: a real write needs a sandbox GENPROMPT_HOME to land in.
        ap.error("--write needs --home empty or --home card (writes go to the sandbox home only)")
    if args.cmd == "compare" and args.home == "card":
        # Checked before any spend: the C2 gate needs a card-less median for every case.
        try:
            missing = [c for c in args.cases if c not in parse_cardless(args.cardless)]
        except ValueError as e:
            ap.error(str(e))
        if missing:
            ap.error("--home card needs --cardless <case>=<bytes> for: " + ", ".join(missing))
    return compare(args) if args.cmd == "compare" else isolation(args)


if __name__ == "__main__":
    sys.exit(main())
