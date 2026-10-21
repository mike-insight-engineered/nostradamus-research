---
name: audit-provenance
description: Full research-integrity audit - source registry statuses and evidence, passage provenance, rights, leakage, manifests, test-access ledger and backlog honesty - producing a written report. Use before milestone gates or when data changes.
---

# Provenance audit

Run, collecting outputs:

```bash
uv run nr sources validate
uv run nr sources audit --output reports/source-audit.md
uv run nr passages validate
uv run nr corpus provenance
uv run nr corpus leakage
uv run python scripts/validate_repository.py
uv run nr report milestone --output reports/milestone-1-readiness.md
```

Then review manually:
- every `experiments/runs/*/manifest.json` with `test_split_accessed: true` has a ledger entry
  and reason in `experiments/runs/test_access_ledger.jsonl`;
- no reference translation was produced by an evaluated model;
- `docs/project/backlog.yaml` statuses match the evidence (software vs research).

Write findings (severity, record IDs, recommended human action) to the user. Do not edit data.
