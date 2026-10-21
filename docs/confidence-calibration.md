# Confidence calibration

## Terms (used consistently in code and reports)

- **Stated confidence:** a number in [0, 1] verbalised by the model (`confidence_source:
  model_stated`) or emitted by the mock (`mock_deterministic`). It is **not** a probability and is
  never treated as one without empirical checking.
- **Empirical correctness rate:** the share of outputs judged correct by reviewers (rule in
  [evaluation-framework.md](evaluation-framework.md)), with a Wilson interval.
- **Calibration:** how far stated confidence matches the empirical correctness rate.
- **Translation confidence ≠ interpretive confidence.** Nothing here speaks to the plausibility of
  any interpretation (QC3).

## No fabricated confidence

If a provider returns no meaningful confidence, `stated_confidence` is null and
`confidence_source` is `none`. A validator enforces this. Such outputs are counted and excluded from
calibration metrics; they are never imputed. Token log-probabilities are not used: they are not
available from every provider, and sequence-level probabilities do not equal translation
correctness.

## Metrics (`calibration/metrics.py`)

| Metric | Definition | Notes |
|---|---|---|
| Reliability bins | Uniform (default 5) or quantile bins; per bin: n, mean confidence, accuracy with Wilson CI, gap | Bins with n < 5 are flagged as unreliable |
| ECE | Σ (n_b / N) · \|acc_b − conf_b\| | Depends on binning; noisy at small N |
| MCE | max_b \|acc_b − conf_b\| | |
| Brier score | mean (conf − correct)² | Treats stated confidence *as if* it were P(correct) |
| Coverage–risk | For each threshold t: share retained, error rate among retained (Wilson CI) | Basis for abstention |
| AURC | Area under the risk–coverage curve (trapezoidal) | Lower is better |

## Abstention

`AbstentionPolicy(threshold)` answers only when stated confidence ≥ threshold, and abstains when
confidence is missing (default). `select_threshold` picks the lowest threshold meeting a target error
rate on **development/validation items only**. It refuses test items.

## Sample size

`calibration.min_items_for_calibration_claims` (default 50) is the minimum number of usable items
(confidence plus label) before a report may describe a model as calibrated or miscalibrated. Below
it, the report says the figures are descriptive only. Even at 80 passages × 4 pipelines, per-pipeline
calibration estimates remain imprecise. **Twenty held-out passages cannot establish a precise
accuracy rate:** 15/20 correct gives a Wilson 95% interval of about [0.53, 0.89].

## Procedure

1. Runs on development/validation → blinded review → `nr calibrate report` (descriptive).
2. Choose any abstention threshold on validation; record it in a decision record.
3. A single pre-registered test run → review → final calibration report with intervals.
