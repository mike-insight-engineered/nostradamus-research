# Pilot corpus preparation — Phase 2 (CAL-05 to CAL-10)

*Prepared 2026-10-21 by Claude Code. Everything here is **candidate** material awaiting human verification.*

| Artifact | Path |
|---|---|
| 20-slot candidate manifest | `data/candidates/pilot_candidates.jsonl` (+ `.csv`) |
| Draft diplomatic transcriptions (AI-assisted, UNVERIFIED) | `data/transcriptions/drafts/pilot_draft_passages.cleared.jsonl` (LA-01); rights-pending drafts in the git-ignored `*.pending-rights.jsonl` |
| **Rights and provenance matrix** (remediation) | `research/pilot/rights-provenance-matrix.md` |
| **Candidate-quality audit (20 slots), replacements** | `research/pilot/candidate-quality-audit.md` |
| **Review packets** (four drafts) | `research/pilot/review-packets/LA-01/`; FP-01, FV-01, MX-01 under the git-ignored `review-packets/pending-rights/` |
| **Translation assignments** (Target-1 passages) | `research/pilot/translation-assignments/` |
| **Acquisition priorities** | `research/pilot/acquisition-priorities.md` |
| **Human actions** | `research/pilot/human-actions.md` |
| Source registry (updated) | `data/sources/source_registry.jsonl`, `source_candidates.csv` |
| Source and licence audit | `research/pilot/source-licence-audit.md`, `reports/source-audit.md` |
| Reference translation availability | `research/pilot/reference-translation-matrix.md` |
| Transcription verification queue + per-slot sheets | `research/pilot/transcription-verification-queue.md`, `research/pilot/transcription-review/` |
| Reference translation queue + translator brief | `research/pilot/reference-translation-queue.md` |
| Unresolved provenance issues | `research/pilot/provenance-issues.md` |
| Evidence snapshots (catalogue and platform records as retrieved) | `research/pilot/evidence/` |
| Verification protocol | `docs/transcription-verification-protocol.md` |

## Method

1. **Discovery:** fr.wikisource "Index – 16e siècle" (131 books) and e-rara searches. BVH was searched, but its TEI
   server was unreachable. Gallica itself returned HTTP 403 to this environment.
2. **Witness identification:** each Gallica ARK was matched **mechanically** to a BnF Catalogue général record
   whose field 856 links that ARK (SRU API), and holdings were read from field 930. e-rara records supply holding
   library, shelfmark and VD16 or other references.
3. **Facsimile reading:** page images (Commons 1280 px derivatives of the Gallica scans, or e-rara IIIF images)
   were viewed directly. Draft diplomatic transcriptions were made from the images and cross-checked against
   Wikisource where available. Image SHA-256 hashes are recorded.
4. **Nothing was promoted beyond `located`**, which needs only a URL and an access date. Catalogue matches are
   recorded as notes, not as `verification_evidence`, because that field requires a named human verifier.

## Source table

Status: `located` = digitised exemplar accessed and identified. **No source is `provenance_checked`.**
"BnF match" = BnF catalogue record whose 856 field links the same Gallica ARK.

