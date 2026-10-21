# Milestone 1 execution plan — Historical Translation Calibration Pilot

## 1. Phases

| Phase | Backlog | Output | Exit condition |
|---|---|---|---|
| 0. Foundation | CAL-01–04 | Software framework, protocols, registers, rubric | Project-lead review of protocols; CI green |
| 1. Source acquisition | CAL-02, CAL-05–08 | 20 passages from authenticated witnesses, diplomatic transcriptions checked | `nr corpus stats` shows 5/5/5/5 eligible (status ≥ transcription_verified) |
| 2. References | CAL-09 | ≥1 independent FR and EN reference per passage, rights cleared | `nr corpus provenance` has no errors |
| 3. Pilot evaluation | CAL-10, (CAL-12 on pilot) | Runs A–D on development/validation; blinded review of outputs | ≥2 reviewers per item; agreement reported |
| **Feasibility gate** | — | `nr report milestone` + lead decision | continue / remediate / defer |
| 4. Expansion | CAL-11 | 80 passages; splits frozen (48/12/20) | leakage-free; test set locked |
| 5. Benchmark | CAL-12 | Runs A–D on dev/val; **one** pre-registered run on test | manifests + ledger entry |
| 6. Analysis | CAL-13 | Error analysis; calibration report | expert-labelled, intervals reported |
| 7. Decision | CAL-14 | Milestone completion report; go/no-go | signed decision record |

## 2. Pilot design (20 passages)

5 French prose, 5 French poetry, 5 Latin (prose or verse), 5 mixed-language or otherwise difficult.
Draw from at least three works per group where possible, with passages of roughly 40–120 words. The
pilot tests the *workflow* and gives first error profiles. It is not powered to rank pipelines.

## 3. Pre-registration before touching the test set

Before any test-split run, record in `docs/decisions/`: the pipelines and prompt versions to be
tested, the provider/model IDs, the correctness rule (`config/evaluation.yaml`), the abstention
threshold (selected on validation only), and the primary comparisons. Then run once, with
`--allow-test-split --test-reason "pre-registered final evaluation (ADR-xxxx)"`.

## 4. Cost control

All development uses the mock provider. Paid runs need lead authorisation, an enabled local provider
config, and `--allow-paid-api`. Do a `--dry-run` first: it reports the number of calls. Record
estimated and actual cost in the progress log.

## 5. Acceptance criteria (M1)

- S1–S6: software criteria (config, registry, pipelines, schemas, tests, backlog consistency).
- R1: authenticated witnesses registered; R2: pilot quotas met with verified transcriptions;
  R3: independent, rights-cleared references; R4: provenance audit clean; R5: leakage-free
  partitions; R6: A–D benchmarked on real passages with a real provider; R7: blinded expert review
  complete; R8: calibration on expert labels with sufficient sample.

The gate report evaluates these automatically where possible (`nr report milestone`).

## 6. Current position (2026-10-21)

Phase 0 is implemented and ready for review. Phases 1–7 have not started. See
`reports/milestone-1-readiness.md` and [project/progress-log.md](project/progress-log.md).
