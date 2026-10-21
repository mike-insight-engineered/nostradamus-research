# nostradamus-research

Build a small, independently validated dataset to discover whether AI models preserve the historical meaning, grammar, and ambiguity of French and Latin texts comparable to those Nostradamus could have encountered. Compare alternative translation pipelines under reproducible conditions and document weaknesses.

> **Status (2026-10-21): software foundation ready for review; no historical calibration has taken place yet.**
> The framework runs end to end on *synthetic fixtures* with a *mock* provider. No source has been
> authenticated, no verified passage or independent reference translation exists, and no expert
> review has been carried out. See [reports/milestone-1-readiness.md](reports/milestone-1-readiness.md).

## 1. Research objectives

The long-term aim is historically rigorous modern French and English translations of the quatrains
of Michel de Nostredame (Nostradamus), and a disciplined assessment of interpretations of them. Before
any of that, we must establish whether AI translation of **sixteenth-century French and Renaissance
Latin** into modern French and English is reliable. Interpreting ambiguous, possibly deliberately
obscure text is meaningless without that foundation. Claims of deliberate encoding are to be
investigated, never assumed.

Three quality dimensions are kept separate throughout:

| | Dimension | Milestone 1 |
|---|---|---|
| **QC1** | Fidelity of transcription to historical source witnesses | in scope |
| **QC2** | Fidelity of translation to the historical language | in scope |
| **QC3** | Evidential strength of later interpretations | architecture only |

## 2. Historical and linguistic scope

Sixteenth-century French prose and poetry, Renaissance Latin prose and verse, and mixed French/Latin
passages: historical spelling and typography, morphology and syntax, period lexical senses,
Occitan/Provençal influence, and classical, biblical, astrological and mythological reference.
Nostradamus's own texts are deliberately **not** part of the calibration corpus.

## 3. Milestone 1 goals

A reproducible calibration framework, then a **20-passage feasibility study** (5 French prose, 5 French
poetry, 5 Latin, 5 mixed/difficult), followed after a gate by an **80-passage corpus** (30/20/15/5/10)
partitioned 48/12/20 into development, validation and held-out test sets by work group. Four
translation pipelines are compared: **A** direct, **B** two-stage via modern French, **C**
retrieval-augmented, **D** structured linguistic analysis. The milestone ends with an auditable
go/no-go decision. Details: [docs/milestone-1-execution-plan.md](docs/milestone-1-execution-plan.md).

## 4. Repository organisation

| Path | Contents |
|---|---|
| `src/nostradamus_research/` | Python package: `models/` (Pydantic data model), `provenance/` (registry, status policy, audit), `corpus/` (I/O, stats, splits, leakage, pilot), `ingestion/`, `transcription/` (normalisation safeguards, TEI), `linguistics/` (heuristics, local retrieval), `translation/` (pipelines A–D, prompts, providers, runner), `evaluation/` (MQM, chrF, review packages, agreement), `calibration/`, `reporting/`, `cli.py` |
| `config/` | `project.yaml`, `corpus.yaml`, `translation.yaml`, `evaluation.yaml`, `providers.example.yaml` |
| `data/` | `sources/` registry (candidates only), `fixtures/` (**synthetic**), placeholders for transcriptions, references, processed corpus, splits, annotations |
| `schemas/` | JSON Schemas generated from the models |
| `docs/` | Charter, methodology, policies, protocols, risk register, decisions, backlog |
| `experiments/` | Per-pipeline experiment notes; `runs/` holds run outputs and manifests |
| `reports/` | Report templates and generated reports |
| `research/` | Bibliography, acquisition plan, resources, candidate authors, questions, open issues |
| `scripts/` | Bootstrap, validation, schema generation, pilot manifest, review export, benchmark, calibration |
| `tests/` | Offline unit and integration tests |

## 5. Installation

