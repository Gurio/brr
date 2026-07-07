#!/usr/bin/env python3
"""Report local worktree/branch hygiene in dry-run mode."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from brr.worktree_hygiene import main as run_main

    return run_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
