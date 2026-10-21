#!/usr/bin/env python
"""Generate a confidence calibration report (thin wrapper around `nr calibrate report`).

Usage:
    uv run python scripts/generate_calibration_report.py --run experiments/runs/<RUN_ID> \
        --reviews data/annotations/reviews/<PKG>.jsonl --output reports/calibration-<PKG>.md
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nostradamus_research.cli import app

if __name__ == "__main__":
    app(["calibrate", "report", *sys.argv[1:]])
