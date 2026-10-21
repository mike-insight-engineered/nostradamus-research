#!/usr/bin/env python
"""Run every enabled pipeline (A–D) with one provider over the research corpus.

SAFE BY DEFAULT: without --execute this is a dry run (no provider calls, no
writes). A paid provider additionally requires --allow-paid-api, an enabled
entry in config/providers.yaml and the API key in the environment.

Usage:
    uv run python scripts/run_benchmark.py --provider mock --split development            # dry run
    uv run python scripts/run_benchmark.py --provider mock --split development --execute
    uv run python scripts/run_benchmark.py --provider anthropic --split development --execute --allow-paid-api
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nostradamus_research.cli import app
from nostradamus_research.config import load_config


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--provider", required=True)
    ap.add_argument("--split", action="append", default=[])
    ap.add_argument("--passages", type=Path)
    ap.add_argument("--execute", action="store_true", help="actually run (otherwise dry run)")
    ap.add_argument("--allow-paid-api", action="store_true")
    ap.add_argument("--description")
    args = ap.parse_args(argv)

    cfg = load_config()
    status = 0
    for key, toggle in cfg.translation.pipelines.items():
        if not toggle.enabled:
            print(f"skip {key} (disabled)")
            continue
        cmd = ["translate", "run", "--pipeline", key, "--provider", args.provider]
        for s in args.split:
            cmd += ["--split", s]
        if args.passages:
            cmd += ["--passages", str(args.passages)]
        if args.description:
            cmd += ["--description", args.description]
        if args.allow_paid_api:
            cmd.append("--allow-paid-api")
        if not args.execute:
            cmd.append("--dry-run")
        print(f"== {key} ==")
        try:
            app(cmd, standalone_mode=False)
        except SystemExit as exc:  # typer.Exit
            status = status or int(exc.code or 0)
        except Exception as exc:
            print(f"ERROR {key}: {exc}")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
