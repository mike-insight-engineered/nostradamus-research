# Milestone 1 backlog

Machine-readable source: [`backlog.yaml`](backlog.yaml), validated by tests and cross-checked by
`nr report milestone`. **Software** and **research** workstreams are tracked separately. A template
or empty directory is never evidence of completion. Statuses: Not started · In progress · Blocked ·
Ready for review · Complete.

*Last updated: 2026-10-21*

| ID | Activity | Overall | Software | Research | Depends on |
|---|---|---|---|---|---|
| CAL-01 | Create repository research protocol and project configuration | Ready for review | Ready for review | Ready for review | — |
| CAL-02 | Establish historical source and licensing registers | In progress | Ready for review | In progress | CAL-01 |
| CAL-03 | Define sampling and dataset partition methodology | Ready for review | Ready for review | Ready for review | CAL-01 |
| CAL-04 | Establish translation review and evaluation rubric | Ready for review | Ready for review | Ready for review | CAL-01 |
| CAL-05 | Acquire five verified French prose passages | Not started | n/a | Not started | CAL-02 |
| CAL-06 | Acquire five verified French poetry passages | Not started | n/a | Not started | CAL-02 |
| CAL-07 | Acquire five verified Renaissance Latin passages | Not started | n/a | Not started | CAL-02 |
| CAL-08 | Acquire five verified multilingual or difficult passages | Not started | n/a | Not started | CAL-02 |
| CAL-09 | Obtain independent reference translations | Not started | n/a | Not started | CAL-05–08 |
| CAL-10 | Complete review of the initial 20-passage feasibility dataset | Not started | n/a | Not started | CAL-09 |
| CAL-11 | Expand the corpus to 80 verified passages | Not started | n/a | Not started | CAL-10 |
| CAL-12 | Benchmark four translation pipelines | Blocked | Ready for review | Blocked | CAL-10 |
| CAL-13 | Conduct independent error analysis and confidence calibration | Blocked | Ready for review | Blocked | CAL-12 |
| CAL-14 | Produce the milestone completion report and go/no-go decision | Blocked | Ready for review | Blocked | CAL-13 |

## Notes

- **CAL-01–04:** implemented by the initial software build; protocols and rubric need project-lead
  review and a reviewer pilot before they can be Complete.
- **CAL-02:** 26 *candidate* records (14 repositories/reference works, 12 witnesses). None located or
  authenticated; licences unconfirmed.
- **CAL-05–08:** candidate witnesses are listed in `research/candidate-authors.md`. No passages
  selected or transcribed.
- **CAL-12–14:** software is in place and runs end to end on synthetic fixtures with the mock
  provider. Research execution is blocked on verified data, references and paid-API authorisation.
