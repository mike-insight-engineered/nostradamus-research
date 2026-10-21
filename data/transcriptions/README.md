# data/transcriptions

Working transcriptions before they are imported as passages.

- One file per passage, named by the intended passage ID: `PSG-FP-0001.xml` (TEI) or `.txt`.
- Follow `docs/transcription-policy.md`: diplomatic, no silent expansion or correction.
- Import with a JSONL record that names the file in `tei_file`; the importer extracts the diplomatic
  layer and locks its hash:
  `uv run nr passages import new_passages.jsonl --by "Name" --dry-run`
- A transcription is not verified until a second person has checked it against the facsimile and
  that check is recorded (`transcription_checked` review event).

`drafts/` holds 4 AI-assisted draft diplomatic transcriptions (Phase 2), made by reading facsimile images:
`pilot_draft_passages.cleared.jsonl` (LA-01, from a Public Domain Mark facsimile) and the git-ignored
`pilot_draft_passages.pending-rights.jsonl` (FP-01, FV-01, MX-01, from Gallica images). They are **UNVERIFIED** (status `candidate`) and must pass
`docs/transcription-verification-protocol.md` before import. Drafts made from Gallica images stay
rights-pending until the project lead confirms publication is permitted (`DATA_LICENSE.md` §3).
