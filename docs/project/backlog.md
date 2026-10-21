# Milestone 1 backlog

Machine-readable source: [`backlog.yaml`](backlog.yaml), validated by tests and cross-checked by
`nr report milestone`. **Software** and **research** workstreams are tracked separately. A template
or empty directory is never evidence of completion. Statuses: Not started · In progress · Blocked ·
Ready for review · Complete.

*Last updated: 2026-10-21 (Phase 2 remediation)*

| ID | Activity | Overall | Software | Research | Depends on |
|---|---|---|---|---|---|
| CAL-01 | Create repository research protocol and project configuration | Ready for review | Ready for review | Ready for review | — |
| CAL-02 | Establish historical source and licensing registers | In progress | Ready for review | In progress | CAL-01 |
| CAL-03 | Define sampling and dataset partition methodology | Ready for review | Ready for review | Ready for review | CAL-01 |
| CAL-04 | Establish translation review and evaluation rubric | Ready for review | Ready for review | Ready for review | CAL-01 |
| CAL-05 | Acquire five verified French prose passages | In progress | n/a | In progress | CAL-02 |
| CAL-06 | Acquire five verified French poetry passages | In progress | n/a | In progress | CAL-02 |
| CAL-07 | Acquire five verified Renaissance Latin passages | In progress | n/a | In progress | CAL-02 |
| CAL-08 | Acquire five verified multilingual or difficult passages | In progress | n/a | In progress | CAL-02 |
| CAL-09 | Obtain independent reference translations | In progress | n/a | In progress | CAL-05–08 |
| CAL-10 | Complete review of the initial 20-passage feasibility dataset | Not started | n/a | Not started | CAL-09 |
| CAL-11 | Expand the corpus to 80 verified passages | Not started | n/a | Not started | CAL-10 |
| CAL-12 | Benchmark four translation pipelines | Blocked | Ready for review | Blocked | CAL-10 |
| CAL-13 | Conduct independent error analysis and confidence calibration | Blocked | Ready for review | Blocked | CAL-12 |
| CAL-14 | Produce the milestone completion report and go/no-go decision | Blocked | Ready for review | Blocked | CAL-13 |

## Notes

- **CAL-01–04:** implemented by the initial software build; protocols and rubric need project-lead review and a
  reviewer pilot before they can be Complete.
- **CAL-02 (Phase 2):** 47 registry records: 24 `located` (digitised exemplar or resource accessed on 2026-10-21),
  23 `candidate`, **0 `provenance_checked`**. Rights are documented per layer in
  `research/pilot/source-licence-audit.md`. Open issues: `research/pilot/provenance-issues.md`.
- **CAL-05–08 (Phase 2):** 20 pilot slots in `data/candidates/pilot_candidates.jsonl` (5 per group). 10 have
  page-level locators. 4 AI-assisted **unverified** draft diplomatic transcriptions exist, one per group
  (`data/transcriptions/drafts/`). **No passage is verified, and none has been imported into the research corpus.**
- **CAL-09 (Phase 2):** availability matrix compiled from general knowledge (nothing located or licensed);
  translator brief prepared. No reference translation exists.
- **Remediation (2026-10-21):** split licensing adopted (software GPL-3.0-or-later; original docs and annotations CC BY 4.0;
  third-party material under its own terms). Rights matrix with URL, evidence and date; 20-slot quality audit;
  replacements proposed for MX-05 and LA-05; review packets for the four drafts; three published translations confirmed
  to exist (none licensed). Target 1 = FV-01, LA-01, FP-01, MX-01 (`research/pilot/acquisition-priorities.md`).
- **CAL-10:** not started; per-slot sheets, full packets for the four drafts, and the two-person protocol are ready.
- **CAL-12–14:** software is in place and runs end to end on synthetic fixtures with the mock provider.
  Research execution is blocked on verified data, references and paid-API authorisation.
