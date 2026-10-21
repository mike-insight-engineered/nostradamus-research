#!/usr/bin/env python
"""Export a blinded human-review package (thin wrapper around `nr review export`).

Usage:
    uv run python scripts/export_review_package.py --run experiments/runs/<RUN_ID> [--run ...] --package-id PKG-001
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nostradamus_research.cli import app

if __name__ == "__main__":
    app(["review", "export", *sys.argv[1:]])
