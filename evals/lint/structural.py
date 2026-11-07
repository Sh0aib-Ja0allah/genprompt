"""Deterministic graders for one genprompt emission (the generator's final chat message).

`claude plugin eval` has no custom-code graders, so these run after the eval, in evals/run.py,
over each run's final message and workspace. They mirror the mechanical rows of guide/04-checklist.md
(8, 16, 21, and the write boundary).

PLANNED SWAP: E-04a adds `tools/doctor.py --prompt <file>`, a lint for the same rows. When it lands,
replace `check_prompt_text` with a call to it, so there is one validator, not two that drift.
`grade()`'s signature and result shape stay the same.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

PASS, FAIL, SKIPPED = "PASS", "FAIL", "SKIPPED"
LINE_MAX = 100
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
NPM_BUILTINS = {"install", "i", "ci", "ls", "view", "init", "outdated", "audit", "pack"}

FENCE_RE = re.compile(r"^(`{3,})(.*)$")
LOCK_LINE_RE = re.compile(r"^(Repo|Gates|Archetype)\s{2,}\S")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
PLACEHOLDER_RE = re.compile(r"(?<![\w`])<(?:…|[A-Za-z][A-Za-z0-9 ._|/:-]{0,60})>")
GATE_RE = re.compile(r"\b(npm|pnpm|yarn)\s+(run(?:-script)?\s+)?([A-Za-z0-9:_-]+)")
CITE_RE = re.compile(r"(?<![\w/.~{-])((?:[\w.-]+/)*[\w.-]+\.(?:js|json|md|sh|txt|yml|yaml))"
                     r":(\d+)(?:\s*[-–]\s*(\d+))?")


@dataclass
class Result:
    name: str
    status: str
    detail: str

    def as_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "detail": self.detail}


def top_level_blocks(text: str) -> list[dict]:
    """Top-level fenced blocks: {'ticks', 'info', 'lines', 'closed'}. A fence closes only on a
    bare line of at least as many backticks, so a 3-backtick outer fence around a nested fence
    splits in two, which is exactly the nesting defect row 16 is about."""
    blocks, cur = [], None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if cur is None:
            if m:
                cur = {"ticks": len(m.group(1)), "info": m.group(2).strip(), "lines": [],
                       "closed": False}
            continue
        if m and len(m.group(1)) >= cur["ticks"] and not m.group(2).strip():
            cur["closed"] = True
            blocks.append(cur)
            cur = None
        else:
            cur["lines"].append(line)
    if cur is not None:
        blocks.append(cur)
    return blocks


def is_lock_block(block: dict) -> bool:
    hits = {LOCK_LINE_RE.match(l).group(1) for l in block["lines"] if LOCK_LINE_RE.match(l)}
    return len(hits) >= 2 or any(l.startswith("TARGET LOCK") for l in block["lines"][:2])


def prompt_block(text: str) -> tuple[dict | None, list[dict]]:
    blocks = [b for b in top_level_blocks(text) if not is_lock_block(b)]
    if not blocks:
        return None, blocks
    return max(blocks, key=lambda b: len(b["lines"])), blocks


def prose_lines(block: dict) -> list[str]:
    """Lines of the prompt outside nested fences, with inline code removed."""
    out, inside = [], False
    for line in block["lines"]:
        if FENCE_RE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(INLINE_CODE_RE.sub("", line))
    return out


def block_cost(lines: list[str]) -> int:
    return sum(max(1, math.ceil(len(l) / LINE_MAX)) for l in lines)


def check_prompt_text(text: str, cap: int, cap_multi: int | None = None,
                      scripts: set[str] | None = None,
                      files: dict[str, int] | None = None) -> list[Result]:
    res: list[Result] = []
    res.append(Result("lock-present", PASS if "TARGET LOCK" in text else FAIL,
                      "TARGET LOCK found" if "TARGET LOCK" in text else "no TARGET LOCK"))

    block, others = prompt_block(text)
    if block is None:
        res.append(Result("one-fence", FAIL, "no fenced prompt block"))
        for name in ("no-placeholders", "line-length", "length-cap", "gates-exist", "cites-real"):
            res.append(Result(name, FAIL, "no prompt block to check"))
        return res
    nested = any(FENCE_RE.match(l) for l in block["lines"])
    problems = []
    if len(others) != 1:
        problems.append(f"{len(others)} top-level non-lock fenced blocks")
    if not block["closed"]:
        problems.append("prompt fence never closed")
    if nested and block["ticks"] < 4:
        problems.append("nested fence inside a 3-backtick outer fence")
    res.append(Result("one-fence", FAIL if problems else PASS,
                      "; ".join(problems) or f"one {block['ticks']}-backtick block, "
                                              f"{len(block['lines'])} lines"))

    leftovers = [m.group(0) for l in prose_lines(block) for m in PLACEHOLDER_RE.finditer(l)]
    leftovers += ["<…>"] * sum(l.count("<…>") for l in block["lines"])
    gen = text.count("[generator:")
    if gen:
        leftovers.append(f"[generator: ×{gen}")
    res.append(Result("no-placeholders", FAIL if leftovers else PASS,
                      ", ".join(sorted(set(leftovers))[:8]) or "none"))

    long_lines = [(i + 1, len(l)) for i, l in enumerate(block["lines"]) if len(l) > LINE_MAX]
    res.append(Result("line-length", FAIL if long_lines else PASS,
                      f"{len(long_lines)} line(s) > {LINE_MAX}: "
                      + ", ".join(f"L{i}={n}" for i, n in long_lines[:6])
                      if long_lines else f"all ≤ {LINE_MAX}"))

    checkpoints = sum(1 for l in block["lines"] if re.match(r"^\s*CHECKPOINT\s+[A-Z]\b", l))
    limit = cap_multi if (cap_multi and checkpoints >= 2) else cap
    cost = block_cost(block["lines"])
    res.append(Result("length-cap", PASS if cost <= limit else FAIL,
                      f"{cost} counted lines vs cap {limit}"
                      + (f" ({checkpoints} checkpoints)" if cap_multi else "")))

    if scripts is None:
        res.append(Result("gates-exist", SKIPPED, "no manifest given"))
    else:
        used, missing = set(), set()
        for line in block["lines"]:
            for m in GATE_RE.finditer(line):
                script = m.group(3)
                if not m.group(2) and m.group(1) == "npm" and script in NPM_BUILTINS:
                    continue
                if not m.group(2) and m.group(1) == "npm" and script not in ("test", "start"):
                    continue  # `npm <other>` is an npm verb, not a script gate
                used.add(script)
                if script not in scripts:
                    missing.add(script)
        if missing:
            res.append(Result("gates-exist", FAIL, "not in package.json scripts: "
                              + ", ".join(sorted(missing))))
        elif not used:
            res.append(Result("gates-exist", FAIL, "no literal npm gate in the prompt"))
        else:
            res.append(Result("gates-exist", PASS, "gates: " + ", ".join(sorted(used))))

    if files is None:
        res.append(Result("cites-real", SKIPPED, "no workspace file list given"))
    else:
        bad, seen = [], 0
        for line in block["lines"]:
            for m in CITE_RE.finditer(line):
                path, lo, hi = m.group(1).lstrip("./"), int(m.group(2)), m.group(3)
                seen += 1
                top = int(hi) if hi else lo
                if path not in files:
                    bad.append(f"{path}:{lo} (no such file)")
                elif top > files[path] or lo < 1:
                    bad.append(f"{path}:{top} (file has {files[path]} lines)")
        res.append(Result("cites-real", FAIL if bad else PASS,
                          "; ".join(bad[:6]) if bad else f"{seen} path:line citation(s) checked"))
    return res


def check_writes(tool_uses: list[str] | None, home: Path | None) -> Result:
    if tool_uses is None:
        return Result("no-writes", SKIPPED, "no trace given")
    writes = [t for t in tool_uses if t in WRITE_TOOLS]
    archive = []
    if home is not None and (home / ".genprompt").exists():
        archive = [p for p in (home / ".genprompt").rglob("*") if p.is_file()]
    if writes or archive:
        return Result("no-writes", FAIL, f"write tool calls: {writes or 'none'}; "
                                         f"files under ~/.genprompt: {len(archive)}")
    return Result("no-writes", PASS, "no write tool calls, nothing under the temp ~/.genprompt")


def check_archive() -> Result:
    return Result("archive-valid", SKIPPED, "skipped: needs tools/archive.py (E-04)")


def grade(text: str, *, cap: int, cap_multi: int | None = None, scripts: set[str] | None = None,
          files: dict[str, int] | None = None, tool_uses: list[str] | None = None,
          home: Path | None = None) -> list[Result]:
    return (check_prompt_text(text, cap, cap_multi, scripts, files)
            + [check_writes(tool_uses, home), check_archive()])
