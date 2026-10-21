#!/usr/bin/env python
"""Generate (or with --check, verify) schemas/*.schema.json from the Pydantic models.

Usage:
    uv run python scripts/generate_schemas.py          # regenerate
    uv run python scripts/generate_schemas.py --check  # exit 1 if stale (used in CI)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nostradamus_research.schemas import generate_schemas, stale_schemas  # noqa: E402


def main(argv: list[str]) -> int:
    directory = ROOT / "schemas"
    if "--check" in argv:
        stale = stale_schemas(directory)
        if stale:
            print(f"Stale schemas: {stale}. Run: uv run python scripts/generate_schemas.py")
            return 1
        print("Schemas are up to date.")
        return 0
    for path in generate_schemas(directory):
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
