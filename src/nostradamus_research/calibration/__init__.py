"""Confidence calibration: reliability, ECE, Brier, coverage-risk and abstention.

Terminology used throughout:

* **stated confidence** — a number the model verbalised (or the mock emitted).
  It is uncalibrated and is not a probability.
* **empirical correctness rate** — the fraction of outputs judged correct by
  reviewers, estimated with an interval.
* **calibration** — the comparison between the two.

No confidence value is ever imputed: outputs without stated confidence are
counted and reported separately.
"""
