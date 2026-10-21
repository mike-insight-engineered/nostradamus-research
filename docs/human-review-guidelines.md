# Human review guidelines

For qualified reviewers of sixteenth-century French and/or Renaissance Latin. Each package's
`README.md` gives the practical steps. This page gives the standards.

## What you judge

**Fidelity to the historical language (QC2).** Does the modern French/English say what the
sixteenth-century text says, in the senses those words had then, with its grammar correctly
analysed and its genuine ambiguities preserved?

You do **not** judge: literary elegance (beyond fluency errors), agreement with a translation you
know, or any interpretation of meaning beyond the text.

## Blinding

You will not be told which system produced an output. Do not try to infer it. Do not discuss items
with other reviewers until both of you have submitted.

## Procedure per item

1. Read the diplomatic transcription. Use the facsimile reference where given.
2. If the transcription is wrong, record a `transcription` error (QC1) and judge the translation
   against what the witness actually says, noting the issue.
3. Judge French and English separately: `acceptable`, `unacceptable` or `unresolvable`.
   - *Acceptable* means no error of major or critical severity. Minor errors are allowed.
   - *Unresolvable* means the source cannot be judged (damaged, irreducibly obscure).
4. Record every error: category, severity, target language, the span, and a note saying what is
   wrong and why.
5. Record legitimate alternative readings, even if the output chose one of them.
6. Flag genuine ambiguity (`ambiguity_flag`) and say whether the output handled it.
7. Give your confidence (1–5) and the references you **actually consulted** (dictionary, headword or
   page; edition). Never cite a work you did not consult.

## Severity guide

| Severity | Use when |
|---|---|
| critical | Reverses or wholly misrepresents the meaning; invents a named person, event or date |
| major | Changes meaning materially: wrong period sense, wrong tense or person affecting sense, omitted clause, unjustified resolution of a real ambiguity |
| minor | Small loss of nuance or an awkward rendering that does not mislead |
| neutral | A note that is not an error (e.g. a defensible choice worth recording) |

## Particular hazards

- **Diachronic false friends**: words whose modern sense differs from the sixteenth-century one.
  Check a period dictionary before accepting a modern sense.
- **Latinate syntax** in French (participial constructions, displaced verbs).
- **Code-switching**: a Latin phrase translated as if it were French, or vice versa.
- **Proper names and allusions**: classical, biblical or astrological names must not be modernised
  into specific later referents.
- **Interpretive drift**: any suggestion of prophecy, prediction or identification with later
  events is an `unsupported_addition` or `invented_specificity` error. Severity is normally critical.

## Data handling

Do not share package contents beyond the review team. Do not paste source texts or outputs into
external AI tools. Return the completed CSV or JSONL to the project lead.
