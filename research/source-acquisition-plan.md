# Source acquisition plan (CAL-02, CAL-05–CAL-08)

> **Status 2026-10-21 (Phase 2):** steps 1–3 carried out where access allowed; see `research/pilot/README.md`.
> Step 4 has produced 4 unverified AI-assisted drafts; no human check yet. Steps 5–6 not started.

## Goal

Twenty pilot passages (5 French prose, 5 French poetry, 5 Latin, 5 mixed/difficult) from
authenticated witnesses, with diplomatic transcriptions checked against facsimiles and
rights-cleared storage. Then extend to 80.

## Step 1 — Confirm resources and terms (CAL-02)

| Resource | Registry ID | Questions to answer |
|---|---|---|
| BVH / Epistemon | `RES-BVH-EPISTEMON` | Licence for images and TEI transcriptions? Which witnesses have both? Can TEI be used as a starting point (still checked against images)? |
| Gallica | `RES-GALLICA` | Current conditions of use for images/OCR; ARK identifiers for candidate witnesses |
| BnF catalogue / USTC | `RES-BNF-CATALOGUE`, `RES-USTC` | Edition identification for `provenance_checked` evidence |
| Frantext | `RES-FRANTEXT` | Access route; licence for quoting period usages as evidence |
| Perseus | `RES-PERSEUS` | Per-text licences; usefulness for Renaissance (not classical) Latin |
| DMF, Huguet, Godefroy, Cotgrave, Estienne, Nicot, Du Cange | `RES-*` | URLs, access, rights for quoting entries in `lexical_evidence.jsonl` |

Record results with `nr sources promote ... --to located` (URL + access date) and notes on rights.

## Step 2 — Locate and authenticate witnesses

For each candidate witness (`SRC-*`, see `candidate-authors.md`):

1. Find a digitised exemplar and record the URL/ARK and access date → `located`.
2. Identify the edition: compare the title page, imprint, colophon and printer's device with a
   catalogue record (USTC/BnF). Record the holding institution and shelfmark → `provenance_checked`,
   with `catalogue_record` evidence by a named person.
3. Note variant issues/states and alternative early editions (e.g. disputed first editions).

## Step 3 — Select passages

- 40–120 words (or a sonnet or stanza group), self-contained, and representative of the category's
  difficulties.
- Prefer passages *without* widely reproduced modern translations where possible (contamination),
  and record when one exists.
- At least three works per pilot group where feasible. The mixed group targets real code-switching
  (French with embedded Latin), latinising French and dense abbreviation.
- Record the rationale and exact locator (signature/folio/page and image number).

## Step 4 — Transcribe and check

Diplomatic transcription per `docs/transcription-policy.md` (TEI or plain), independent check
against the facsimile by a second person, then import (`nr passages import`) and set
`transcription_verified` with a `transcription_checked` event.

## Step 5 — References (CAL-09)

Commission at least one independent French and one English reference per passage (or license
published translations), with translator details, rights and independence recorded.

## Step 6 — Gate checks

`nr corpus stats`, `nr corpus provenance`, `nr corpus leakage`, `scripts/build_pilot_manifest.py`,
then `nr report milestone`.

## Effort estimate (to refine)

Per passage: location and authentication 1–3 h (shared across passages from one witness);
transcription 0.5–1 h; check 0.5 h; references 1–2 h per language. A pilot of 20 is therefore
roughly 60–120 person-hours before review.
