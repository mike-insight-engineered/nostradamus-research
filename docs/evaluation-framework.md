# Evaluation framework

## Evidence hierarchy

1. **Blinded expert MQM review**: the primary evidence of translation quality.
2. **Non-expert review**: preliminary.
3. **Automated metrics** (chrF, chrF++, optional COMET): secondary, as a screening and consistency
   signal. A high chrF does not show a translation is correct. A low chrF does not show it is wrong
   (legitimate alternative wording, multiple references).
4. **Synthetic fixtures / mock output**: software testing only. Never evidence.

Every evaluation record and report states its `evidence_level`.

## MQM-inspired taxonomy (`evaluation/mqm.py`)

| Category | Dimension | Definition |
|---|---|---|
| `mistranslation` | accuracy | Target meaning differs from source meaning |
| `historical_lexical` | historical | Modern sense given where the period sense differs, or an unsupported period sense |
| `grammar` | linguistic | Historical morphology/syntax misanalysed (tense, case, agreement, word order), changing meaning |
| `omission` | accuracy | Source content missing |
| `unsupported_addition` | accuracy | Content not supported by the source |
| `language_identification` | linguistic | Source language or code-switch misidentified |
| `lost_ambiguity` | historical | Genuine ambiguity resolved without justification or record of alternatives |
| `invented_specificity` | historical | A person, place, date or event named that the source does not specify |
| `names_dates` | accuracy | Proper names, numerals or dates wrong |
| `transcription` | source | The problem lies in the transcription (QC1), not the translation |
| `fluency` | fluency | Target ungrammatical or unidiomatic |
| `other` | other | Describe in the note |

Severities and default weights (`config/evaluation.yaml`): neutral 0, minor 1, major 5, critical 25.
The penalty is normalised per 100 source words. Each error records the target language (or null for
source-level errors), span, note and supporting evidence.

## Correctness label (for acceptance rates and calibration)

Per reviewer and output language, an output is **correct** if the judgement is `acceptable` **and**
no error at or above `major` applies to that language. `unresolvable` items are excluded. Labels are
aggregated across reviewers with the `all_reviewers` rule (any reviewer's "incorrect" makes it
incorrect) or `majority`. With `target: both`, an output is correct only if both French and English
are correct.

## Automated metrics

- chrF (char order 6, β = 2) and chrF++ (word order 2) per output against **all** references for that
  language, via sacrebleu. Sentence BLEU is off by default; it is unreliable on short texts.
- Group means carry percentile-bootstrap 95% intervals (2000 resamples, fixed seed). No interval is
  given below n = 5.
- COMET: `uv sync --extra comet`, then `evaluation/metrics.py:comet_scores`. It needs a model
  download, is excluded from CI, and is multilingual-modern-trained, so its reliability on
  sixteenth-century source text is itself unknown.

## Blinded human evaluation

See [human-review-guidelines.md](human-review-guidelines.md). Packages hide pipeline, provider,
model and run. Items are shuffled with a seeded RNG, and the key is stored separately. Reviewers
see the source, the provenance summary and a facsimile reference. Known blinding limitation:
structural differences (e.g. whether alternatives are offered) can hint at the pipeline. Pipeline D's
analysis and B's intermediate French are therefore not shown.

## Agreement

Per output language: percent agreement, mean pairwise Cohen's κ on judgements, and Spearman
correlation of weighted error totals. Fewer than 10 multiply-reviewed items are flagged as unstable.
Disagreements should be adjudicated and the adjudication recorded, without overwriting the original
reviews.

## Pipeline comparison

Report per pipeline × language: chrF with CI, acceptance rate with Wilson CI, MQM penalty with CI,
and error distribution by category. Per-category results are descriptive. With 20–80 passages,
avoid significance claims. Describe differences whose intervals overlap as inconclusive.
