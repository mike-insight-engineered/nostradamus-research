# Source authentication policy

## Principle

**Discovering a digitised copy is not authenticating a printed witness.** A Gallica or BVH page shows
*an* exemplar of *some* edition. Before passages can be calibrated we need to know which edition, which
exemplar, and that our transcription matches it.

## Verification ladder

Statuses are cumulative and move **one rung at a time** (`nr sources promote`). Demotion or
`rejected` is always allowed with a reason. The rules are enforced in
`src/nostradamus_research/models/status_policy.py`.

| Status | Meaning | Required (in addition to lower rungs) |
|---|---|---|
| `candidate` | A plausible source has been identified | Nothing; list `outstanding_work` |
| `located` | A specific digitised or physical exemplar has been found and accessed | `stable_url` or `persistent_identifier` or `catalogue_identifier`; `date_accessed` |
| `provenance_checked` | The exemplar has been matched to a catalogued edition | Witness: `holding_institution`, `catalogue_identifier`, and `catalogue_record` evidence by a named person confirming edition, printer, place and date (title page, colophon, device, collation where practical). Non-witness resources: documented evidence of the resource's authority and terms. |
| `transcription_verified` | Passage transcriptions from this witness were checked against images | Witness only; `locator`; `transcription_check` evidence by a named person |
| `expert_reviewed` | A qualified expert has reviewed the witness and transcriptions | `expert_review` evidence by someone other than the transcription checker |
| `rejected` | Unsuitable or inauthentic | Reason in `notes` or `status_history` |

Passages have their own status. A passage may not be `transcription_verified` unless its source is at
least `provenance_checked` (checked by `nr corpus provenance`), and it must carry a locator, a
facsimile reference and a `transcription_checked` review event.

## Evidence quality

- Name the person (`verified_by`), never an AI system.
- Describe what was compared with what, and cite exact images or pages.
- Record discrepancies and residual uncertainty in `uncertainty_notes`.
- Prefer union catalogues (USTC) and holding-library catalogues (e.g. BnF) for edition identification.

## Rights

Text from the sixteenth century is public domain by age. **Digital facsimiles, modern
transcriptions, critical editions and translations may still carry rights.** Record `rights_status`.
Commit scans or extended text only with `public_domain`, `open_licence` or `permission_granted`.
Otherwise, keep material local (`data/raw/` is git-ignored) and store only identifiers and locators.

## Current state (2026-10-21)

The registry has 26 candidate records: 14 repositories and reference works, 12 witnesses. All are at
`candidate`. Bibliographic details were entered from general scholarly knowledge and have **not**
been checked against catalogues. No URL has been accessed for verification. See
`reports/source-audit.md`.
