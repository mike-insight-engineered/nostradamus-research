# Blinded Translation Review — Package ${package_id}

Items in this package: ${n_items}. Data origin(s): ${data_origins}.

> If the data origin includes `synthetic_fixture`, this package is a **software demonstration**.
> Do not spend expert time on it.

## What you are reviewing

Each row shows a historical passage (diplomatic transcription, with provenance and a facsimile
reference where available) and one machine translation into modern French and modern English. You
do **not** know which system produced it, and must not try to find out. Full guidance:
`docs/human-review-guidelines.md`.

## Files

- `review_sheet.csv` — fill in the review columns (one row per item; duplicate a row if a second
  reviewer works in the same file).
- `items.jsonl` — the same items in machine-readable form (you may instead submit JSONL reviews).

## For every item

1. Read the source in the facsimile where possible. If the transcription itself looks wrong, record
   a `transcription` error (QC1) rather than penalising the translation.
2. Set `judgement_fr` and `judgement_en`: `acceptable`, `unacceptable` or `unresolvable`.
3. Record each error in `errors_json` as a JSON list, for example:
   `[{"category": "historical_lexical", "severity": "major", "target_language": "en", "span": "<words>", "note": "<what is wrong and why>", "evidence": ["<work, headword/page you actually consulted>"]}]`
   - Categories: mistranslation, historical_lexical, grammar, omission, unsupported_addition,
     language_identification, lost_ambiguity, invented_specificity, names_dates, transcription,
     fluency, other.
   - Severities: neutral, minor, major, critical.
4. Record legitimate alternative readings in `alternative_readings` (separate with `||`).
5. Set `ambiguity_flag` (true/false) if the source is genuinely ambiguous; `unresolvable` if it
   cannot be judged.
6. Record `reviewer_confidence` (1–5) and `supporting_references` (dictionaries, editions; separate
   with `||`). Cite only works you actually consulted.
7. Fill `reviewer_id`, `reviewer_provenance` (`expert` or `non_expert`) and `reviewed_on`
   (YYYY-MM-DD).

## Rules

- Judge fidelity to the historical language, not similarity to any modern translation you know.
- Do not reward or add interpretation (prophecy, later events): translation only.
- Do not discuss items with other reviewers until both have submitted.
