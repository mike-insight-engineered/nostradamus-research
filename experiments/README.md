# Experiments

| Directory | Pipeline | Notes |
|---|---|---|
| `baseline/` | A — direct | Baseline without retrieval |
| `two_stage/` | B — two-stage via modern French | Measures staging loss |
| `rag/` | C — retrieval-augmented | Requires verified lexical evidence |
| `linguistic_analysis/` | D — structured analysis | Heuristic pre-analysis + retrieval |
| `runs/` | Run outputs: `<run_id>/results.jsonl` + `manifest.json`; `test_access_ledger.jsonl` | |

Each experiment directory holds an `experiment.yaml` describing intended runs (provider, model,
splits, prompt versions) and notes. Configuration that affects runs lives in `config/`. The
experiment files document intent and must agree with the manifests that runs produce.

## Workflow

1. Dry run: `uv run nr translate run --pipeline A --provider <p> --split development --dry-run`
2. Run (paid providers need authorisation and `--allow-paid-api`).
3. Review the manifest. Commit the run directory if it belongs to the research record
   (`git add -f experiments/runs/<run_id>`).
4. Export a blinded review package across the runs being compared.

No real (non-mock) experiments have been run.
