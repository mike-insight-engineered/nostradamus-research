# ADR 0003 — Encode research-integrity rules as validators and guards

**Status:** Accepted (implementation), awaiting lead confirmation · **Date:** 2026-10-21

## Context
Conventions written only in documentation are easily broken, especially by automated assistants
working quickly. The most damaging failures (fabricated verification, synthetic data in the corpus,
silent transcription edits, test-set tuning, unplanned spend) can be detected mechanically.

## Decision
Enforce in code:
- verification status ↔ evidence (`models/status_policy.py`), with one-rung promotion;
- `SYN-` prefix ↔ `synthetic_fixture` origin for every record type, and synthetic reviewer IDs;
- diplomatic transcription hash lock;
- machine references never "independent";
- held-out access needs a flag and a reason, plus a ledger entry; abstention thresholds cannot be tuned on test;
- paid provider construction needs config + CLI flag + environment key;
- evidence banners in every report;
- a repository validator (CI) that also scans for secrets and synthetic records in research files.

## Consequences
+ Integrity failures become test failures or validation errors, not silent drift.
− Some legitimate edge cases need an explicit, documented workflow (e.g. transcription corrections).
