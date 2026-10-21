# data/candidates — pilot candidate manifest (CAL-05 to CAL-08)

`pilot_candidates.jsonl` (canonical) and `pilot_candidates.csv` (review view) list the **20 pilot slots**:
5 French prose (FP), 5 French poetry (FV), 5 Latin (LA) and 5 mixed or difficult (MX). Each slot references a
registered witness (`source_id`) and records its locator, passage extent, expected linguistic challenges,
transcription status, blockers and same-work overlaps.

These are **candidates**. A slot becomes a calibration passage only after:
1. its witness reaches `provenance_checked` (catalogue evidence by a named person);
2. a human transcription is verified by an independent checker (`docs/transcription-verification-protocol.md`);
3. independent FR and EN references are obtained (`research/pilot/reference-translation-queue.md`);
4. it is imported into `data/processed/passages.jsonl` with `nr passages import`.

Fields: `slot_id`, `pilot_group`, `source_id`, `locator`, `page_level_locator` (true when a specific page or
signature has been identified), `passage`, `linguistic_challenges` (entries prefixed "EXPECTED" were not yet
observed in the passage), `selection_rationale`, `facsimile` (image actually viewed, if any),
`transcription_status` (`pending` | `draft_ai_unverified`), `draft_passage_id`, `reference_translation_status`,
`human_verification_status`, `blockers`, `same_work_as`, `candidate_status`.

Integrity is checked by `tests/unit/test_research_artifacts.py`: every `source_id` must be registered, every draft
must exist and validate, and no slot may claim human verification.
