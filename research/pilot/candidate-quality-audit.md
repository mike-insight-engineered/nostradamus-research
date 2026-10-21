# Candidate-quality audit: all 20 pilot slots (remediation, 2026-10-21)

Machine-readable flags are in `data/candidates/pilot_candidates.jsonl` (`audit_flags`, `proposed_replacement`).
**No slot is research-ready:** none has an authenticated witness, a verified transcription or a reference
translation. The audit says *how far* each slot is from readiness.

Legend: ✔ satisfied · ⚠ problem or unconfirmed · ✖ blocking · — not applicable or not yet assessable.

| Slot | Copy / edition identified | Image quality | Duplicate work | Classification | Author/work leakage | Page reference | Readings verifiable | Readiness |
|---|---|---|---|---|---|---|---|---|
| FP-01 Deffence 1549 | ⚠ edition ✔ (first ed.); copy ✖ (RES-X-1888 or Arsenal) | ✔ clear roman | ✔ | ✔ french_prose | ⚠ du Bellay also FV-02 | ⚠ Commons p. 9; leaf not recorded | ⚠ Greek βάρ-ϐαρας; ꝗ/ꝑ | **High** (draft exists) |
| FP-02 Heptaméron 1559 | ✔ single Arsenal copy; ⚠ printer Prevost vs Sertenas | — not viewed | ✔ | ✔ | ⚠ Marguerite also FV-05 | ⚠ f. 1 via Wikisource TOC | — | Medium |
| FP-03 Crenne Songe 1541 | ⚠ 2 BnF holdings | — not viewed | ✔ | ✔ | ✔ | ⚠ Commons p. 33; extent unfixed | — | Medium |
| FP-04 Alector 1560 | ✖ no shelfmark; printer Fradin vs "Alton" | — | ✔ | ✔ | ✔ | ✖ missing | — | Low |
| FP-05 Dentière 1539 | ✔ copy (MHR D Den 1); ⚠ imprint probably false | — | ✔ | ✔ | ✔ | ✖ missing | — | Medium (PDM image) |
| FV-01 Pernette Rymes 1545 | ⚠ probably RES-YE-1341 (stamp) | ✔ very clear italic | ✔ | ✔ french_poetry | ✔ | ✔ p. 9, sig. a5r | ⚠ ſs ligatures; spacing | **High** (draft; complete poem) |
| FV-02 Olive 1549 | ✖ 3 copies | — | ✔ | ✔ | ⚠ du Bellay (FP-01); shared privilege | ✖ missing | — | Low |
| FV-03 Continuation 1555 | ✔ single copy RES-YE-4758 | — | ✔ | ✔ | ✔ | ⚠ Commons p. 25 | — | Medium |
| FV-04 Marot Œuvres 1547 | ✔ RES-YE-1564/5 | ⚠ in-16: untested | ✔ | ✔ | ✔ | ⚠ Commons p. 31 | — | Medium |
| FV-05 Marguerites 1547 | ⚠ probably RES-YE-1628 | — | ✔ | ✔ | ⚠ Marguerite (FP-02) | ✖ missing | — | Low |
| LA-01 Moriae 1512 | ✔ ZB Zürich III M 81,2; VD16 E 3181 | ✔ IIIF full resolution | ⚠ same page as MX-04 | ✔ latin_prose (embedded Greek) | ⚠ Erasmus ×3 slots | ✔ sig. Aa iiij r | ⚠ Greek accents; gloss initial | **High** (draft; PDM) |
| LA-02 Colloquia 1520 | ✔ UB Basel FL X 21:2 | — | ⚠ same work as LA-05 | ✔ | ⚠ Erasmus | ✖ missing | — | Medium |
| LA-03 Bèze Poemata 1548 | ⚠ 2 BGE shelfmarks | — | ✔ | ✔ latin_verse | ✔ | ✖ missing | — | Medium |
| LA-04 Valla 1526 | ⚠ 2 copies | — | ✔ | ⚠ composed c. 1439 (outside 1500–1570 composition window) | ✔ | ✖ missing | ⚠ Wikisource text is a French translation | Low |
| LA-05 Colloquia c. 1540 | ✔ ZB Zürich 25.1008 | — | ✖ same work as LA-02 | ✔ | ⚠ Erasmus | ✖ missing | — | **Replace** → Atrocianus 1528 |
| MX-01 Pantagruel [1532] | ✔ RES-Y2-2146 (three pointers) | ⚠ **binding gutter loss in the original digitisation** (not a Commons crop); passage words appear continuous at 1920 px | ✔ | ✔ frm + difficult override | ⚠ Rabelais also MX-02 | ⚠ Commons p. 30; leaf not recorded | ⚠ "fretōs" vs Wikisource "transfetons"; hidden hyphens | **High** with image caveat |
| MX-02 Gargantua 1535 | ✔ RES-Y2-2130 | ✖ **Commons DjVu heavily compressed** (2133×3200 in 19 MB / 211 pp.); unreadable abbreviations | ✔ | ✔ | ⚠ Rabelais (MX-01) | ✔ sig. E ij r | ✖ not from this image | Medium (needs a better image) |
| MX-03 Peletier Dialogue 1550 | ⚠ 2 copies, both digitised | — **not viewed** (Gallica blocked) | ✔ | ⚠ reformed orthography, tagged as difficult French prose | ✔ | ✖ missing | — | Low |
| MX-04 Moriae Greek proverb | ✔ (as LA-01) | ✔ | ✖ same work **and page** as LA-01 | ✔ | ⚠ Erasmus | ✔ Aa iiij r (lower) | — | Keep only if no independent mixed text is found |
| MX-05 Meigret Défenses 1550 | ✖ microfiche of an unidentified copy | ⚠ microfiche | ✔ | ✔ | ✔ | ✖ | ✖ | **Replace** → Hypnérotomachie 1546 |

