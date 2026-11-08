#!/usr/bin/env python3
"""Stage another commit of genprompt for an eval run without touching its branch.

    python evals/prepare_worktree.py <ref> <path>      # e.g. 512e2e1 ../genprompt-wt-cp4
    python evals/prepare_worktree.py --remove <path>

It adds a DETACHED git worktree of <ref> at <path> (so no branch moves and nothing can be committed
to it by accident) and copies this tree's evals/ into it, minus results/. The copy is untracked.
`claude plugin eval` reads cases from <plugin>/evals/, so the cases must sit inside the tree under
test. Then, from <path>:

    python evals/run.py --model claude-opus-5-5 --max-cost-usd 8 --doctor <this tree>/tools/doctor.py

`--doctor` pins archive-valid to the same lint the baseline was graded with. Copy the results back
and remove the worktree afterwards.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
ROOT = EVALS.parent


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ref", nargs="?")
    ap.add_argument("path", nargs="?", type=Path)
    ap.add_argument("--remove", type=Path, help="remove a worktree made by this script")
    args = ap.parse_args()
    if args.remove:
        git("worktree", "remove", "--force", str(args.remove.resolve()))
        print(f"removed {args.remove}")
        return 0
    if not args.ref or not args.path:
        ap.error("need <ref> and <path>")
    dest = args.path.resolve()
    if dest.exists():
        sys.exit(f"{dest} already exists")
    sha = git("rev-parse", "--verify", f"{args.ref}^{{commit}}")
    git("worktree", "add", "--detach", str(dest), sha)
    if (dest / "evals").exists():
        sys.exit(f"{args.ref} already has evals/; run from it directly instead of copying")
    shutil.copytree(EVALS, dest / "evals",
                    ignore=shutil.ignore_patterns("results", "__pycache__"))
    print(f"worktree {dest} at {sha[:7]} (detached); evals/ copied from {ROOT.name}")
    print(f"next: cd {dest} && python evals/run.py --validate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
