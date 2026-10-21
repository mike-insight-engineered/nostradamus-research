"""End-to-end calibration analysis with explicit sample-size caveats."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from ..config import CalibrationConfig
from ..evaluation.statistics import Estimate, wilson_interval
from ..models.enums import EvidenceLevel
from .dataset import CalibrationItem
from .metrics import (
    CoveragePoint,
    ReliabilityBin,
    area_under_risk_coverage,
    brier_score,
    coverage_risk_curve,
    expected_calibration_error,
    max_calibration_error,
    reliability_bins,
)


@dataclass
class CalibrationAnalysis:
    n_items: int
    n_labelled: int
    n_with_confidence: int
    n_usable: int
    confidence_sources: dict[str, int]
    evidence_levels: dict[str, int]
    accuracy: Estimate
    mean_stated_confidence: float | None
    bins: list[ReliabilityBin] = field(default_factory=list)
    ece: float | None = None
    mce: float | None = None
    brier: float | None = None
    coverage: list[CoveragePoint] = field(default_factory=list)
    aurc: float | None = None
    sufficient_sample: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def weakest_evidence(self) -> EvidenceLevel | None:
        order = list(EvidenceLevel)
        present = [EvidenceLevel(k) for k in self.evidence_levels]
        return min(present, key=order.index) if present else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_items": self.n_items, "n_labelled": self.n_labelled,
            "n_with_confidence": self.n_with_confidence, "n_usable": self.n_usable,
            "confidence_sources": self.confidence_sources, "evidence_levels": self.evidence_levels,
            "empirical_correctness_rate": {"value": self.accuracy.value, "low": self.accuracy.low,
                                           "high": self.accuracy.high, "n": self.accuracy.n},
            "mean_stated_confidence": self.mean_stated_confidence,
            "ece": self.ece, "mce": self.mce, "brier": self.brier, "aurc": self.aurc,
            "bins": [b.__dict__ for b in self.bins],
            "coverage_risk": [c.__dict__ for c in self.coverage],
            "sufficient_sample": self.sufficient_sample, "notes": self.notes,
        }  # fmt: skip


def analyse(
    items: list[CalibrationItem], cfg: CalibrationConfig, confidence_level: float = 0.95
) -> CalibrationAnalysis:
    labelled = [i for i in items if i.correct is not None]
    usable = [i for i in labelled if i.confidence is not None]
    conf = [float(i.confidence) for i in usable if i.confidence is not None]
    correct = [bool(i.correct) for i in usable]
    k = sum(1 for i in labelled if i.correct)
    res = CalibrationAnalysis(
        n_items=len(items),
        n_labelled=len(labelled),
        n_with_confidence=sum(1 for i in items if i.confidence is not None),
        n_usable=len(usable),
        confidence_sources=dict(Counter(str(i.confidence_source) for i in items)),
        evidence_levels=dict(Counter(str(i.evidence_level) for i in items)),
        accuracy=wilson_interval(k, len(labelled), confidence_level),
        mean_stated_confidence=(sum(conf) / len(conf)) if conf else None,
    )
    if usable:
        res.bins = reliability_bins(conf, correct, n_bins=cfg.n_bins, strategy=cfg.binning,
                                    confidence_level=confidence_level)  # fmt: skip
        res.ece = expected_calibration_error(res.bins)
        res.mce = max_calibration_error(res.bins)
        res.brier = brier_score(conf, correct)
        res.coverage = coverage_risk_curve(conf, correct, confidence_level=confidence_level)
        res.aurc = area_under_risk_coverage(res.coverage)
    res.sufficient_sample = len(usable) >= cfg.min_items_for_calibration_claims
    if not res.sufficient_sample:
        res.notes.append(
            f"Only {len(usable)} usable (confidence + label) items; at least "
            f"{cfg.min_items_for_calibration_claims} are required before any calibration claim. "
            "All figures are descriptive and highly uncertain."
        )
    missing_conf = len(labelled) - len(usable)
    if missing_conf:
        res.notes.append(
            f"{missing_conf} labelled outputs had no stated confidence; no value was imputed and "
            "they are excluded from calibration metrics."
        )
    if "mock_deterministic" in res.confidence_sources:
        res.notes.append(
            "Confidence values come from the MOCK provider (synthetic); they mean nothing."
        )
    if "model_stated" in res.confidence_sources:
        res.notes.append(
            "Model-stated confidence is a verbalised self-assessment, not a calibrated probability."
        )
    return res
