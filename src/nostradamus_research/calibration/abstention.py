"""Abstention policies: answer only above a confidence threshold.

Thresholds must be selected on development/validation data. Selecting a
threshold on held-out test items would turn the test set into a tuning set, so
:func:`select_threshold` refuses test-split items.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from ..models.enums import DatasetSplit
from .dataset import CalibrationItem


class TestSplitTuningError(PermissionError):
    __test__ = False  # not a pytest test class


@dataclass(frozen=True)
class AbstentionPolicy:
    threshold: float
    abstain_without_confidence: bool = True

    def decide(self, confidence: float | None) -> Literal["answer", "abstain"]:
        if confidence is None:
            return "abstain" if self.abstain_without_confidence else "answer"
        return "answer" if confidence >= self.threshold else "abstain"

    def evaluate(self, items: Sequence[CalibrationItem]) -> dict[str, float | int | None]:
        labelled = [i for i in items if i.correct is not None]
        answered = [i for i in labelled if self.decide(i.confidence) == "answer"]
        errors = sum(1 for i in answered if not i.correct)
        return {
            "threshold": self.threshold,
            "n_labelled": len(labelled),
            "n_answered": len(answered),
            "coverage": len(answered) / len(labelled) if labelled else None,
            "error_rate_when_answering": errors / len(answered) if answered else None,
        }


def select_threshold(
    items: Sequence[CalibrationItem], *, max_error_rate: float, min_coverage: float = 0.0
) -> float | None:
    """Lowest threshold whose retained error rate ≤ ``max_error_rate`` (dev/validation only)."""
    if any(i.split is DatasetSplit.TEST for i in items):
        raise TestSplitTuningError(
            "abstention thresholds may not be selected on held-out test items"
        )
    usable = [i for i in items if i.correct is not None and i.confidence is not None]
    if not usable:
        return None
    for t in sorted({i.confidence for i in usable if i.confidence is not None}):
        kept = [i for i in usable if i.confidence is not None and i.confidence >= t]
        err = sum(1 for i in kept if not i.correct) / len(kept)
        if err <= max_error_rate and len(kept) / len(usable) >= min_coverage:
            return t
    return None
