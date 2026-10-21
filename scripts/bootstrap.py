#!/usr/bin/env python
"""Check the local environment and prepare a working checkout.

Usage:
    python scripts/bootstrap.py          # checks only
    python scripts/bootstrap.py --sync   # also run `uv sync` (dev group + provider SDKs)

Never creates API keys or enables paid providers. It prints the steps for doing so.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRS = [
    "data/raw", "data/transcriptions", "data/reference_translations", "data/processed", "data/splits",
    "data/annotations/reviews", "data/annotations/review_packages", "experiments/runs",
]  # fmt: skip


def main(argv: list[str]) -> int:
    ok = True
    if sys.version_info < (3, 12):
        print(
            f"FAIL  Python 3.12+ required (found {sys.version.split()[0]}); uv can install it: `uv python install 3.12`"
        )
        ok = False
    else:
        print(f"PASS  Python {sys.version.split()[0]}")
    uv = shutil.which("uv")
    print(
        f"{'PASS' if uv else 'FAIL'}  uv {'found at ' + uv if uv else 'not found: https://docs.astral.sh/uv/'}"
    )
    ok &= bool(uv)
    for d in DIRS:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    print(f"PASS  data/experiment directories present ({len(DIRS)})")
    if "--sync" in argv and uv:
        rc = subprocess.call([uv, "sync", "--extra", "providers"], cwd=ROOT)
        print(f"{'PASS' if rc == 0 else 'FAIL'}  uv sync")
        ok &= rc == 0
    providers = ROOT / "config" / "providers.yaml"
    env = ROOT / ".env"
    print("\nNext steps:")
    print("  uv run nr info                 # project status")
    print("  uv run nr demo                 # offline demonstration (synthetic, zero cost)")
    print("  uv run pytest                  # tests (offline)")
    if not providers.exists():
        print(
            "  (optional) cp config/providers.example.yaml config/providers.yaml  # to configure real providers"
        )
    if not env.exists():
        print("  (optional) cp .env.example .env and add keys locally — never commit it")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
