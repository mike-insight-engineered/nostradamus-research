# Reproducibility

## What every run records (`experiments/runs/<run_id>/manifest.json`)

| Aspect | Field(s) |
|---|---|
| Code | `git_commit`, `git_dirty`, `package_version` |
| Environment | `python_version`, `dependency_lock_sha256` (hash of `uv.lock`) |
| Configuration | `config_sha256` (project, corpus, translation, evaluation YAML) |
| Prompts | `prompt_templates[]` (ID, version, SHA-256 of the template file); each call also stores the rendered-prompt hash |
| Data | `dataset_path`, `dataset_sha256` (content hash, independent of file order), `passage_ids`, `splits_included`, `data_origin_counts` |
| Retrieval | `retrieval_store_sha256` |
| Model | `provider`, `model` (as returned by the API where available), `provider_params` (temperature, max_tokens, top_k) |
| Held-out access | `test_split_accessed`, `test_access_reason` (+ ledger entry) |
| Outcome | `status`, `n_results`, `n_failed`, tokens, cost (if pricing configured), `runtime_seconds` |

## Reproducing a run

1. `git checkout <git_commit>` and confirm `git_dirty` was false (otherwise the run is not exactly reproducible).
2. `uv sync --locked --extra providers` and check `sha256(uv.lock)` against the manifest.
3. Check the config hashes: `sha256sum config/*.yaml`.
4. Check the dataset: `uv run python -c "from nostradamus_research.corpus.io import *; from pathlib import Path; print(dataset_version(load_passages(Path('<dataset_path>')).records))"`.
5. Re-run with the same pipeline, provider, model and passage selection.
6. Mock runs reproduce exactly. Commercial models may not, even at temperature 0: providers change
   model snapshots and sampling is not guaranteed deterministic. Record pinned, dated model IDs where
   the provider offers them, and compare outputs rather than expecting identity.

## Determinism in this codebase

- Splits: seeded (`corpus.yaml: splits.seed`), group order fixed, and independent of input order.
- Review packages: seeded shuffle and item IDs (`evaluation.yaml: review.blinding_seed`).
- Bootstrap: fixed seed (`statistics.seed`).
- Mock provider: output is a pure function of request metadata and seed.

## Archiving

Commit run directories that form part of the research record (`git add -f experiments/runs/<id>`),
together with the review files under `data/annotations/reviews/`. Do not commit unblinding keys until
review is complete.
