#!/usr/bin/env python
"""Select the 20-passage feasibility (pilot) set and write a pilot manifest.

Only eligible passages (verified to the inclusion status, with FR and EN
references) are selected. Shortfalls are reported, never filled.

Usage:
    uv run python scripts/build_pilot_manifest.py [--passages PATH] [--seed N] [--output PATH] [--dry-run]
    uv run python scripts/build_pilot_manifest.py --passages data/fixtures/synthetic_passages.jsonl --allow-synthetic --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nostradamus_research.config import load_config  # noqa: E402
from nostradamus_research.corpus.io import dataset_version, load_passages  # noqa: E402
from nostradamus_research.corpus.pilot import select_pilot  # noqa: E402
from nostradamus_research.utils.jsonl import write_json  # noqa: E402
from nostradamus_research.utils.runtime import utc_now  # noqa: E402


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--passages", type=Path)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--allow-synthetic", action="store_true", help="for tests/demos only")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(ROOT)
    path = args.passages or cfg.path("passages")
    if not path.exists():
        shortfall = {str(k): v for k, v in cfg.corpus.targets.pilot.items()}
        print(f"No passages at {path}. Pilot shortfall: {shortfall} (nothing selected).")
        return 0
    loaded = load_passages(path)
    if loaded.errors:
        for e in loaded.errors[:20]:
            print(f"ERROR {e}")
        return 1
    seed = args.seed if args.seed is not None else cfg.corpus.splits.seed
    sel = select_pilot(loaded.records, cfg.corpus, seed=seed, allow_synthetic=args.allow_synthetic)
    manifest = {
        "created_at": utc_now().isoformat(),
        "dataset_path": str(path),
        "dataset_sha256": dataset_version(loaded.records),
        "targets": {str(k): v for k, v in cfg.corpus.targets.pilot.items()},
        **sel.to_dict(),
    }
    print(json.dumps({k: manifest[k] for k in ("selected", "shortfall", "complete")}, indent=2))
    if args.dry_run:
        print("Dry run: nothing written.")
        return 0
    out = args.output or cfg.path("splits_dir") / "pilot-manifest.json"
    write_json(out, manifest)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
