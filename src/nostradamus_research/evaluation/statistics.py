"""Small-sample statistics: bootstrap and Wilson intervals.

With the sample sizes in Milestone 1 (tens of passages), intervals are wide.
Functions return ``None`` intervals below a minimum sample size rather than
reporting spuriously precise numbers.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class Estimate:
    value: float | None
    low: float | None
    high: float | None
    n: int
    method: str
    note: str | None = None

    def fmt(self, digits: int = 2) -> str:
        if self.value is None:
            return f"n/a (n={self.n})"
        if self.low is None or self.high is None:
            return (
                f"{self.value:.{digits}f} (n={self.n}; no interval: {self.note or 'n too small'})"
            )
        return (
            f"{self.value:.{digits}f} [{self.low:.{digits}f}, {self.high:.{digits}f}] (n={self.n})"
        )


def bootstrap_ci(
    values: Sequence[float],
    *,
    statistic: Callable[[np.ndarray], float] = lambda a: float(np.mean(a)),
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 12345,
    min_n: int = 5,
) -> Estimate:
    """Percentile bootstrap interval for ``statistic`` over ``values``."""
    arr = np.asarray([v for v in values if v is not None and not math.isnan(v)], dtype=float)
    n = len(arr)
    if n == 0:
        return Estimate(None, None, None, 0, "bootstrap", "no observations")
    point = statistic(arr)
    if n < min_n:
        return Estimate(point, None, None, n, "bootstrap", f"n < {min_n}")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_resamples, n))
    boot = np.array([statistic(arr[i]) for i in idx])
    alpha = (1 - confidence) / 2
    return Estimate(point, float(np.quantile(boot, alpha)), float(np.quantile(boot, 1 - alpha)), n,
                    f"percentile bootstrap ({n_resamples} resamples, {confidence:.0%})")  # fmt: skip


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> Estimate:
    """Wilson score interval for a binomial proportion (well-behaved at small n)."""
    if n == 0:
        return Estimate(None, None, None, 0, "wilson", "no observations")
    z = float(stats.norm.ppf(1 - (1 - confidence) / 2))
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return Estimate(
        p, max(0.0, centre - half), min(1.0, centre + half), n, f"Wilson {confidence:.0%}"
    )
