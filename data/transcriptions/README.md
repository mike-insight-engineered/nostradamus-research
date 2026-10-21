# data/transcriptions

Working transcriptions before they are imported as passages.

- One file per passage, named by the intended passage ID: `PSG-FP-0001.xml` (TEI) or `.txt`.
- Follow `docs/transcription-policy.md`: diplomatic, no silent expansion or correction.
- Import with a JSONL record that names the file in `tei_file`; the importer extracts the diplomatic
  layer and locks its hash:
  `uv run nr passages import new_passages.jsonl --by "Name" --dry-run`
- A transcription is not verified until a second person has checked it against the facsimile and
  that check is recorded (`transcription_checked` review event).

No transcriptions have been made yet.
