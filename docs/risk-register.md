# Risk register

Likelihood (L) and impact (I): 1 = low, 3 = high. Reviewed at each gate.

| ID | Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|---|
| R01 | Fabricated or unverified data enters the corpus (transcriptions, citations, references) | 2 | 3 | Validators (status evidence, `SYN-` rules, hash lock); provenance audit; `CLAUDE.md` rules; review of every data PR | Lead |
| R02 | Digitised copy mistaken for an authenticated witness | 2 | 3 | Status ladder; catalogue-record evidence required for `provenance_checked` | Source verifier |
| R03 | Transcription errors propagate into translation scores | 2 | 3 | Second-person check against facsimile; `transcription` MQM category separates QC1 from QC2 | Transcriber/checker |
| R04 | Expert translators or reviewers unavailable or costly | 3 | 3 | Early recruitment; use rights-cleared published translations where possible; keep pilot small | Lead |
| R05 | Rights restrictions on facsimiles, transcriptions or translations | 3 | 2 | Record rights per record; store identifiers only; `data/raw` ignored by Git | Source verifier |
| R06 | Test-set leakage through prompt tuning or repeated evaluation | 2 | 3 | Test lock, explicit flag and reason, ledger, threshold-selection guard, pre-registration | Research engineer |
| R07 | Pretraining contamination inflates performance | 3 | 2 | Documented limitation; prefer less-reproduced passages; compare passages with and without published translations | Lead |
| R08 | Lexical metrics over-interpreted | 2 | 2 | Evidence banners; human MQM as primary evidence | Evaluator |
| R09 | Verbal confidence mistaken for probability | 2 | 2 | Terminology; no imputation; sample-size threshold for claims | Evaluator |
| R10 | Translation drifts into prophetic interpretation | 2 | 3 | Prompt rules; guardrail flags; reviewer guidance (critical severity) | Translation developer |
| R11 | Unplanned API spend | 1 | 2 | Triple guard (config + flag + env key); dry runs report call counts; pricing recorded | Lead |
| R12 | Commercial model changes break reproducibility | 3 | 2 | Record returned model IDs and dates; store outputs; compare, don't assume identity | Research engineer |
| R13 | Small samples produce misleading pipeline rankings | 3 | 2 | Intervals everywhere; descriptive framing; pilot is not powered to rank | Evaluator |
| R14 | Heuristic linguistic pre-analysis misleads pipeline D | 2 | 1 | Labelled non-authoritative; model told to correct it; reviewers judge outputs only | Translation developer |
| R15 | Credentials leaked | 1 | 3 | Keys only from env; redaction; `.gitignore`; secret scan in `validate_repository.py` and CI | Research engineer |
