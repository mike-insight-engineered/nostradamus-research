# Rights and provenance matrix (remediation, 2026-10-21)

Supersedes the platform section of `source-licence-audit.md`. Each determination records its **URL**,
**evidence type** and **date**:
- **READ:** the primary page or document was fetched and read in full.
- **REPORTED:** a secondary summary only.
- **NOT CHECKED:** no evidence yet.

No legal advice is implied. Every REPORTED or NOT CHECKED cell needs a human to confirm it.

## 1. Platform determinations

| # | Platform / layer | Determination | Evidence type | URL | Date |
|---|---|---|---|---|---|
| R-01 | BnF: **descriptive metadata** (catalogue, data.bnf) | Licence Ouverte de l'État since 1 Jan 2014. Free reuse, citing the source and the retrieval date. | READ | https://data.bnf.fr/fr/licence | 2026-10-21 |
| R-02 | BnF/Gallica: **digitised images** (public-domain works) | Free for non-commercial use with source attribution; academic and scientific users exempt from the commercial-use fee in their publications; other commercial use licensed. | READ (policy, Oct 2019) | https://www.bnf.fr/sites/default/files/2019-10/CP_politique_diffusion_images_BnF.pdf | 2026-10-21 |
| R-03 | Gallica: **current CGU** | Non-commercial reuse free with the mention "Source gallica.bnf.fr / BnF"; commercial reuse requires a fee and licence; metadata under Etalab. | REPORTED (search summary only). Page returns HTTP 403 directly and via Wayback. | https://gallica.bnf.fr/accueil/fr/html/conditions-dutilisation-de-gallica | 2026-10-21 |
| R-04 | Gallica: **OCR text** | Not determined | NOT CHECKED | — | — |
| R-05 | BVH: **images** | Partner libraries keep ownership and copyright; reproduction for collective use prohibited without authorisation; commercial use needs specific authorisation. | READ | https://www.bvh.univ-tours.fr/mentions.asp | 2026-10-21 |
| R-06 | BVH Epistemon: **transcriptions** | CONFLICT: the editorial principles state CC BY-NC-SA 4.0 (private reading and research); the index page badge links CC BY-NC-ND 2.0 FR. | READ (both pages) | https://www.bvh.univ-tours.fr/Epistemon/principeseditoriaux.asp ; https://www.bvh.univ-tours.fr/Epistemon/index.asp | 2026-10-21 |
| R-07 | BVH: **metadata / OAI** | Not determined | NOT CHECKED | https://www.bvh.univ-tours.fr/oai.asp | — |
| R-08 | e-rara: **digitised documents** | Licence stated per document. PDM documents may be freely used for scholarly, private, non-commercial **and commercial** purposes. Others are CC BY-SA 4.0. Cite with the DOI. | READ | https://www.e-rara.ch/wiki/termsOfUse | 2026-10-21 |
| R-09 | e-rara: **record metadata** | No separate statement found on the terms page | NOT CHECKED | (same) | — |
| R-10 | Wikisource: **transcriptions** | CC BY-SA 4.0 (also GFDL). Not diplomatic. | READ (page footer) | https://fr.wikisource.org/ | 2026-10-21 |
| R-11 | Wikimedia Commons: **files** | Contributor label "Public domain"; this does **not** override the originating library's terms | READ (file metadata) | https://commons.wikimedia.org/ | 2026-10-21 |
| R-12 | Wikidata: **data** | CC0 (Wikidata standard; not re-read this session) | REPORTED | https://www.wikidata.org/ | — |
| R-13 | Internet Archive microfiches (Ottawa) | Not determined | NOT CHECKED | https://archive.org/details/fre_b2063628 | — |
| R-14 | USTC metadata | Not determined | NOT CHECKED | https://www.ustc.ac.uk/ | — |

## 2. Per-witness rights by layer

Layers: **Meta** = catalogue metadata · **Text** = historical work · **Image** = digitised facsimile ·
**Transcr.** = existing third-party transcription · **Transl.** = modern translations (see the availability report).

| Witness | Meta | Text | Image | Transcr. | Transl. | May the project's own transcription be committed now? |
|---|---|---|---|---|---|---|
| Gallica witnesses (Pantagruel, Gargantua, Deffence, Heptaméron, Songe, Alector, Rymes, Olive, Continuation, Marot, Marguerites, Valla, Peletier, Hypnérotomachie) | R-01 open (cite BnF, date) | PD | R-02/R-03: non-commercial; current CGU unread | Wikisource CC BY-SA (where present); BVH NC (Pantagruel TEI) | in copyright where they exist | **No — rights-pending** (git-ignored) until the lead confirms R-03 permits publication |
| e-rara witnesses (Moriae 1512, Colloquia 1520 & c.1540, Bèze 1548, Dentière 1539, Atrocianus 1528) | R-09 unchecked (factual data, DOI cited) | PD | R-08 PDM: free for all uses | none (Dentière: Wikisource CC BY-SA) | in copyright where they exist | **Yes**, with attribution to the holding library and the DOI |
| Meigret 1550; Thierry 1564; Cartier 1545 (microform reproductions) | IA / BnF records | PD | R-13 unchecked | — | — | No (and these witnesses are excluded or rejected) |

## 3. Corrections made to earlier statements

| Earlier statement | Correction |
|---|---|
| Gallica metadata "reported to be under Etalab; to confirm" | **Confirmed (READ):** Licence Ouverte de l'État, R-01. Updated in 14 registry records. |
| e-rara rights known only from individual records | **Confirmed (READ)** at platform level, R-08. PDM explicitly allows commercial use. |
| MX-01: "the Commons derivative crops line ends at the gutter" | **Incorrect.** The loss comes from a tight binding in the original digitisation (R-11 file at 2096 px shows the page curving into the gutter). Registry and manifest corrected. |
| Phase 2 `rights_status` for RES-E-RARA was `unknown` | Unchanged, deliberately: terms differ per document (PDM vs CC BY-SA), so the per-document status governs. |
| Repository "Licensed under GPL-3.0" | Replaced by split licensing: software GPL-3.0-or-later; original docs and annotations CC BY 4.0; third-party material under its own terms (`DATA_LICENSE.md`). |

## 4. Open rights actions (human)

1. Read the current Gallica CGU (R-03) in a browser and record its date and wording here.
2. Decide whether short project transcriptions made from Gallica images may be published in a public repository (non-commercial clause; academic exemption).
3. Resolve BVH R-06 by email (bvh@univ-tours.fr), if BVH TEI or images will be used.
4. For each published translation to be used as a reference: obtain written permission (publisher), see the availability report.
