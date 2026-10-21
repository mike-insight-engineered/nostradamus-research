# Calibration methodology: sampling, partitioning, contamination

## Sampling

- Targets (`config/corpus.yaml`): pilot 5 French prose / 5 French poetry / 5 Latin / 5 mixed or
  difficult; full corpus 30 / 20 / 15 / 5 / 10.
- **Eligibility:** passage status ≥ `transcription_verified` and ≥1 independent reference in each of
  French and English (`corpus/stats.py:is_eligible`). Shortfalls are reported, never filled with
  ineligible or synthetic passages.
- **Diversity:** pilot selection (`scripts/build_pilot_manifest.py`) round-robins across works within
  each group in a seeded order, so no single work dominates.
- **Passage length:** about 40–120 words, or one sonnet or stanza group for verse. Record the
  selection rationale in `notes`.
- **Difficulty:** the mixed/difficult group deliberately includes code-switching, dense
  abbreviation, Latinate syntax and allusion. Use `difficulty_flags` and `pilot_group` overrides.

## Partitioning

`corpus/splitting.py`:

1. Group passages by `work_id` (default) or by author (`--group-by author`, stricter).
2. Shuffle groups with the configured seed, then place larger groups first.
3. Assign each group to the split with the largest proportional deficit, with a mild penalty for
   over-representing the group's category. Whole groups only.
4. Targets 48/12/20 are scaled proportionally for other corpus sizes (largest-remainder rounding).
   Group isolation takes priority over exact sizes, and deviations are reported as warnings.
5. **Test lock:** a group containing any passage already assigned to `test` stays in `test`.
   Re-splitting can never move frozen held-out passages into development.

The plan (seed, targets, achieved counts, category counts, group assignments, dataset hash, plan
hash) is written to `data/splits/`. `--apply` writes split fields back into the corpus.

## Leakage and contamination checks (`corpus/leakage.py`)

| Check | Severity |
|---|---|
| Exact duplicate text (after typographic folding) | error |
| Near-duplicate (character 5-gram Jaccard ≥ 0.8) across splits | error (warning within a split) |
| Same work across splits | error |
| Same author across splits | warning (error when grouping by author) |
| Same witness across splits | warning |
| Held-out reference near-duplicating a non-test reference | error |
| Retrieval evidence (quotation/sense) contained in held-out text or references | error |

**Pretraining contamination**, meaning a model having seen these texts or published translations
during training, cannot be detected or eliminated here. Mitigations: prefer less-reproduced passages;
record whether a published translation exists (`source_citation`); compare performance on passages
with and without widely available translations; report this as a limitation.

## Protecting the held-out set

- `select_passages` excludes test passages unless `--allow-test-split` is passed with a reason.
- Each such run appends to `experiments/runs/test_access_ledger.jsonl` and is marked in its manifest.
- Abstention thresholds cannot be selected on test items (`calibration/abstention.py`).
- Prompt templates, retrieval material and model choices are frozen (version-pinned) before the
  pre-registered test run. Repeated test runs are visible in the ledger and must be justified in
  `docs/decisions/`.
