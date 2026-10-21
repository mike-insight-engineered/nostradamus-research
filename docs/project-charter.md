# Project charter — Nostradamus Historical Translation Calibration

**Status:** draft for project-lead review (CAL-01) · **Milestone:** M1 · **Date:** 2026-10-21

## Purpose

To determine, with auditable evidence, whether AI translation pipelines can reliably translate
sixteenth-century French and Renaissance Latin into modern French and English, as the necessary
foundation for later historically rigorous translation and interpretation of the quatrains of Michel
de Nostredame.

## Why calibration comes first

The quatrains are short, elliptical, mix languages and are surrounded by centuries of speculative
interpretation. If the translation layer is unreliable, every later interpretive claim inherits
errors that cannot be separated from deliberate ambiguity. Milestone 1 therefore measures
translation quality on *comparable but non-Nostradamus* texts where independent expert references
can be obtained.

## Quality dimensions

- **QC1 — transcription fidelity**: does the digital text match the printed witness?
- **QC2 — translation fidelity**: does the translation render the historical language correctly,
  including period senses, grammar and genuine ambiguity?
- **QC3 — interpretive evidential strength**: how well is a proposed interpretation supported? (M1
  builds the data model; it does not assess interpretations.)

## In scope (M1)

Source registry and provenance policy; canonical passage model; 20-passage pilot, then 80-passage
corpus; pipelines A–D; MQM-style human review; automated metrics; confidence calibration; milestone gate.

## Out of scope (M1)

Translating or interpreting Nostradamus; claims about encoding, anagrams or prophecy; fine-tuning
models; paid infrastructure; GPU requirements.

## Principles

1. Evidence before claims; no fabricated data of any kind.
2. Software flags; people conclude.
3. Separate transcription, translation and interpretation.
4. Report uncertainty honestly; small samples give wide intervals.
5. Reproducibility: every run is recorded with its configuration, prompts, data hash and model.
6. Minimal cost: everything runs offline except explicitly authorised benchmark runs.

## Roles

| Role | Responsibility |
|---|---|
| Project lead | Scope, authorisation of paid runs, gate decisions |
| Source verifier(s) | Locating and authenticating witnesses (QC1) |
| Transcriber + independent checker | Diplomatic transcriptions |
| Expert translators | Independent reference translations |
| Expert reviewers (≥2) | Blinded MQM review |
| Research engineer | Software, runs, reports |

## Success criteria for M1

See [milestone-1-execution-plan.md](milestone-1-execution-plan.md) §5 and the gate criteria in
`reports/milestone-1-readiness.md`.
