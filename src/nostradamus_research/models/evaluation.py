"""Per-output evaluation records combining automated metrics and human review."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from .base import StrictModel
from .enums import CorpusCategory, DatasetSplit, EvidenceLevel, PipelineId, TargetLanguage


class EvaluationResult(StrictModel):
    evaluation_id: str
    run_id: str
    result_id: str
    passage_id: str
    pipeline: PipelineId
    category: CorpusCategory
    split: DatasetSplit
    target_language: TargetLanguage
    metrics: dict[str, float | None] = Field(
        default_factory=dict,
        description="Automated reference-based scores (e.g. chrF). Not proof of correctness.",
    )
    reference_ids: list[str] = Field(default_factory=list)
    n_references: int = 0
    mqm_penalty: float | None = Field(
        default=None, description="Mean MQM penalty per normalisation unit across reviewers."
    )
    mqm_error_counts: dict[str, int] = Field(default_factory=dict)
    human_acceptable: bool | None = None
    review_ids: list[str] = Field(default_factory=list)
    evidence_level: EvidenceLevel
    notes: list[str] = Field(default_factory=list)
    created_at: datetime
