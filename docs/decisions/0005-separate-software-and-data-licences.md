# ADR 0005 — Separate the software licence from corpus-data, transcription and translation licences

**Status:** ACCEPTED by the project lead (decisions recorded 2026-10-21) · **Date:** 2026-10-21

## Context

The repository's `LICENSE` is GPL-3.0 and governs the **software**. The research corpus mixes material with
different and sometimes incompatible terms:

- public-domain historical works;
- facsimiles under library terms. For example, Gallica: non-commercial use free, commercial use licensed (BnF, 2019);
  e-rara: Public Domain Mark;
- third-party transcriptions: Wikisource CC BY-SA 4.0; BVH Epistemon CC BY-NC-SA 4.0 *or* CC BY-NC-ND 2.0
  (conflicting statements);
- the project's own diplomatic transcriptions, annotations and commissioned translations;
- published translations in copyright (licence required).

A single repository-wide licence cannot describe this accurately. Non-commercial and share-alike conditions
cannot be relicensed under GPL or a permissive licence.

## Options (for decision)

1. **Software GPL-3.0. Project-created data (transcriptions, annotations, commissioned translations) under CC BY 4.0.**
   Third-party material keeps its own licence, recorded per record. Material that cannot be redistributed is
   referenced by identifier only.
2. As 1, but project data under **CC BY-SA 4.0**. This is compatible with reusing Wikisource text, but requires
   share-alike from users.
3. Keep corpus data in a separate repository or dataset with its own licence and access controls.

## Proposed rules (whichever option is chosen)

- Add `DATA_LICENSE.md` describing the data licence and listing exceptions.
- Each source, passage and reference record carries its own rights fields; `rights_status` governs whether text
  may be committed.
- Commissioned translators grant an explicit licence in writing (see the translation brief).
- No Gallica or BVH images are committed. Only links, locators and image hashes are recorded.

## Consequences

Until this ADR is decided, Phase 2 draft transcriptions derived from Gallica images are kept in
`data/transcriptions/drafts/` and should **not be committed or published**. Transcriptions from e-rara (Public
Domain Mark) facsimiles have no such barrier beyond attribution.

## Decision (accepted)

1. Original software: **GPL-3.0-or-later**, subject to dependency compatibility (checked: MIT, BSD-3-Clause and
   Apache-2.0 only; no vendored code) and to copyright ownership (see the open question below).
2. Software and research-data licences are kept separate (`LICENSE`/`NOTICE` vs `DATA_LICENSE.md`).
3. No blanket licence for third-party historical source material.
4. **CC BY 4.0** only for original research annotations and documentation where the project controls the rights.
5. Third-party transcriptions, facsimiles, references and other data keep their individual licences and
   restrictions, recorded per record.
6. Material whose rights are not cleared is not committed (`*.pending-rights*` is git-ignored).

**Open question for the project lead:** copyright ownership of AI-assisted code and documentation. `NOTICE`
names "Michael Minto and contributors"; confirm that this reflects the intended ownership.
