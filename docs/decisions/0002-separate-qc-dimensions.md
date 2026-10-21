# ADR 0002 — Separate transcription (QC1), translation (QC2) and interpretation (QC3)

**Status:** Accepted (implementation), awaiting lead confirmation · **Date:** 2026-10-21

## Context
Errors at each layer look alike downstream: a misread letter, a wrong period sense and a speculative
reading can all yield "the text means X". Conflating them makes calibration meaningless.

## Decision
- Passages hold a locked diplomatic transcription (QC1) separately from any normalised reading.
- Translation outputs (QC2) contain translations, alternatives and ambiguities only. Guardrails flag
  interpretive drift, and reviewers treat it as a critical error.
- Interpretations (QC3) live only in `Passage.proposed_interpretations`, each with an
  `evidence_strength`, and separate from `historical_assertions`, which require evidence.
- The MQM taxonomy has a `transcription` category so that QC1 problems are not scored as QC2 failures.

## Consequences
+ Clean measurement of translation fidelity; Milestone 2 can add QC3 without touching QC2 data.
− Some useful context (e.g. known allusions) must be recorded as annotations rather than baked into translations.
