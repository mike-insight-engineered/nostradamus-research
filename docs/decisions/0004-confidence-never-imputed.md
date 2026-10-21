# ADR 0004 — Use model-stated confidence only; never impute it

**Status:** Accepted (implementation), awaiting lead confirmation · **Date:** 2026-10-21

## Context
Calibration needs a confidence signal. Providers differ: some expose token log-probabilities, some do
not, and none returns a probability that a *translation* is correct.

## Decision
- Prompts invite an optional `self_reported_confidence` in [0, 1], and allow null.
- Values that are missing, out of range or of the wrong type become null with `confidence_source:
  none`. A validator forbids any value without a source.
- Reports call this *stated confidence* and compare it with the *empirical correctness rate*. They
  never call it a probability.
- Calibration claims require a configured minimum sample (default 50 usable items).

## Consequences
+ No manufactured numbers; calibration measures what models actually say about themselves.
− Models that decline to state confidence contribute no calibration data (reported as counts).
− Log-probability-based confidence could be explored later as a separate, clearly labelled signal.