Requires [uv](https://docs.astral.sh/uv/); uv installs Python 3.12 if needed.

```bash
uv sync --extra providers        # core + dev tools + Anthropic/OpenAI SDKs (SDKs make no calls by themselves)
uv run python scripts/bootstrap.py
```

Optional COMET (installs PyTorch; never needed for tests): `uv sync --extra comet`.

## 6. Offline demonstration (synthetic, zero cost)

```bash
uv run nr demo                      # writes experiments/runs/demo/ (git-ignored)
uv run nr translate mock --pipeline D --limit 2
```

The demo validates the fixtures, splits them, runs all four pipelines with the deterministic mock
provider, computes chrF, exports a blinded review package, generates **synthetic** reviews (labelled
`SYNTHETIC-REVIEWER-*`), and produces benchmark, calibration and source-audit reports. Every output
carries a *SYNTHETIC FIXTURE DATA — NOT RESEARCH EVIDENCE* banner. The fixture texts are written in an
imitation of period style for testing. They are not historical texts.

## 7. Validating a corpus

```bash
uv run nr config validate
uv run nr sources validate               # registry incl. evidence required by each status
uv run nr sources audit --output reports/source-audit.md
uv run nr passages import new.jsonl --by "Your Name" --dry-run
uv run nr passages validate              # schema, transcription hash, category, status evidence
uv run nr corpus provenance              # passages vs registry and rights
uv run nr corpus stats                   # progress vs pilot/full targets
uv run nr corpus split --dry-run         # group-isolated 48/12/20 (scaled) partitions
uv run nr corpus leakage                 # duplicates, cross-split sharing, retrieval/test overlap
uv run python scripts/validate_repository.py
```

## 8. Running translation experiments

```bash
uv run nr translate run --pipeline A --provider mock --split development --dry-run
uv run python scripts/run_benchmark.py --provider mock --split development           # dry run of A–D
```

Every run writes `experiments/runs/<run_id>/results.jsonl` and `manifest.json` (git commit, config
hashes, `uv.lock` hash, dataset hash, prompt template IDs/versions/hashes, provider/model, token use
and cost where known). Held-out test passages require `--allow-test-split --test-reason "..."`, and
each such run is appended to `experiments/runs/test_access_ledger.jsonl`.

**Paid runs** need *all* of: `config/providers.yaml` with `enabled: true` and a real model ID, the API
key in the environment (see `.env.example`), and `--allow-paid-api`. Nothing else ever calls a paid
API.

## 9. Human review

```bash
uv run nr review export --run experiments/runs/<RUN_A> --run experiments/runs/<RUN_B> --package-id PKG-001
# reviewers complete data/annotations/review_packages/PKG-001/review_sheet.csv
uv run nr review import path/to/review_sheet.csv --key data/annotations/review_packages/PKG-001-KEY/key.json
uv run nr review agreement data/annotations/reviews/PKG-001.jsonl
```

Packages are shuffled and blinded. Pipeline, provider and model appear only in the separate `-KEY`
file. Guidance: [docs/human-review-guidelines.md](docs/human-review-guidelines.md).

## 10. Evaluation reports

```bash
uv run nr evaluate metrics --run <RUN> --reviews <REVIEWS> --output <DIR>
uv run nr report benchmark --run <RUN> ... --reviews <REVIEWS> --output reports/benchmark.md
uv run nr calibrate report --run <RUN> ... --reviews <REVIEWS> --output reports/calibration.md
uv run nr report milestone --output reports/milestone-1-readiness.md
```

## 11. Privacy and API cost

- No API keys in files; keys come only from environment variables, and logs redact key-like strings.
- Prompt and response bodies are **not** logged by default (only hashes and lengths).
- Installation, CI, tests and the demo make **no** network or paid calls.
- Costs are reported only if you enter current prices in `providers.yaml`; otherwise "unknown".
- Source texts are public domain by age, but **digital facsimiles, transcriptions and modern
  translations may not be**. Do not commit them until rights are confirmed (see `data/README.md`).

## 12. Research limitations

- chrF measures surface similarity to references. It does not establish correctness, so human MQM review is the primary evidence.
- Model-stated confidence is a verbalised self-assessment, not a probability. It is never imputed when absent.
- With 20 held-out passages, accuracy intervals are wide: a Wilson 95% interval for 15/20 is about
  [0.53, 0.89]. No precise accuracy rate can be claimed.
- Pretraining contamination (models having seen these texts or translations) cannot be ruled out.
- The language-identification and morphology heuristics are aids only.

## 13. Next milestones

1. **CAL-05–CAL-08:** locate, authenticate and transcribe 20 pilot passages.
2. **CAL-09:** commission or license independent reference translations.
3. **CAL-10:** blinded expert review of the pilot, followed by the feasibility gate.
4. **CAL-11–CAL-14:** expand to 80 passages, benchmark A–D, calibrate, then decide go/no-go.
5. Milestone 2 (only after a "continue" decision): Nostradamus witnesses and QC3 interpretation.

See [docs/project/backlog.md](docs/project/backlog.md) and [docs/project/milestones.md](docs/project/milestones.md).

## Development

```bash
make check     # or: uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest && uv run python scripts/validate_repository.py
```

Tests marked `external` (none required today; reserved for COMET or live-provider smoke tests) are
excluded by default; run them with `uv run pytest -m external`.

## Licensing

- **Software** (code, scripts, tests, configuration): **GPL-3.0-or-later**. See `LICENSE` and `NOTICE`.
- **Original documentation and research annotations:** **CC BY 4.0** where the project holds the rights
  (`LICENSES/CC-BY-4.0.txt`).
- **Third-party material** (historical texts, facsimiles, catalogue metadata, transcriptions, translations):
  its own terms, recorded per item. No blanket licence applies. See [DATA_LICENSE.md](DATA_LICENSE.md).
- Rights-pending material is git-ignored (`*.pending-rights*`) and never committed.

Contributors: read [CLAUDE.md](CLAUDE.md) first.
