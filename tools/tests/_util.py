"""Shared helpers for the tools tests (stdlib only)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # the plugin root
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_tool(script: Path, *args: str, home: Path | None = None, cwd: Path = ROOT) -> tuple[int, str]:
    """Run a tool as a subprocess and return (exit code, stdout+stderr as text)."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    env.pop("GENPROMPT_HOME", None)
    if home is not None:
        env["GENPROMPT_HOME"] = str(home)
    proc = subprocess.run([sys.executable, str(script), *args], cwd=str(cwd), env=env,
                          capture_output=True, encoding="utf-8", errors="replace", check=False)
    return proc.returncode, proc.stdout + proc.stderr


def error_lines(out: str) -> list[str]:
    return [ln for ln in out.splitlines() if ln.startswith("ERROR")]
