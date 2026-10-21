# Research questions

## Milestone 1 (QC1/QC2)

| ID | Question | Evidence | Pipelines |
|---|---|---|---|
| RQ1 | How often do AI translations of verified sixteenth-century French and Renaissance Latin passages meet expert acceptability, by category? | Blinded MQM review; Wilson intervals | A–D |
| RQ2 | Which error types dominate (historical lexical, grammar, lost ambiguity, invented specificity, language identification)? | MQM category distributions | A–D |
| RQ3 | Does translating through modern French (B) introduce English errors absent from the French? | Paired B−A comparison; reviewer error attribution | A, B |
| RQ4 | Does verified historical lexical evidence (C) reduce historical-lexical errors without adding unsupported claims? | MQM historical_lexical / unsupported_addition; cited-evidence flags | A, C |
| RQ5 | Does explicit structured analysis (D) improve grammatical accuracy and preservation of ambiguity? | MQM grammar / lost_ambiguity; alternatives offered vs reviewer-identified ambiguities | A, D |
| RQ6 | Is model-stated confidence informative about correctness? Can abstention cut error at acceptable coverage? | Reliability, ECE, Brier, coverage–risk (with stated sample limits) | A–D |
| RQ7 | How far do expert reviewers agree? This is the practical ceiling for automatic assessment. | κ, percent agreement, penalty correlation | — |
| RQ8 | How well do chrF (and optionally COMET) track expert judgements on period texts? | Correlation of metric with MQM/acceptability | A–D |
| RQ9 | Is performance higher on passages with widely available published translations (possible contamination)? | Stratified comparison (descriptive) | A–D |

## Later milestones (QC3; not addressed in M1)

- How do the earliest Nostradamus witnesses differ textually, and how stable are the readings (QC1)?
- How does calibrated translation of the quatrains differ from popular translations (QC2)?
- What evidence supports or undermines specific claims of anagram, wordplay or deliberate obscurity,
  and how should evidential strength be graded (QC3)?
- How did contemporary censorship and religious controversy shape the texts? Historical evidence
  only.
