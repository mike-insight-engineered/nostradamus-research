"""Human review records (blinded MQM-style annotation)."""

from __future__ import annotations

from datetime import date

from pydantic import Field, model_validator

from .base import StrictModel
from .enums import (
    ErrorCategory,
    ReviewerProvenance,
    ReviewJudgement,
    Severity,
    TargetLanguage,
)

SYNTHETIC_REVIEWER_PREFIX = "SYNTHETIC"


class MQMError(StrictModel):
    category: ErrorCategory
    severity: Severity
    target_language: TargetLanguage | None = Field(
        default=None, description="Which output the error is in; null for source-level errors."
    )
    span: str | None = None
    note: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)


class HumanReview(StrictModel):
    review_id: str
    review_item_id: str = Field(description="Blinded item ID from the review package.")
    package_id: str
    reviewer_id: str = Field(min_length=2)
    reviewer_provenance: ReviewerProvenance
    reviewed_on: date
    judgement_fr: ReviewJudgement | None = None
    judgement_en: ReviewJudgement | None = None
    errors: list[MQMError] = Field(default_factory=list)
    alternative_readings: list[str] = Field(default_factory=list)
    ambiguity_flag: bool = False
    unresolvable: bool = False
    reviewer_confidence: int | None = Field(default=None, ge=1, le=5)
    supporting_references: list[str] = Field(default_factory=list)
    comments: str | None = None
    time_spent_minutes: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check(self) -> HumanReview:
        syn_id = self.reviewer_id.upper().startswith(SYNTHETIC_REVIEWER_PREFIX)
        syn = self.reviewer_provenance is ReviewerProvenance.SYNTHETIC_FIXTURE
        if syn_id != syn:
            raise ValueError(
                "reviewer_id must start with 'SYNTHETIC' iff reviewer_provenance is synthetic_fixture"
            )
        if self.judgement_fr is None and self.judgement_en is None and not self.unresolvable:
            raise ValueError("a review needs judgement_fr, judgement_en, or unresolvable=true")
        return self
