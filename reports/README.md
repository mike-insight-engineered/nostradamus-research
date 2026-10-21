# Reports

| Report | Generator | Template |
|---|---|---|
| A. Historical Source Audit | `nr sources audit --output reports/source-audit.md` | `templates/source-audit.md` |
| B. Translation Benchmark | `nr report benchmark --run ... [--reviews ...]` | `templates/benchmark-report.md` |
| C. Confidence Calibration | `nr calibrate report --run ... --reviews ...` | `templates/calibration-report.md` |
| D. Milestone Gate | `nr report milestone --output reports/milestone-1-readiness.md` | `templates/milestone-gate.md` |
| Reviewer instructions | written into each package by `nr review export` | `templates/human-review.md` |

Every generated report opens with an **evidence banner**: synthetic fixture data, automated metrics
only, non-expert review, or expert-reviewed. Never remove or edit the banner by hand, and never
present synthetic or mock results as research findings.

## Current reports

- `milestone-1-readiness.md`: software criteria passed; research criteria failed or not evaluated;
  recommendation **DEFER** (no verified data yet).
- `source-audit.md`: all registry records are unverified candidates.

Templates use `${placeholder}` syntax (Python `string.Template`). The sign-off tables at the end of
the audit and gate templates are completed by people, not software.