| Slot(s) | Witness | Facsimile link | Catalogue reference (corroborated by) | Copy identified? | Status |
|---|---|---|---|---|---|
| MX-01 | Rabelais, *Pantagruel*, Lyon [Claude Nourry], [1531/32] | [Gallica btv1b86095855](https://gallica.bnf.fr/ark:/12148/btv1b86095855) · [Commons](https://commons.wikimedia.org/wiki/File:Rabelais_-_Pantagruel,_ca_1530.djvu) | BnF cb311673938, RES-Y2-2146 (BnF match + Wikidata Q124285733 + BVH docId) | yes (single copy; three pointers) | located |
| MX-02 | Rabelais, *Gargantua*, Lyon [F. Juste], 1535 | [Gallica btv1b86000209](https://gallica.bnf.fr/ark:/12148/btv1b86000209) | BnF cb31167378c, RES-Y2-2130 (BnF match) | yes (single copy) | located |
| FP-01 | du Bellay, *Deffence*, Paris [A. L'Angelier], 1549 | [Gallica bpt6k1050733](https://gallica.bnf.fr/ark:/12148/bpt6k1050733) | BnF cb36123953k (BnF match) | no (2 copies) | located |
| FP-02 | Marguerite de Navarre, *Heptaméron*, Paris, B. Prevost, 1559 | [Gallica btv1b86171930](https://gallica.bnf.fr/ark:/12148/btv1b86171930) | BnF cb39335597j, Arsenal 4-BL-4332 (BnF match) | yes (single copy) | located |
| FP-03 | Hélisenne de Crenne, *Songe*, Paris, D. Janot, 1541 | [Gallica btv1b8608308c](https://gallica.bnf.fr/ark:/12148/btv1b8608308c) | BnF cb30285823f (BnF match) | no | located |
| FP-04 | Aneau, *Alector*, Lyon, P. Fradin, 1560 | [Gallica bpt6k79073s](https://gallica.bnf.fr/ark:/12148/bpt6k79073s) | BnF cb37285228g (BnF match) | no shelfmark in record | located |
| FP-05 | Dentière, *Epistre*, "Anvers, Martin l'empereur" (stated), 1539 | [e-rara-12685](https://doi.org/10.3931/e-rara-12685) | e-rara; GLN-1329; Index Aureliensis 151.424 | yes (MHR D Den 1) | located |
| FV-01 | Pernette du Guillet, *Rymes*, Lyon, J. de Tournes, 1545 | [Gallica btv1b8609525w](https://gallica.bnf.fr/ark:/12148/btv1b8609525w) | BnF cb315505552 (BnF match) | probable (RES-YE-1341) | located |
| FV-02 | du Bellay, *L'Olive*, Paris, 1549 | [Gallica btv1b86095195](https://gallica.bnf.fr/ark:/12148/btv1b86095195) | BnF cb30357502p (BnF match) | no (3 copies) | located |
| FV-03 | Ronsard, *Continuation des Amours*, Paris, V. Sertenas, 1555 | [Gallica bpt6k70074z](https://gallica.bnf.fr/ark:/12148/bpt6k70074z) | BnF cb31242513w, RES-YE-4758 (BnF match) | yes (single copy) | located |
| FV-04 | Marot, *Œuvres*, Lyon, G. Roville (printed by Roussin & Ausoult), 1547 | [Gallica bpt6k109342q](https://gallica.bnf.fr/ark:/12148/bpt6k109342q) | BnF cb308886109, RES-YE-1564/1565 (BnF match) | yes | located |
| FV-05 | Marguerite de Navarre, *Marguerites*, Lyon, J. de Tournes, 1547 | [Gallica btv1b8609559p](https://gallica.bnf.fr/ark:/12148/btv1b8609559p) | BnF cb30882574t (BnF match) | probable (RES-YE-1628) | located |
| LA-01, MX-04 | Erasmus, *Moriae encomium*, Strasbourg, Schürer, Oct. 1512 | [e-rara-64232](https://doi.org/10.3931/e-rara-64232) | e-rara; VD16 E 3181; Bezzel 1300 | yes (ZB Zürich III M 81,2) | located |
| LA-02 | Erasmus, *Colloquiorum formulae*, Basel, Gengenbach, 1520 | [e-rara-240](https://doi.org/10.3931/e-rara-240) | e-rara; VD16 ZV 5269 | yes (UB Basel FL X 21:2) | located |
| LA-03 | Bèze, *Poemata*, Paris, Badius / R. Estienne, 1548 | [e-rara-77094](https://doi.org/10.3931/e-rara-77094) | e-rara; Gardy 1; Renouard 16 | no (2 shelfmarks) | located |
| LA-04 | Valla, *De libero arbitrio*, Basel, Cratander, 1526 | [Gallica bpt6k5401626k](https://gallica.bnf.fr/ark:/12148/bpt6k5401626k) | BnF cb315224967 (BnF match) | no | located |
| LA-05 | Erasmus, *Familiaria quaedam colloquia*, Zürich, Froschauer, [c. 1540] | [e-rara-195](https://doi.org/10.3931/e-rara-195) | e-rara; VD16 E 2420 | yes (ZB Zürich 25.1008) | located |
| MX-03 | Peletier, *Dialogue de l'ortografe*, [Poitiers, Marnef], 1550 | [Gallica btv1b8624649n](https://gallica.bnf.fr/ark:/12148/btv1b8624649n) (not viewed) | BnF cb32515020j (BnF match) | no (2 copies) | candidate |
| MX-05 | Meigret, *Défenses*, [Paris, Wechel], 1550 | [IA fre_b2063628](https://archive.org/details/fre_b2063628) (microfiche) | none (IA metadata only) | **no; second-generation** | candidate |

**Confirmed vs unresolved:**
- *Confirmed by retrieved records:* the catalogue links between each scan and a catalogue record, the holdings
  listed, the imprints and collations quoted in the registry, and the e-rara licence statements.
- *Unresolved:* which copy was digitised (where several exist), USTC numbers (none obtained), current Gallica terms,
  printer attributions marked as discrepancies, and every transcription reading.
