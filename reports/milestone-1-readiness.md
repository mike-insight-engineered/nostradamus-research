# Milestone Gate Report — M1 — Historical Translation Calibration Pilot

> **This gate report reflects repository state only.** It contains no translation-quality results. Synthetic fixtures and mock runs are excluded from every research criterion.

- Generated: 2026-10-21T02:22:58+00:00
- Git commit: `669bae6c44f5e5bd20ef5a3811f6c5b23341b6ce`

## 1. Required deliverables

- Repository structure, configuration, CI and documentation
- Source registry with provenance/licensing tracking and status policy
- Canonical passage model and generated JSON Schemas
- Translation pipelines A–D with versioned prompts and provider adapters (mock, Anthropic, OpenAI)
- Evaluation framework (MQM taxonomy, chrF, blinded review, agreement)
- Confidence calibration module and reports
- 20 verified pilot passages with independent references (research — see R2/R3)
- Blinded expert review and calibration of the pilot (research — see R7/R8)

## 2. Acceptance criteria

`PASSED` = evaluated and met; `FAILED` = evaluated and not yet met; `NOT EVALUATED` = cannot be
assessed from the current repository state.

| ID | Area | Criterion | Status | Detail |
|---|---|---|---|---|
| S1 | software | Configuration files load and validate | PASSED | config/*.yaml valid |
| S2 | software | Source registry validates against the schema | PASSED | 50 records, 0 errors |
| S3 | software | Pipelines A–D and pinned prompt templates load | PASSED | 4 pipelines; 5 templates |
| S4 | software | JSON Schemas match the Pydantic models | PASSED | compared generated vs committed |
| S5 | software | Automated test suite passes | NOT EVALUATED | evaluated by CI / `make test`, not by this report |
| R1 | research | Witnesses with checked provenance are registered | FAILED | 0 of 32 witness records at provenance_checked or above |
| R2 | research | 20-passage pilot meets category quotas with verified transcriptions | FAILED | eligible passages — french_prose: 0/5; french_poetry: 0/5; latin: 0/5; mixed_or_difficult: 0/5 |
| R3 | research | Independent FR and EN references with cleared rights | NOT EVALUATED | 0 of 0 eligible passages |
| R4 | research | Provenance audit has no errors | NOT EVALUATED | 0 errors, 26 warnings over 0 passages |
| R5 | research | Partitions are leakage-free | NOT EVALUATED | no passages assigned to splits |
| R6 | research | All four pipelines benchmarked on real passages with a real provider | NOT EVALUATED | pipelines with non-synthetic, non-mock runs: none |
| R7 | research | Blinded expert review of pilot outputs completed | NOT EVALUATED | 0 imported review records in data/annotations/reviews/ |
| R8 | research | Calibration analysis on expert labels with sufficient sample | NOT EVALUATED | requires R6 and R7 |
| S6 | software | Backlog file validates and is consistent with corpus state | PASSED | 14 items |

## 3. Backlog status

Software and research workstreams are tracked separately (`docs/project/backlog.yaml`).

| ID | Title | Overall | Software | Research |
|---|---|---|---|---|
| CAL-01 | Create repository research protocol and project configuration | Ready for review | Ready for review | Ready for review |
| CAL-02 | Establish historical source and licensing registers | In progress | Ready for review | In progress |
| CAL-03 | Define sampling and dataset partition methodology | Ready for review | Ready for review | Ready for review |
| CAL-04 | Establish translation review and evaluation rubric | Ready for review | Ready for review | Ready for review |
| CAL-05 | Acquire five verified French prose passages | In progress | n/a | In progress |
| CAL-06 | Acquire five verified French poetry passages | In progress | n/a | In progress |
| CAL-07 | Acquire five verified Renaissance Latin passages | In progress | n/a | In progress |
| CAL-08 | Acquire five verified multilingual or difficult passages | In progress | n/a | In progress |
| CAL-09 | Obtain independent reference translations | In progress | n/a | In progress |
| CAL-10 | Complete review of the initial 20-passage feasibility dataset | Not started | n/a | Not started |
| CAL-11 | Expand the corpus to 80 verified passages | Not started | n/a | Not started |
| CAL-12 | Benchmark four translation pipelines | Blocked | Ready for review | Blocked |
| CAL-13 | Conduct independent error analysis and confidence calibration | Blocked | Ready for review | Blocked |
| CAL-14 | Produce the milestone completion report and go/no-go decision | Blocked | Ready for review | Blocked |

## 4. Outstanding blockers

- R1: Witnesses with checked provenance are registered — 0 of 32 witness records at provenance_checked or above
- R2: 20-passage pilot meets category quotas with verified transcriptions — eligible passages — french_prose: 0/5; french_poetry: 0/5; latin: 0/5; mixed_or_difficult: 0/5
- R3: Independent FR and EN references with cleared rights — 0 of 0 eligible passages
- R4: Provenance audit has no errors — 0 errors, 26 warnings over 0 passages
- R5: Partitions are leakage-free — no passages assigned to splits
- R6: All four pipelines benchmarked on real passages with a real provider — pipelines with non-synthetic, non-mock runs: none
- R7: Blinded expert review of pilot outputs completed — 0 imported review records in data/annotations/reviews/
- R8: Calibration analysis on expert labels with sufficient sample — requires R6 and R7

## 5. Recommendation

**DEFER**

The software foundation is ready for review, but no verified historical passages, independent reference translations or expert reviews exist yet. The go/no-go decision on AI translation reliability is deferred until CAL-05 to CAL-10 are complete.

---
*Decision record (completed by the project lead, not by software):*

| Decision | Decided by | Date | Rationale reference |
|---|---|---|---|
| | | | |
