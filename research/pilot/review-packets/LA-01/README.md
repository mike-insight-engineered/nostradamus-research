# Review packet — LA-01 / PSG-LP-0001

**For:** a qualified transcriber and an independent checker (two different people).
**Task:** verify, character by character, a DRAFT diplomatic transcription against the facsimile.

> The draft was produced by an AI system reading a facsimile image. It is **UNVERIFIED**. Do not treat
> it as correct; it may contain misreadings. This packet contains **no translation of any kind**. Do not
> consult AI tools, and do not use the Wikisource text, except as a last-resort hint recorded as such.

## 1. Source

- Registry ID: `SRC-ERASMUS-MORIAE-1512-SCHURER` (status `located`)
- Author / title: Desiderius Erasmus — *Moriae Encomivm Erasmi Roterodami Declamatio ...*
- Imprint: Argentorat. (Strasbourg) : Ex Aedibus Schurerianis (Matthias Schürer), Mense Octobri. Anno M. D. XII
- Edition / collation: [42] Bl.; 21 cm (4°)
- Holding institution / copy: Zentralbibliothek Zürich, III M 81,2
- Catalogue: e-rara 17496710; VD 16 E 3181; Bezzel (Erasmus) 1300
- Facsimile used for the draft (derivative): https://doi.org/10.3931/e-rara-64232
- Original digitisation (use this to verify): doi:10.3931/e-rara-64232
- Image/quality notes: Bibliographic data below come from the cited records; no person has yet compared them with the physical or facsimile title page.
- Rights (`public_domain`): see `research/pilot/rights-provenance-matrix.md`

## 2. Where to look

- Locator: Signature 'Aa iiij' (recto, per signature line at foot); e-rara canvas 17496718 (IIIF image https://www.e-rara.ch/i3f/v20/17496718).
- Image read for the draft (derivative, with SHA-256): https://www.e-rara.ch/i3f/v20/17496718/pct:10,40,82,26/1500,/0/default.jpg (crop read; sha256 26d57f013b188db1f8a615a58c9617207c3b3ca582b601069fd9a0bfc00339c7); full page: https://www.e-rara.ch/i3f/v20/17496718/full/full/0/default.jpg; record https://doi.org/10.3931/e-rara-64232
- **Verify against the original digitisation** (persistent identifier above), at full resolution.

## 3. Draft transcription (line-numbered copy in `transcription_lines.txt`)

```text
Tametſi quorſum tandem attinet,
mei velut vmbram atqꝫ imaginem finitione repræſenta
re , cum ipſam me coram præſentes præſentem oculis
intueamini ? Sum etenim vti videtis , vera illa largitrix
ἐάων, quam Latini ſtulticiam, Græci μωρίαν appellant.
```

SHA-256 of the draft text: `2e58e3c298d1eae0d15f3815c10c6a3a99c3c9f63c2ffc8717d514dd36520f56`

## 4. Conventions used in the draft

Roman type with Greek. Passage begins mid-line (preceding words on the line: 'genus ita cõſentiat ,'). Lineation as printed; no hyphen at 'repræſenta|re'. 'atqꝫ' = atque with the -que abbreviation sign (ꝫ, U+A76B). æ ligature kept. Space before some commas and before '?' as printed. Initial v in 'vmbram', 'vti'.

## 5. Flagged uncertainties (resolve each one, or leave it explicitly unresolved)

Printed marginal gloss beside the Greek line reads '.i.honoꝝ' or '.i.bonoꝝ' (first letter uncertain) — recorded here, not in the text. UNCERTAIN: accents/breathings of the Greek words; '?' mark shape.

## 6. Other notes

AI-ASSISTED DRAFT. Produced by Claude Code reading a facsimile image; NOT checked by any person. Must be verified line by line against the facsimile by a human transcriber and an independent checker (docs/transcription-verification-protocol.md) before any status change. No reference translations attached. No modern transcription was consulted (none found for this edition). Public Domain Mark facsimile.

## 7. Dictionary and reference works (cite only what you actually consult)

- `RES-HUGUET` — Edmond Huguet, Dictionnaire de la langue française du seizième siècle
- `RES-DMF-ATILF` — Dictionnaire du Moyen Français (DMF) — ATILF (CNRS / Université de Lorraine)
- `RES-COTGRAVE-1611` — Randle Cotgrave, A Dictionarie of the French and English Tongues (London, 1611)
- `RES-ESTIENNE-1549` — Robert Estienne, Dictionaire francoislatin (Paris, 1549)
- `RES-NICOT-1606` — Jean Nicot, Thresor de la langue françoyse (Paris, 1606)
- `RES-GODEFROY` — Frédéric Godefroy, Dictionnaire de l'ancienne langue française et de tous ses dialectes du IXe au XVe siècle
- `RES-DU-CANGE` — Du Cange et al., Glossarium mediae et infimae latinitatis
- `RES-PERSEUS` — Perseus Digital Library — Tufts University

## 8. Instructions

1. Read `docs/transcription-verification-protocol.md` in full.
2. **Transcriber:** confirm the copy and shelfmark in the library's own viewer; record the exact leaf or
   page and the stable image URL; correct the draft line by line in `corrections.csv`.
3. **Checker (a different person):** repeat the comparison independently. Do not rely on the transcriber's
   corrections, then reconcile.
4. Keep abbreviations, ſ, u/v, i/j, ⁊ or &, tildes, punctuation, spacing and lineation exactly as printed.
   Do not modernise or correct.
5. Record copy-specific marks (manuscript notes, stamps) in the notes, never in the text.
6. Both sign `signoff.md`. Return the packet to the project lead. The status changes to
   `transcription_verified` only after the project lead records your check in the passage history.
