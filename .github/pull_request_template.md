## Summary

<!-- What changes and why. Link backlog items (CAL-xx) and issues. -->

## Type of change

- [ ] Software (code, config, tests, CI)
- [ ] Research data (sources, passages, references, evidence, reviews)
- [ ] Documentation / protocol

## Verification

- [ ] `uv run ruff check . && uv run ruff format --check .`
- [ ] `uv run mypy`
- [ ] `uv run pytest` (offline)
- [ ] `uv run python scripts/validate_repository.py`
- [ ] Schemas regenerated if models changed (`nr schemas generate`)
- [ ] Prompt template version bumped and pinned if a template changed

## Research integrity

- [ ] No fabricated transcriptions, citations, reference translations or review scores
- [ ] No status promoted without recorded evidence from a named person
- [ ] Diplomatic transcriptions unchanged, or corrections documented with new hash + review event
- [ ] Synthetic data confined to fixtures/tests and labelled `SYN-` / `SYNTHETIC`
- [ ] Held-out test passages not used for prompt tuning, retrieval material or selection
- [ ] No paid API calls without explicit authorisation; no credentials committed
- [ ] Rights confirmed for any committed source/translation text
- [ ] Translation outputs contain no interpretive (QC3) content
- [ ] Backlog statuses reflect actual evidence (software vs research tracked separately)
