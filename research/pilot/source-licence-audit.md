# Source and licence audit — Phase 2 (2026-10-21)

> **Superseded in part (remediation, 2026-10-21):** the platform determinations, with URLs, evidence types
> and dates, are now in [`rights-provenance-matrix.md`](rights-provenance-matrix.md). Where the two differ,
> the matrix wins. Notably, BnF metadata (Licence Ouverte) and e-rara terms are now READ, not reported.

Rights are recorded **separately for five layers**: (1) the historical work, (2) the digital facsimile,
(3) any modern transcription or edition, (4) modern translations and annotations, (5) catalogue metadata
and API access. A statement is marked **read** only when the primary page or document was fetched and
read in this session. Otherwise it is marked **reported** (e.g. via a search-engine summary) or **not checked**.

> No legal conclusion is drawn here. Where terms are conditional, unclear or conflicting, the source stays
> `rights_status: unknown` in the registry. No transcription derived from it should be committed or
> published until the project lead decides (see ADR 0005, proposed).

## 1. Archives and platforms

| Platform | (2) Facsimile terms | (3) Transcription terms | (5) Metadata / API | Evidence |
|---|---|---|---|---|
| **BnF / Gallica** | **Read** (BnF press release, 2 Oct 2019): public-domain images free for non-commercial use with the mention of source; academic and scientific users exempt from the commercial-use fee in their publications; other commercial use licensed. **Reported** (search summary of current CGU): non-commercial reuse free with "Source gallica.bnf.fr / BnF"; commercial reuse subject to fee and licence. The current CGU page returned **HTTP 403** to this environment. | Gallica OCR text: terms not checked; OCR is not a verified transcription. | **Reported:** metadata under Etalab / Licence Ouverte. BnF SRU API used (`catalogue.bnf.fr/api/SRU`); API terms not read. | `research/pilot/evidence/` |
| **BVH / Epistemon (Tours)** | **Read:** partner libraries keep ownership/copyright of images; any use or reproduction of the digitisation work requires authorisation; commercial use requires specific authorisation. | **Read, conflicting:** editorial principles say CC BY-NC-SA 4.0 (private reading and research); the index page badge says CC BY-NC-ND 2.0 FR. Transcriptions are "patrimoniales", not diplomatic. | Not checked. TEI server unreachable. | `evidence/bvh_rights_excerpts_2026-10-21.md` |
| **e-rara (Switzerland)** | **Read** (per record): "Public Domain Mark", free download; holding institution asks for source citation. | No modern transcription. e-rara offers OCR for some titles (not used). | Not checked. | `evidence/e-rara_records_2026-10-21.json` |
| **Wikimedia Commons** | Files labelled "Public domain" by contributors. This **does not by itself** override the originating library's reuse terms for its digitisation. | — | MediaWiki API (open) | `evidence/wikisource_commons_metadata_2026-10-21.json` |
| **fr.wikisource** | (hosts Commons scans) | **Read:** CC BY-SA 4.0 (page footer). Conventions are mostly semi-normalised and not diplomatic. Used for discovery and cross-checking only. | MediaWiki API | page footer, 2026-10-21 |
| **Internet Archive** (Ottawa microfiche) | Not checked; microfiche reproductions of unidentified copies. | — | `archive.org/metadata` API | IA metadata |
| **USTC** | n/a | n/a | Site reachable; search is client-side JavaScript; **no USTC numbers obtained**. | — |

**Layer (1), the work:** every witness in the manifest was printed between 1512 and 1560. The texts are public domain by age.
**Layer (4), translations:** see `reference-translation-matrix.md`. No translation has been obtained or licensed.

## 2. Witnesses in the pilot manifest

| Witness (registry ID) | Facsimile platform | Registry `rights_status` | Commit-safe now? | Open rights question |
|---|---|---|---|---|
| SRC-RABELAIS-PANTAGRUEL-1532 | Gallica (via Commons) | unknown | No (decision pending) | Gallica terms for derived transcriptions; BVH TEI licence conflict |
| SRC-RABELAIS-GARGANTUA-1535 | Gallica (via Commons) | unknown | No | Gallica terms |
| SRC-DUBELLAY-DEFFENCE-1549 | Gallica (via Commons) | unknown | No | Gallica terms |
| SRC-MARGUERITE-HEPTAMERON-1559 | Gallica (via Commons) | unknown | No | Gallica terms; Arsenal copy "communication soumise à autorisation" (physical access only) |
| SRC-CRENNE-SONGE-1541 | Gallica (via Commons) | unknown | No | Gallica terms |
| SRC-ANEAU-ALECTOR-1560 | Gallica (via Commons) | unknown | No | Gallica terms |
| SRC-PERNETTE-RYMES-1545 | Gallica (via Commons) | unknown | No | Gallica terms |
| SRC-DUBELLAY-OLIVE-1549 | Gallica (via Commons) | unknown | No | Gallica terms |
| SRC-RONSARD-CONTINUATION-1555 | Gallica (via Commons) | unknown | No | Gallica terms |
| SRC-MAROT-OEUVRES-1547-ROVILLE | Gallica (via Commons) | unknown | No | Gallica terms |
| SRC-MARGUERITE-MARGUERITES-1547 | Gallica (via Commons) | unknown | No | Gallica terms |
| SRC-VALLA-LIBERO-ARBITRIO-1526 | Gallica (via Commons) | unknown | No | Gallica terms; the Wikisource French translation on the same index has unknown provenance |
| SRC-PELETIER-DIALOGUE-1550 | Gallica (not viewed) | unknown | No | Gallica terms |
| SRC-MEIGRET-DEFENSES-1550 | Internet Archive microfiche | unknown | No | Reproduction rights; unidentified original |
| SRC-ERASMUS-MORIAE-1512-SCHURER | e-rara | public_domain (PDM) | Yes, with attribution to ZB Zürich / e-rara | — |
| SRC-ERASMUS-COLLOQUIA-1520-GENGENBACH | e-rara | public_domain (PDM) | Yes, with attribution | — |
| SRC-ERASMUS-COLLOQUIA-1540-FROSCHAUER | e-rara | public_domain (PDM) | Yes, with attribution | — |
| SRC-BEZE-POEMATA-1548 | e-rara | public_domain (PDM) | Yes, with attribution | — |
| SRC-DENTIERE-EPISTRE-1539 | e-rara | public_domain (PDM) | Yes, with attribution | — |

## 3. Restrictions to respect now

1. **Do not download or redistribute Gallica or BVH images** into the repository. Only links and hashes of the
   images that were read are recorded (`data/raw/` stays git-ignored).
2. **Do not import BVH TEI text** until the licence conflict (NC-SA 4.0 vs NC-ND 2.0) is resolved in writing with
   BVH (bvh@univ-tours.fr). NC-ND would forbid adapted versions such as a re-transcription.
3. **Wikisource text is CC BY-SA 4.0.** If any of it is reused, the reuse inherits share-alike and requires
   attribution. Phase 2 drafts were made by reading the facsimile images. Wikisource was consulted only to compare readings.
4. **Non-commercial conditions** (Gallica images, BVH) are incompatible with a blanket permissive licence. The
   software licence (GPL-3.0) must not be assumed to cover corpus data (ADR 0005, proposed).

## 4. Actions for the project lead

- [ ] Decide the corpus-data licence and transcription-reuse policy (ADR 0005).
- [ ] Read the current Gallica CGU in a browser and record the date and wording here.
- [ ] Email BVH to resolve the Epistemon licence conflict (only if BVH TEI is wanted).
- [ ] Confirm that short diplomatic transcriptions made by the project from Gallica images may be stored in a public repository.
