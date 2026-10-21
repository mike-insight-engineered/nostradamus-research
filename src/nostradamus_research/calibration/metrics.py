"""Calibration metrics over (stated confidence, reviewed correctness) pairs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

import numpy as np

from ..evaluation.statistics import wilson_interval


@dataclass(frozen=True)
class ReliabilityBin:
    lower: float
    upper: float
    count: int
    mean_confidence: float | None
    accuracy: float | None
    accuracy_low: float | None
    accuracy_high: float | None

    @property
    def gap(self) -> float | None:
        if self.mean_confidence is None or self.accuracy is None:
            return None
        return self.mean_confidence - self.accuracy


def _arrays(conf: Sequence[float], correct: Sequence[bool]) -> tuple[np.ndarray, np.ndarray]:
    if len(conf) != len(correct):
        raise ValueError("confidence and correctness must have the same length")
    c = np.asarray(conf, dtype=float)
    y = np.asarray(correct, dtype=float)
    if c.size and (np.any(c < 0) or np.any(c > 1)):
        raise ValueError("confidence values must lie in [0, 1]")
    return c, y


def reliability_bins(
    conf: Sequence[float],
    correct: Sequence[bool],
    *,
    n_bins: int = 10,
    strategy: Literal["uniform", "quantile"] = "uniform",
    confidence_level: float = 0.95,
) -> list[ReliabilityBin]:
    c, y = _arrays(conf, correct)
    if strategy == "uniform" or c.size == 0:
        edges = np.linspace(0.0, 1.0, n_bins + 1)
    else:
        edges = np.unique(np.quantile(c, np.linspace(0, 1, n_bins + 1)))
        edges[0], edges[-1] = 0.0, 1.0
    bins: list[ReliabilityBin] = []
    for i in range(len(edges) - 1):
        lo, hi = float(edges[i]), float(edges[i + 1])
        mask = (c >= lo) & ((c < hi) if i < len(edges) - 2 else (c <= hi))
        n = int(mask.sum())
        if n == 0:
            bins.append(ReliabilityBin(lo, hi, 0, None, None, None, None))
            continue
        k = int(y[mask].sum())
        w = wilson_interval(k, n, confidence_level)
        bins.append(ReliabilityBin(lo, hi, n, float(c[mask].mean()), k / n, w.low, w.high))
    return bins


def expected_calibration_error(bins: Sequence[ReliabilityBin]) -> float | None:
    n = sum(b.count for b in bins)
    if n == 0:
        return None
    return float(sum(abs(b.gap) * b.count / n for b in bins if b.gap is not None))


def max_calibration_error(bins: Sequence[ReliabilityBin]) -> float | None:
    gaps = [abs(b.gap) for b in bins if b.gap is not None]
    return max(gaps) if gaps else None


def brier_score(conf: Sequence[float], correct: Sequence[bool]) -> float | None:
    """Mean squared error of confidence treated as P(correct). Lower is better."""
    c, y = _arrays(conf, correct)
    return float(np.mean((c - y) ** 2)) if c.size else None


@dataclass(frozen=True)
class CoveragePoint:
    threshold: float
    coverage: float
    n_retained: int
    error_rate: float | None
    error_low: float | None
    error_high: float | None


def coverage_risk_curve(
    conf: Sequence[float], correct: Sequence[bool], *, confidence_level: float = 0.95
) -> list[CoveragePoint]:
    """Error rate among outputs retained when abstaining below each distinct threshold."""
    c, y = _arrays(conf, correct)
    n = c.size
    points: list[CoveragePoint] = []
    for t in sorted(set(c.tolist())):
        keep = c >= t
        m = int(keep.sum())
        errors = m - int(y[keep].sum())
        w = wilson_interval(errors, m, confidence_level)
        points.append(CoveragePoint(float(t), m / n, m, w.value, w.low, w.high))
    return points


def area_under_risk_coverage(points: Sequence[CoveragePoint]) -> float | None:
    """Trapezoidal AURC over coverage (lower is better)."""
    pts = sorted((p.coverage, p.error_rate) for p in points if p.error_rate is not None)
    if len(pts) < 2:
        return None
    # Explicit trapezoid rule (np.trapz/np.trapezoid differ across NumPy 1.x/2.x).
    return float(sum((x1 - x0) * (y0 + y1) / 2 for (x0, y0), (x1, y1) in pairwise(pts)))