## Image investigation (MX-01, MX-02)

- **MX-01 (Pantagruel, Commons file 2096×2953 px).** At 1920 px the verso page curves into a tight binding,
  and text from the facing page is visible beyond the gutter. Line-ends are therefore compressed or hidden in
  the **original capture**, so the Gallica viewer is unlikely to show more. Within the chosen passage, each split
  word continues on the next line (trāſ|fretōs, deam|bulons, deſ|pumons, amo|rabunds), so no letters appear lost,
  but a hidden hyphen or a partial letter cannot be ruled out. Options:
  (a) verify in the Gallica viewer;
  (b) ask the BnF Réserve for an image or a reading;
  (c) use the Limousin chapter in a second witness, for example the BVH facsimile of the 1542 Juste edition
      (Châteauroux), which is a revised text and would need its own slot.
- **MX-02 (Gargantua, Commons file 2133×3200 px, 211 pages in 19 MB).** Letterforms are smeared by
  compression even at 1920 px. A reliable transcription of the dense abbreviations is not possible from this
  file. Options: (a) Gallica's own images (untested here); (b) BVH witnesses seen in listings: the [1534] Juste
  (BnF Y2 2126, BVH TEI) and the 1542 Juste (Châteauroux, BVH facsimile).

## Proposed replacements (awaiting project-lead approval; not yet swapped)

| Slot | Proposed witness | Evidence | Caveat |
|---|---|---|---|
| MX-05 | `SRC-HYPNEROTOMACHIE-1546`: *Hypnerotomachie, ou Discours du songe de Poliphile*, Paris, for J. Kerver, printed by L. Cyaneus, 20 Aug 1546 | BnF cb302602909 (856 → btv1b8600169w; IFN-8600169); Commons/Wikisource index | A French **translation** (Jean Martin) of the Italian *Hypnerotomachia*; tests latinate French; copy not confirmed (5+ BnF copies) |
| LA-05 | `SRC-ATROCIANUS-ELEGIA-1528`: Atrocianus, *Elegia de bello rustico* … *epigrammata*, Basel, Faber Emmeus, 1528 | e-rara 26367201, doi:10.3931/e-rara-92307, VD16 A 4012, UB Basel, PDM | Passage not selected; adds a second Latin-verse slot |
| (rejected) | `SRC-THIERRY-DICTIONNAIRE-1564`: Thierry, *Dictionnaire françois-latin* | BnF record shows the Gallica item is a **1972 microfiche** | Second-generation; registered as rejected-for-use |

No replacement was found for **MX-04**, the second passage from the LA-01 page. It stays, flagged; the splitter
keeps both passages in the same partition.

## Leakage summary (by author)

Erasmus 4 slots (LA-01, LA-02, LA-05, MX-04); Rabelais 2 (MX-01, MX-02); du Bellay 2 (FP-01, FV-02);
Marguerite de Navarre 2 (FP-02, FV-05). With `group_by: work_id` these are separate groups. With
`group_by: author`, the 20-passage pilot forms 14 author groups (15 with the proposed replacements). For the pilot (which has no held-out
test split) this is acceptable. For the 80-passage corpus, prefer `group_by: author`, or cap each author at
two works.
