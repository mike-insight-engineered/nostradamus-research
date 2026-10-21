# Calibration acquisition priorities (remediation, 2026-10-21)

**Target 1 (project lead's preference):** four passages, one per category, that are fully authenticated,
independently transcribed, independently translated and blind-reviewed. This tests the whole workflow before
scaling to 20.

## Target-1 set and the path to readiness

| Order | Slot | Why first | Steps remaining (in order) | Main risk |
|---|---|---|---|---|
| 1 | **FV-01** Pernette, *Rymes* 1545 | Clearest image; complete short poem; bilingual scholarly edition exists | confirm copy in Gallica → catalogue evidence (named person) → two-person transcription check → commission FR + literal EN; request Finch permission → reviewer check of references | Gallica rights for publishing the transcription |
| 2 | **LA-01** Erasmus, *Moriae* 1512 | PDM image (no rights barrier); full-resolution IIIF; authoritative translation exists | catalogue evidence (VD16 E 3181) → two-person check (Greek accents) → compare passage with the ASD text → commission FR + literal EN | Edition mismatch with published translations |
| 3 | **FP-01** du Bellay, *Deffence* 1549 | Legible roman type; first edition; bilingual scholarly edition exists | identify copy → evidence → two-person check (ꝗ/ꝑ, Greek) → commission FR + literal EN; Helgerson permission | Copy identification (two BnF copies) |
| 4 | **MX-01** Rabelais, *Pantagruel* [1532] | Best-corroborated witness; strong code-switching test | Gallica viewer check of line-ends → evidence → two-person check → commission FR + EN from a Rabelais specialist | Binding-gutter readings; no translation of this edition exists |

**Fallback for the mixed category:** if MX-01 line-ends cannot be confirmed, use a passage from LA-01's page
(MX-04: Latin/Greek code-switching, PDM image), or the proposed MX-05 replacement (*Hypnérotomachie* 1546),
after approval.

## Then (slots 5–20)

1. Approve or reject the proposed replacements (MX-05 → Hypnérotomachie; LA-05 → Atrocianus).
2. Fix passages and locators where missing (FP-04, FP-05, FV-02, FV-05, LA-02, LA-03, LA-04, MX-03).
3. Prefer slots whose facsimiles are public-domain-marked (e-rara) or whose rights are cleared, while the Gallica
   publication question remains open.
4. Resolve MX-02's image problem before any transcription work.
5. Reduce Erasmus concentration (4 slots) when expanding to 80.

## Gating rules

- No slot enters `data/processed/passages.jsonl` before its witness is `provenance_checked` (named person) and
  its transcription is checked by an independent person.
- No reference is attached unless a named human produced it (or it is licensed), its source edition is recorded,
  and its rights are documented.
- No pipeline run on real passages (development split only) before Target 1 passes the above; no paid API use
  without explicit authorisation.
