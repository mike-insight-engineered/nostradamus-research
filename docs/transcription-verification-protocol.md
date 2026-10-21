# Transcription verification protocol (two-person QC1 check)

Applies to every passage before it can be `transcription_verified`. It complements
[transcription-policy.md](transcription-policy.md), which defines *what* a diplomatic transcription contains.

## Roles

- **Transcriber:** produces or corrects the diplomatic transcription from the facsimile.
- **Independent checker:** a different person who compares the transcription with the facsimile without relying
  on the transcriber's notes. An AI system can be neither. AI or OCR drafts are only starting points and are
  labelled `UNVERIFIED`.

## Materials

The library's own viewer at full resolution (Gallica, e-rara, BVH), **not** only a Commons derivative: derivatives
may crop gutters or reduce resolution. Use the per-slot sheet in `research/pilot/transcription-review/`.

## Procedure

1. **Identify the copy.** Confirm on the library record which shelfmark was digitised. Record the stable image URL
   (IIIF or ARK with page or view number) as `facsimile_reference`, and the signature, folio or page as `locator`.
2. **Fix the extent.** Record the first and last words, and which printed lines are included.
3. **Transcribe or correct line by line.** Keep the printed lineation (one `\n` per printed line), spelling,
   capitals, punctuation and spacing, ſ, u/v, i/j, æ/œ, ⁊ or &, tildes and abbreviation signs (ꝗ ꝑ q̃ ꝫ ꝯ …).
   Do not expand, correct or modernise. The project's documented conventions:
   r rotunda (ꝛ) → `r`; ligatures other than æ/œ/ſs are decomposed; apostrophe → `’`.
   Record any further convention in `typography_notes`.
4. **Mark uncertainty in the notes, not the text.** List each uncertain reading (line, what is seen, alternatives).
5. **Exclude copy-specific marks** (manuscript annotations, stamps, underlining) from the text, and mention them in `notes`.
6. **Independent check.** The checker reads the facsimile and the transcription in parallel, character by
   character, and logs every difference in the sheet's corrections table. Disagreements are resolved by
   re-examining the image, or are left explicitly unresolved.
7. **Sign-off.** Both names, qualifications and dates go on the sheet. The passage record gets a
   `transcription_checked` review event by the checker, and its hash is recomputed (`nr passages import`
   locks it).
8. **Escalate** when a reading cannot be settled from the image (damage, show-through, a poor scan). Request a
   better image from the holding library, or mark the passage `unresolvable` and replace it.

## Acceptance criterion

A transcription is accepted when the checker finds **no unexplained difference** from the facsimile, and every
remaining uncertainty is documented. Error counts found at the check are recorded on the sheet, so the
reliability of AI-assisted drafts can itself be measured.
