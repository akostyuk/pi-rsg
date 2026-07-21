#!/usr/bin/env python3
"""Wrapper for source_map_v2 that works from any working directory.

Usage:
    python scripts/source-map.py --target <root> --output rds/analysis/<session_name>/source-map.json

This script resolves its own location to find the source_map_v2 package,
so it works regardless of the current working directory.

Zero external dependencies — only Python stdlib.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    # Resolve the directory where THIS script lives
    script_dir = Path(__file__).resolve().parent

    # source_map_v2 is a sibling package inside scripts/
    v2_dir = script_dir / "source_map_v2"

    if not v2_dir.is_dir():
        print(
            f"ERROR: source_map_v2 package not found at {v2_dir}",
            file=sys.stderr,
        )
        print(
            f"Expected directory structure: scripts/source_map_v2/__main__.py",
            file=sys.stderr,
        )
        return 1

    # Prepend the scripts/ directory to sys.path so imports work
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    # Import and run the v2 CLI
    from source_map_v2.__main__ import main as v2_main

    return v2_main()


if __name__ == "__main__":
    sys.exit(main())
