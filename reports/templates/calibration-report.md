# Confidence Calibration Report

${banner}

Generated: ${generated_at}

Inputs:

${inputs}

${sufficiency}

**Terminology.** *Stated confidence* is a number the model verbalised (or the mock emitted). It is
not a probability. *Empirical correctness rate* is the share of outputs reviewers judged correct.
Calibration compares the two. Confidence sources in this analysis: ${confidence_sources}.

## 1. Confidence metrics

${metrics_table}

## 2. Reliability (confidence bins)

${reliability_table}

## 3. Coverage vs error (abstention analysis)

Abstaining on outputs below each threshold retains the listed share of outputs at the listed
error rate. Thresholds must be chosen on development/validation data, never on the test set.

${coverage_table}

## 4. Reliability observations

${observations}

## 5. Notes on the data

${notes}

## 6. Uncertainty and limitations

${limitations}
