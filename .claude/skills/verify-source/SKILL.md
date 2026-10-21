---
name: verify-source
description: Workflow for moving one registered historical source one rung up the verification ladder (candidate → located → provenance_checked → transcription_verified → expert_reviewed) with recorded evidence. Use when the user wants to verify, locate or authenticate a source.
---

# Verify a source (one rung at a time)

1. `uv run nr sources list` and pick the `source_id`. Read its record and `outstanding_work`.
2. Determine the next rung and its requirements (see `docs/source-authentication.md`):
   - **located**: a stable URL / ARK / catalogue ID that you actually opened, plus `date_accessed`.
   - **provenance_checked**: holding institution, catalogue identifier, and `catalogue_record`
     evidence by a *named person* matching edition, printer, place and date.
   - **transcription_verified**: witness only; locator; `transcription_check` evidence by a named
     person against facsimile images.
   - **expert_reviewed**: `expert_review` evidence by an expert who is not the transcription checker.
3. Gather evidence. Record only what was observed. Unknown fields stay null.
4. Draft `evidence.json` (a list of VerificationEvidence objects) and optionally `updates.json`.
5. Dry run:
   `uv run nr sources promote <ID> --to <status> --by "<Person>" --reason "<why>" --evidence-json evidence.json --updates-json updates.json --dry-run`
6. **Stop and show the user.** Only the named person may approve the real promotion (same command
   without `--dry-run`).
7. Regenerate the CSV: `uv run nr sources export-csv`; update `docs/project/progress-log.md`.

Never put an AI system in `verified_by`. Never skip rungs. Never commit facsimiles without rights.
