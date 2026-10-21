# Data dictionary

Authoritative definitions are the Pydantic models in `src/nostradamus_research/models/` and the
generated JSON Schemas in `schemas/`. This page summarises them.

## Identifiers

| Prefix | Record | Example |
|---|---|---|
| `SRC-` | Witness (specific edition/exemplar) | `SRC-RABELAIS-PANTAGRUEL-1532` |
| `RES-` | Repository, corpus or reference work | `RES-GALLICA` |
| `PSG-` | Passage | `PSG-FP-0001` |
| `REF-` | Reference translation | `REF-FP-0001-EN-1` |
| `LEX-` | Lexical evidence entry | `LEX-HUGUET-0001` |
| `SYN-` | **Synthetic fixture** (any type) | `SYN-PSG-FP-001` |
| `RI-` | Blinded review item | `RI-0a1b2c3d4e` |

`SYN-` is required if and only if `data_origin = synthetic_fixture` (validated).

## HistoricalSource (`data/sources/source_registry.jsonl`)

| Field | Meaning |
|---|---|
| `source_id`, `record_type` | ID; `witness`, `digital_repository`, `reference_work`, `text_corpus` |
| `title`, `author`, `work_id`, `date_text`, `date_earliest/latest` | Bibliographic identity; `date_text` as stated |
| `edition`, `printer_publisher`, `place_of_publication` | Imprint |
| `holding_institution`, `catalogue_identifier` | Exemplar location and shelfmark/catalogue number |
| `stable_url`, `persistent_identifier`, `locator` | URL/ARK/IIIF; exact page/folio/image |
| `scan_available`, `transcription_available` | Known availability (null = unknown) |
| `rights_status`, `licence`, `rights_notes` | `unknown`, `public_domain`, `open_licence`, `permission_granted`, `restricted`, `not_permitted` |
| `verification_status` | `candidate`, `located`, `provenance_checked`, `transcription_verified`, `expert_reviewed`, `rejected` |
| `verification_evidence[]` | `evidence_type`, `supports_status`, `description`, `verified_by`, `verified_on`, `reference` |
| `status_history[]` | Transitions with who/when/why |
| `date_accessed`, `authenticity_notes`, `uncertainty_notes`, `outstanding_work[]`, `notes` | |

## Passage (`data/processed/passages.jsonl`)

| Group | Fields |
|---|---|
| Identity | `passage_id`, `source_id`, `data_origin`, `author_id`, `author`, `work_id`, `witness_id` |
| Classification | `language` (`frm`, `lat`, `oci`, `mixed`, `other`), `secondary_languages`, `genre` (`prose`, `verse`), `category` (`french_prose`, `french_poetry`, `latin_prose`, `latin_verse`, `mixed`; must match language+genre), `pilot_group` (override), `difficulty_flags`, dates |
| QC1 | `diplomatic_transcription` (exact), `diplomatic_sha256` (lock), `transcription_format`, `transcribed_by`, `typography_notes`, `spelling_notes`, `normalised_reading` + `normalisation_rules` + `normalised_by`, `locator`, `facsimile_reference`, `textual_variants[]` |
| QC2 | `difficult_words[]`, `linguistic_annotations[]`, `lexical_evidence_ids[]`, `reference_translations[]`, `ambiguities[]` |
| Claims | `historical_assertions[]` (verified/disputed, with evidence) vs `proposed_interpretations[]` (QC3, `evidence_strength`) |
| Workflow | `verification_status`, `split` (`unassigned`, `development`, `validation`, `test`), `review_history[]`, `notes` |

## ReferenceTranslation (embedded in passages)

`reference_id`, `passage_id`, `target_language` (`fr` modern French, `en`), `text`, `translator`,
`translator_type` (`human_expert`, `published_edition`, `human_non_expert`, `machine`,
`synthetic_fixture`), `reviewer`, `source_citation` (required for published editions),
`rights_status`, `licence`, `independent_of_evaluated_models` (machine references can never be
independent), `is_literal`, `notes`.

## LexicalEvidence (`data/annotations/lexical_evidence.jsonl`)

`evidence_id`, `kind` (`dictionary_entry`, `period_usage`, `grammar_reference`, `literary_example`),
`headword`, `variant_forms`, `language`, `sense`, `citation`, `source_id`, `locator`, `quotation`,
`url`, `rights_status`, `verification_status`, `verified_by`, `verified_on`. Verified entries need a
named verifier. **The store is empty until people add checked entries.**

## TranslationResult (`experiments/runs/<id>/results.jsonl`)

IDs (`result_id`, `run_id`, `passage_id`), `pipeline`, `provider`, `model`, `is_mock`, `data_origin`,
`source_text_sha256`, `translation_fr`, `translation_en`, `intermediate_fr` (B), `analysis` (B/C/D),
`retrieved_evidence_ids`, `retrieval_status`, `alternatives[]`, `unresolved_ambiguities[]`,
`stated_confidence` + `confidence_source` (`model_stated`, `mock_deterministic`, `none`; null iff
none), `limitations[]`, `guardrail_flags[]`, `parse_errors[]`, `error`, `prompt_versions`, `calls[]`
(per-call metadata: template id/version/hash, params, timing, attempts, token usage, cost), `created_at`.

## HumanReview (`data/annotations/reviews/<package>.jsonl`, linked form)

`review_id`, `review_item_id`, `package_id`, `reviewer_id`, `reviewer_provenance` (`expert`,
`non_expert`, `synthetic_fixture`), `reviewed_on`, `judgement_fr/en` (`acceptable`, `unacceptable`,
`unresolvable`), `errors[]` (MQM: `category`, `severity`, `target_language`, `span`, `note`,
`evidence`), `alternative_readings`, `ambiguity_flag`, `unresolvable`, `reviewer_confidence` (1–5),
`supporting_references`, `comments`, `time_spent_minutes`. Linked files add `result_id`, `run_id`,
`passage_id` and `pipeline` from the package key.

## EvaluationResult and ExperimentManifest

See `schemas/evaluation_result.schema.json` and `schemas/experiment_manifest.schema.json`. Every
evaluation carries an `evidence_level` (`synthetic_fixture`, `automated_only`, `human_non_expert`,
`expert_reviewed`).
