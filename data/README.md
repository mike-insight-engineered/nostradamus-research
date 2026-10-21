# Data

| Directory | Contents | Committed? |
|---|---|---|
| `sources/` | `source_registry.jsonl` (canonical registry), `source_candidates.csv` (generated with `nr sources export-csv`) | Yes |
| `raw/` | Facsimile images, PDFs, downloaded files | **No** (git-ignored) unless rights confirmed |
| `transcriptions/` | Working TEI/plain transcriptions before import | Yes, if rights permit |
| `reference_translations/` | Working files for reference translations before import | Yes, if rights permit |
| `processed/` | `passages.jsonl`: the canonical research corpus | Yes |
| `splits/` | Split plans and the pilot manifest | Yes |
| `annotations/` | `lexical_evidence.jsonl`, `reviews/`, `review_packages/` (keys are git-ignored) | Yes (except keys) |
| `candidates/` | Pilot candidate manifest (20 slots; candidates only) | Yes |
| `transcriptions/drafts/` | AI-assisted **unverified** drafts: `*.cleared.jsonl` (committable) and `*.pending-rights.jsonl` (git-ignored) | Cleared file only |
| `fixtures/` | **Synthetic** test/demo data (`SYN-` IDs) | Yes |

## Rules

- **Nothing in `fixtures/` is historical data.** Fixture texts are composed in imitation of period
  spelling for software testing. Synthetic records may never be copied into `sources/`,
  `processed/` or `annotations/`. `scripts/validate_repository.py` enforces this.
- **No fabricated data anywhere.** Every historical record must trace to a real, registered source.
- **Rights first.** Sixteenth-century texts are public domain, but scans, modern transcriptions,
  editions and translations may not be. Commit text only when `rights_status` is `public_domain`,
  `open_licence` or `permission_granted`.
- **Diplomatic transcriptions are locked by hash.** See `docs/transcription-policy.md`.
- Validate after every change: `uv run nr sources validate && uv run nr passages validate && uv run nr corpus provenance`.

Current state (2026-10-21, after Phase 2): the registry holds 24 `located` and 23 `candidate` records (none
`provenance_checked`). 20 pilot slots are listed in `candidates/`, and 4 unverified draft transcriptions are in
`transcriptions/drafts/` (1 cleared, 3 rights-pending). Licensing: `../DATA_LICENSE.md`. `processed/passages.jsonl` does not exist yet, and `annotations/lexical_evidence.jsonl` is empty.
