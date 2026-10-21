# CLAUDE.md — project instructions for Claude Code and contributors

This repository is a **research** codebase. Software correctness matters, but research integrity
matters more. When the two conflict, stop and ask.

## Research integrity rules (mandatory)

1. **Never fabricate** source transcriptions, dictionary entries or citations, scholarly or reference
   translations, human review scores, or verification evidence.
2. **Never mark a source, passage or evidence entry verified** without evidence that a named person
   recorded (`verification_evidence`, `review_history`, `verified_by`). The Pydantic validators
   enforce this. Never weaken them to make data load.
3. **Synthetic data** is allowed only for tests and labelled demonstrations. It must use `SYN-` IDs,
   `data_origin: synthetic_fixture`, and `SYNTHETIC` reviewer IDs. It must never enter
   `data/sources/source_registry.jsonl`, `data/processed/` or `data/annotations/lexical_evidence.jsonl`.
4. **Never present fixture or mock results as research findings.** Reports carry evidence banners. Keep them.
5. **Translation ≠ interpretation.** Pipelines translate (QC2). Prophetic or historical
   interpretation (QC3) goes only into `proposed_interpretations`, with an evidence-strength rating,
   and never into translation outputs or prompts. Do not conflate translation confidence with
   interpretive confidence.
6. **Held-out test set:** never use test passages or their references for prompt design, retrieval
   material, threshold selection or model selection. Test access needs `--allow-test-split` plus a
   reason, and is logged.
7. **No paid API calls** unless the user explicitly authorises them in this session. Never pass
   `--allow-paid-api` on your own initiative, and never enable providers in `config/providers.yaml`.
8. **Copyright:** do not commit scans, long extracts or modern translations unless rights are
   confirmed (`rights_status` in `public_domain`, `open_licence`, `permission_granted`). Licensing is split:
   software GPL-3.0-or-later; original docs and annotations CC BY 4.0; third-party material keeps its own terms
   (`DATA_LICENSE.md`). Write rights-pending files with `.pending-rights` in the name, so that they are git-ignored.
9. **Git:** do not commit, push, force-push, rewrite history or delete branches unless asked.
10. Scholarly claims always require human expert review. Software may *flag*; only people *conclude*.

## Rules for transcriptions

- `diplomatic_transcription` is exact: spelling, long s (ſ), u/v, i/j, abbreviations, tildes,
  punctuation and line breaks as printed. It is locked by `diplomatic_sha256`.
- Never modernise, normalise, "fix" or reflow it. A correction needs a new hash **and** a
  `review_history` event (`transcription_checked` or `comment`) explaining it. See
  `docs/transcription-policy.md`.
- Normalised readings are a separate editorial layer and must list `normalisation_rules`.

## Module organisation

```
src/nostradamus_research/
  models/          Pydantic models + enums; status_policy.py holds verification requirements
  provenance/      SourceRegistry (JSONL), promotion rules, corpus provenance audit
  corpus/          passage I/O and dataset hashing, stats, grouped splitting, leakage, pilot selection
  ingestion/       conservative passage import (dry-run, hash locking, TEI)
  transcription/   recorded normalisation with safeguards, integrity comparison, TEI export/import
  linguistics/     segmentation, heuristic language ID/morphology, local evidence retrieval
  translation/     prompts (versioned templates), parsing, guardrails, pipelines A–D, runner
    providers/     base (retry, rate limit, redaction, cost), mock, anthropic, openai, factory
  evaluation/      MQM taxonomy, chrF/COMET, statistics, review packages, agreement, aggregation
  calibration/     reliability/ECE/Brier/coverage, abstention, analysis
  reporting/       report renderers, backlog model, milestone gate
  cli.py           Typer CLI (`nr`); demo.py offline demonstration; schemas.py
```

## Conventions

- Python 3.12+, `uv`, `src/` layout, Pydantic v2 models with `extra="forbid"`.
- Records are JSONL. Schemas in `schemas/` are generated (`nr schemas generate`). Never hand-edit them.
- Prompt templates are versioned files. When you change one, bump its `version` and the pin in
  `config/translation.yaml`, then record the change in `docs/project/progress-log.md`.
- Configuration lives in `config/*.yaml`. Do not hard-code thresholds or model IDs.
- Every run must write a manifest. Do not bypass `translation/runner.py`.

## Testing requirements

- `uv run pytest` must pass offline with no API keys. Add tests for every behaviour change.
- `uv run ruff check . && uv run ruff format --check . && uv run mypy` must pass.
- `uv run python scripts/validate_repository.py` must pass (it also scans for secrets).
- Tests needing network, heavy optional dependencies or credentials are marked `external` and excluded by default.

## Data provenance expectations

Source statuses: `candidate → located → provenance_checked → transcription_verified → expert_reviewed`
(or `rejected`), one rung at a time via `nr sources promote`, with evidence. Locating a digitised
copy is **not** authentication of a printed witness. See `docs/source-authentication.md`.

## Specialised agents and skills

See `.claude/README.md`. Agents may draft and flag; they may not promote statuses beyond `located`,
make scholarly claims, or authorise spending.
