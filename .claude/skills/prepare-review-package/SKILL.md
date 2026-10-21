---
name: prepare-review-package
description: Export a blinded human-review package from recorded translation runs, then validate and import completed reviews and compute agreement. Use for CAL-10 and CAL-13 review rounds.
---

# Blinded review round

1. Confirm the runs to include (`experiments/runs/<id>/manifest.json`). Check `evidence_level` and
   whether the test split was accessed (and why).
2. Export:
   `uv run nr review export --run <RUN1> --run <RUN2> ... --package-id PKG-YYYY-NNN`
   This writes `data/annotations/review_packages/PKG-.../` (send to reviewers) and `PKG-...-KEY/`
   (keep private; git-ignored).
3. Send reviewers the package folder and `docs/human-review-guidelines.md`. Never send the key.
4. On return, validate first:
   `uv run nr review import <completed.csv> --key <KEY>/key.json --dry-run`
   Fix problems with the reviewer, not by editing their judgements.
5. Import: the same command without `--dry-run` writes `data/annotations/reviews/PKG-....jsonl`.
6. Agreement: `uv run nr review agreement data/annotations/reviews/PKG-....jsonl`. Report n and
   caveats.
7. Never fill in, alter or simulate judgements on real data.
