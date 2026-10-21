# Transcription policy (QC1)

## Diplomatic transcription

The `diplomatic_transcription` records the witness as printed:

- **Spelling** exactly as printed (`faict`, `estoit`, `ung`, `cheuaulx`).
- **Typography:** long s (`ſ`), u/v and i/j as printed, ligatures (`æ`, `œ`), `&`, tildes and other
  abbreviation marks (`cõme`, `q̃`). Use precomposed Unicode where it exists; otherwise a combining
  mark. Describe unusual sorts in `typography_notes`.
- **Punctuation** as printed, including virgule `/` and period-specific marks.
- **Line breaks** for verse as `\n`. For prose, record line breaks only if they matter (e.g.
  hyphenation), and say so in `typography_notes`.
- **Abbreviations are not expanded.** Expansions belong in TEI `<choice><abbr/><expan/></choice>` or
  in the normalised reading.
- **Uncertain readings:** transcribe the most likely reading and record the uncertainty in
  `spelling_notes`/`notes`. In TEI, use `<unclear>`.
- **No silent correction** of apparent misprints. Record them as `textual_variants` or notes, or in
  TEI `<sic>/<corr>`.

## Locking and corrections

On import, the SHA-256 of the exact diplomatic text is stored in `diplomatic_sha256`. Any change
breaks validation. To correct a transcription:

1. Confirm the error against the facsimile, with a second person where possible.
2. Update the text **and** the hash, and append a `review_history` event (`transcription_checked` or
   `comment`) stating what changed and why.
3. `transcription/integrity.py:compare_corpora` reports any change without such an event as
   **UNDOCUMENTED**.

## Normalised reading (editorial, optional)

A separate layer for reader orientation, produced by named rules
(`transcription/normalisation.py`):

- Safe rules (default): `long_s`, `ligatures_ae_oe`.
- Editorial rules (opt-in, must be checked): `u_v_consonantal`, `v_u_initial_vowel`, `i_j_initial`,
  `nasal_tilde`, `ampersand`.
- Never: lexical modernisation, punctuation changes, word reordering or word splitting/merging. The
  safeguards reject these.

Pipelines always translate the diplomatic text. The normalised reading is shown only if
`include_normalised_reading` is enabled, and is labelled as editorial.

## Verification

`transcription_verified` requires a check by someone other than the transcriber against the
facsimile, recorded as a `transcription_checked` review event, plus a `locator` and a
`facsimile_reference`.

## TEI

`transcription/tei.py` exports a minimal TEI P5 document and imports the diplomatic layer, preferring
`abbr/orig/sic` over `expan/reg/corr`. Passage import accepts a `tei_file` field.
