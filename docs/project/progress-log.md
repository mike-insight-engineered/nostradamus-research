# Progress log

Newest first. Record what was done, what evidence supports it, and what remains. Record paid-API
use with estimated and actual cost.

## 2026-10-21 — Initial implementation of the Milestone 1 software foundation

**Done (software, ready for review):**
- Packaging (`pyproject.toml`, `uv.lock`, Python 3.12), CI workflow, Makefile, issue/PR templates,
  Claude Code agents and skills.
- Data model (Pydantic v2) with integrity validators; 8 JSON Schemas generated.
- Source registry with a status ladder and one-rung promotion; provenance audit.
- Corpus I/O, dataset hashing, stats vs targets, grouped seeded splitting with test lock, leakage
  checks, pilot selection.
- Transcription safeguards (hash lock, recorded normalisation, TEI export/import), passage importer.
- Linguistic heuristics and local evidence retrieval (abstains without verified evidence).
- Provider layer (mock, Anthropic, OpenAI) with retry, rate limiting, redaction, cost metadata and a
  triple paid-call guard.
- Pipelines A–D with five versioned prompt templates (v1.0.0), guardrails and an experiment runner
  that writes manifests and the test-access ledger.
- Evaluation (MQM taxonomy, chrF/chrF++, optional COMET, bootstrap/Wilson, blinded review packages,
  import, agreement, staging comparison) and calibration (reliability, ECE, Brier, coverage–risk,
  abstention).
- Reports: source audit, benchmark, calibration, milestone gate; templates in `reports/templates/`.
- Typer CLI `nr`; scripts; offline demo on 12 synthetic passages.
- Tests: offline unit and integration suite.

**Done (research, partial):**
- 26 candidate source records (CAL-02 in progress). None verified.

**Not done / next:**
- CAL-05–08: locate and authenticate witnesses; select and transcribe 20 passages.
- CAL-09: independent reference translations.
- Confirm licensing for BVH, Gallica, Frantext, Perseus and Huguet.
- Project-lead review of protocols (CAL-01, 03, 04) and confirmation of ADRs 0001–0004.

**Known limitations of the implementation:** see `research/open-issues.md`.
