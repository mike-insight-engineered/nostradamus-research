# data/splits

- `split-seed<SEED>-<group_by>.json`: partition plans from `nr corpus split` (seed, targets,
  achieved counts, category counts, group assignments, dataset and plan hashes, warnings).
- `pilot-manifest.json`: the 20-passage pilot selection from `scripts/build_pilot_manifest.py`.

Once a test set has been used for a run, its passages are **frozen**: the splitter keeps any group
containing a test passage in `test`. Never edit plans by hand. Regenerate them and commit them with
an explanation in the progress log.
