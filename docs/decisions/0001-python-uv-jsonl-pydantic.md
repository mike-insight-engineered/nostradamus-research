# ADR 0001 — Python 3.12, uv, src layout; JSONL + Pydantic as the canonical store

**Status:** Accepted (implementation), awaiting lead confirmation · **Date:** 2026-10-21

## Context
The corpus is small (≤ 80 passages, tens of sources) but must be auditable line by line, reviewable
in pull requests, and validated strictly. The team needs minimal infrastructure and cost.

## Decision
- Python ≥ 3.12, `uv` with a committed `uv.lock`, `src/` layout, Typer CLI.
- Canonical records are JSONL files in Git, validated by Pydantic v2 models with `extra="forbid"`.
  JSON Schemas are generated from the models and checked for drift in CI.
- CSV is used only for human exchange (review sheets, candidate lists). TEI is supported for
  transcriptions.
- No database, vector store, Docker or cloud service is required.

## Consequences
+ Every change to research data is a reviewable diff, and validation errors point to file:line:field.
+ Zero infrastructure cost.
− Concurrent editing of the same JSONL file needs care (one PR at a time per file).
− If the corpus grows by orders of magnitude, a database may be warranted (not expected in M1/M2).
