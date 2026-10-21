# Progress log

Newest first. Record what was done, what evidence supports it, and what remains. Record paid-API
use with estimated and actual cost.

## 2026-10-21 — Phase 2 remediation: rights, candidate audit, reference-first planning, Git preparation

**Decisions recorded (project lead):** software GPL-3.0-or-later; software and data licences separate; no blanket
licence for third-party material; CC BY 4.0 only for original annotations and docs; per-item terms retained;
two local commits on a feature branch; no push; no uncleared material committed.

**Done:**
- Licensing: `pyproject.toml` `license = "GPL-3.0-or-later"`; `NOTICE` (dependency licences: MIT, BSD-3-Clause,
  Apache-2.0; no vendored code); `DATA_LICENSE.md`; `LICENSES/CC-BY-4.0.txt` (official text); ADR 0005 accepted;
  README and CLAUDE.md updated; `*.pending-rights*` git-ignored.
- Rights matrix with URL, evidence type and date (`research/pilot/rights-provenance-matrix.md`). READ: BnF metadata
  under the Licence Ouverte (data.bnf.fr) and e-rara terms (PDM includes commercial use). Gallica CGU still unread
  (HTTP 403, also via Wayback).
- Corrections: the MX-01 line-end loss is caused by binding in the original digitisation, not by a Commons crop;
  MX-02 is unusable because of compression.
- Registry: 50 records (26 located, 24 candidate, 0 provenance_checked). Added Hypnérotomachie 1546 (MX-05
  replacement), Atrocianus 1528 (LA-05 replacement), and Thierry 1564 (rejected: microfiche).
- 20-slot candidate-quality audit; audit flags and proposed replacements in the manifest.
- Reference availability report: Finch 2010, Helgerson 2006 and Miller 1979 confirmed to exist (none licensed;
  Miller follows the ASD critical text, not 1512). Four translation assignments.
- Review packets for the four drafts (LA-01 committable; FP-01, FV-01, MX-01 rights-pending, local only).
- Acquisition priorities (Target 1 = FV-01, LA-01, FP-01, MX-01) and a list of human actions.

**Still zero:** authenticated witnesses, verified transcriptions, reference translations, human reviews. Gate: DEFER.

**Paid API use:** none.

## 2026-10-21 — Phase 2: historical source discovery and candidate pilot corpus (CAL-02, CAL-05–CAL-10)

**Method and access conditions:** Gallica returned HTTP 403 to the research environment, and the BVH XTF/TEI
server was unreachable. Discovery therefore used fr.wikisource (16th-century index), Wikimedia Commons, e-rara, and
the BnF Catalogue général SRU API. Each Gallica scan was matched to a BnF catalogue record through its field-856
link. All observations are recorded in `research/pilot/` with evidence snapshots.

**Done:**
- Registry: 47 records (24 `located`, 23 `candidate`, **0 `provenance_checked`**). 4 witness records updated and
  18 witness or resource records added. Imprints, collations and holdings come from retrieved records.
  Discrepancies are recorded, not resolved.
- 20-slot pilot candidate manifest (5/5/5/5): 19 distinct witnesses and 18 distinct works. 10 slots have
  page-level locators. Same-work overlaps are flagged (LA-02/LA-05, LA-01/MX-04).
- 4 **AI-assisted, unverified** draft diplomatic transcriptions made by reading facsimile images (one per group).
  The image hashes are recorded. The drafts are kept out of `data/processed/` until a human verifies them.
- Layered source and licence audit. A BnF 2019 press release on image reuse was read; the BVH licence conflict
  (CC BY-NC-SA 4.0 vs CC BY-NC-ND 2.0) was found; e-rara Public Domain Mark confirmed per record; Wikisource
  CC BY-SA 4.0 confirmed.
- Reference translation matrix (general knowledge only; nothing located), translator brief, transcription
  verification queue, 20 per-slot review sheets (`scripts/build_transcription_review_packets.py`), two-person
  verification protocol, and ADR 0005 (separate software and data licences; proposed).
- Tests for manifest and draft integrity (`tests/unit/test_research_artifacts.py`). The registry test now enforces
  "nothing above `located` without human evidence".

**Not done / blockers:** no human verification of any transcription; no catalogue_record evidence by a named
person; no USTC numbers; current Gallica terms not read; no reference translations; Louise Labé and
Occitan-influenced texts not yet located; MX-05 (Meigret) has only a second-generation witness.

**Paid API use:** none.

## 2026-10-21 — Initial implementation of the Milestone 1 software foundation

**Done (software, ready for review):**
- Packaging (`pyproject.toml`, `uv.lock`, Python 3.12), CI workflow, Makefile, issue/PR templates,
  Claude Code agents and skills.
- Data model (Pydantic v2) with integrity validators; 8 JSON Schemas generated.
- Source registry with a status ladder and one-rung promotion; provenance audit.
- Corpus I/O, dataset hashing, stats vs targets, grouped seeded splitting with test lock, leakage
  checks, pilot selection.
- Transcription safeguards (hash lock, recorded normalisation, TEI export/import), passage importer.
- Linguistic heuristics and local evidence retrieval (abstains without verified evidence).
- Provider layer (mock, Anthropic, OpenAI) with retry, rate limiting, redaction, cost metadata and a
  triple paid-call guard.
- Pipelines A–D with five versioned prompt templates (v1.0.0), guardrails and an experiment runner
  that writes manifests and the test-access ledger.
- Evaluation (MQM taxonomy, chrF/chrF++, optional COMET, bootstrap/Wilson, blinded review packages,
  import, agreement, staging comparison) and calibration (reliability, ECE, Brier, coverage–risk,
  abstention).
- Reports: source audit, benchmark, calibration, milestone gate; templates in `reports/templates/`.
- Typer CLI `nr`; scripts; offline demo on 12 synthetic passages.
- Tests: offline unit and integration suite.

**Done (research, partial):**
- 26 candidate source records (CAL-02 in progress). None verified.

**Not done / next:**
- CAL-05–08: locate and authenticate witnesses; select and transcribe 20 passages.
- CAL-09: independent reference translations.
- Confirm licensing for BVH, Gallica, Frantext, Perseus and Huguet.
- Project-lead review of protocols (CAL-01, 03, 04) and confirmation of ADRs 0001–0004.

**Known limitations of the implementation:** see `research/open-issues.md`.
