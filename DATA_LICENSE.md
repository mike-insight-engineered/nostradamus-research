# Research data, documentation and third-party material — licensing

The **software** is licensed GPL-3.0-or-later (see `LICENSE`, `NOTICE`). This file covers everything else.
No blanket licence applies to third-party historical material. Decision record:
[docs/decisions/0005-separate-software-and-data-licences.md](docs/decisions/0005-separate-software-and-data-licences.md).

## 1. Original project material — CC BY 4.0

Where the project controls the necessary rights, the following are licensed under
**Creative Commons Attribution 4.0 International** (full text: `LICENSES/CC-BY-4.0.txt`;
https://creativecommons.org/licenses/by/4.0/):

- project documentation and research notes in `docs/`, `research/` and `reports/`, and the README files;
- the project's own research annotations: selection rationales, linguistic-challenge notes, quality audits,
  provenance and rights notes, and status histories in `data/sources/` and `data/candidates/`;
- the synthetic test fixtures in `data/fixtures/` and `tests/fixtures/`.

Attribution: "nostradamus-research project (Michael Minto and contributors)", with a link to the repository.

**Exceptions inside CC BY 4.0 documents.** Short quotations from historical works, from catalogue records
or from institutional terms of use, which appear in these documents for identification or citation, are
not relicensed. They remain under their source's status (see §2).

## 2. Third-party material — its own terms, recorded per item

| Material | Status | Where recorded |
|---|---|---|
| Historical works (texts printed 1512–1560) | Public domain by age | `data/sources/source_registry.jsonl` (`rights_notes`) |
| BnF Catalogue général / data.bnf.fr descriptive metadata | **Licence Ouverte de l'État** (since 1 Jan 2014). Free reuse **citing the source and the retrieval date**. Retrieved 2026-10-21. | registry `catalogue_identifier`, `research/pilot/evidence/` |
| e-rara record metadata | Not separately licensed on the terms page; reproduced as factual bibliographic data with the DOI | registry, `research/pilot/evidence/` |
| Gallica / BnF facsimile images | Gallica's own conditions (current page not readable from our environment; BnF 2019 policy: free non-commercial use with attribution). **Not stored in this repository.** | `research/pilot/rights-provenance-matrix.md` |
| BVH / Epistemon images and TEI | Authorisation required for reproduction; transcription licence statements conflict. **Not stored.** | same |
| e-rara facsimiles (Public Domain Mark items) | Free for all uses, commercial included; source citation requested. **Images not stored**; only links. | same |
| Wikisource transcriptions | CC BY-SA 4.0. **Not stored** (consulted for comparison only) | same |
| Published modern translations | In copyright. **Not stored** unless licensed in writing | `research/pilot/reference-translation-matrix.md` |
| Commissioned reference translations | Licence to be granted by each translator in writing (proposed CC BY 4.0) | translation assignments |

## 3. Project transcriptions of historical texts

A diplomatic transcription made by the project reproduces a public-domain text. However, a transcription
made **from a facsimile whose reuse terms are conditional** (e.g. Gallica's non-commercial condition) is
treated as **rights-pending** until the project lead confirms that publication is permitted:

- rights-pending files carry `.pending-rights` in their name and are **git-ignored**;
- transcriptions made from Public Domain Mark facsimiles (e-rara) may be committed, with attribution to the
  holding institution and the DOI, and are licensed **CC BY 4.0** as project work.

The registry field `rights_status` governs whether text derived from a source may be committed:
`public_domain`, `open_licence` or `permission_granted` means yes; anything else means no.
