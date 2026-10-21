# experiments/runs

Each run writes `<run_id>/results.jsonl` (one `TranslationResult` per passage) and
`<run_id>/manifest.json` (an `ExperimentManifest`: code, environment, config, prompt, data and model
fingerprints; held-out access; tokens and cost).

`test_access_ledger.jsonl` is append-only. Every run that touched held-out test passages adds an
entry (run, time, pipeline, model, passage IDs, reason, dataset hash). Never edit or truncate it.

`demo/` (git-ignored) holds the synthetic offline demonstration (`uv run nr demo`).
