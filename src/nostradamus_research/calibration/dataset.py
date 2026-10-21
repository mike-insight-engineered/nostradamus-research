"""Assemble calibration items from translation results and linked reviews."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..config import CorrectnessConfig
from ..models.enums import ConfidenceSource, DatasetSplit, EvidenceLevel, PipelineId, TargetLanguage
from ..models.passage import Passage
from ..models.review import HumanReview
from ..models.translation import TranslationResult


@dataclass(frozen=True)
class CalibrationItem:
    result_id: str
    passage_id: str
    pipeline: PipelineId
    split: DatasetSplit
    confidence: float | None
    confidence_source: ConfidenceSource
    correct: bool | None
    evidence_level: EvidenceLevel


def build_items(
    results: list[TranslationResult],
    reviews_by_result: dict[str, list[HumanReview]],
    passages: dict[str, Passage],
    cfg: CorrectnessConfig,
) -> list[CalibrationItem]:
    from ..evaluation.evaluate import aggregate_labels, evidence_level, review_label

    items = []
    for r in results:
        p = passages.get(r.passage_id)
        if p is None:
            continue
        revs = reviews_by_result.get(r.result_id, [])
        langs = (
            [TargetLanguage.MODERN_FRENCH, TargetLanguage.ENGLISH]
            if cfg.target == "both"
            else [TargetLanguage(cfg.target)]
        )
        per_lang = [
            aggregate_labels([review_label(rv, lg, cfg) for rv in revs], cfg) for lg in langs
        ]
        correct = (
            None if any(v is None for v in per_lang) else all(v for v in per_lang if v is not None)
        )
        items.append(CalibrationItem(
            result_id=r.result_id, passage_id=r.passage_id, pipeline=r.pipeline, split=p.split,
            confidence=r.stated_confidence, confidence_source=r.confidence_source, correct=correct,
            evidence_level=evidence_level(p, revs),
        ))  # fmt: skip
    return items


def group_reviews(linked: list[object]) -> dict[str, list[HumanReview]]:
    out: dict[str, list[HumanReview]] = defaultdict(list)
    for lr in linked:
        out[lr.result_id].append(lr.review)  # type: ignore[attr-defined]
    return out
