"""Translation pipeline outputs and provider call metadata."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, model_validator

from .base import StrictModel
from .enums import ConfidenceSource, DataOrigin, PipelineId


class TokenUsage(StrictModel):
    input_tokens: int | None = None
    output_tokens: int | None = None


class ProviderCallRecord(StrictModel):
    """Metadata for one provider call. Prompt text is stored only as a hash by default."""

    call_id: str
    stage: str
    provider: str
    model: str
    task: str
    prompt_template_id: str
    prompt_version: str
    prompt_sha256: str
    temperature: float | None
    max_tokens: int
    started_at: datetime
    duration_seconds: float
    attempts: int = 1
    usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_usd: float | None = None
    cost_note: str | None = None
    response_id: str | None = None
    stop_reason: str | None = None
    error: str | None = None


class AlternativeReading(StrictModel):
    span: str
    readings: list[str] = Field(min_length=1)
    note: str | None = None


RetrievalStatus = Literal[
    "not_applicable",
    "verified_evidence",
    "unverified_or_synthetic_evidence",
    "no_evidence",
]


class TranslationResult(StrictModel):
    result_id: str
    run_id: str
    passage_id: str
    pipeline: PipelineId
    provider: str
    model: str
    is_mock: bool
    data_origin: DataOrigin
    source_text_sha256: str
    translation_fr: str | None = None
    translation_en: str | None = None
    intermediate_fr: str | None = Field(
        default=None,
        description="Pipeline B: the modern French text that was translated to English.",
    )
    analysis: dict[str, Any] | None = Field(
        default=None, description="Pipeline D: structured linguistic analysis."
    )
    retrieved_evidence_ids: list[str] = Field(default_factory=list)
    retrieval_status: RetrievalStatus = "not_applicable"
    alternatives: list[AlternativeReading] = Field(default_factory=list)
    unresolved_ambiguities: list[str] = Field(default_factory=list)
    stated_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model-stated, UNCALIBRATED confidence. Never an empirical probability.",
    )
    confidence_source: ConfidenceSource = ConfidenceSource.NONE
    limitations: list[str] = Field(default_factory=list)
    guardrail_flags: list[str] = Field(default_factory=list)
    parse_errors: list[str] = Field(default_factory=list)
    error: str | None = None
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    calls: list[ProviderCallRecord] = Field(default_factory=list)
    created_at: datetime

    @property
    def succeeded(self) -> bool:
        return self.error is None and (
            self.translation_fr is not None or self.translation_en is not None
        )

    @model_validator(mode="after")
    def _check(self) -> TranslationResult:
        if (self.stated_confidence is None) != (self.confidence_source is ConfidenceSource.NONE):
            raise ValueError(
                "stated_confidence must be null exactly when confidence_source is 'none' "
                "(confidence is never imputed)"
            )
        if self.is_mock and self.confidence_source is ConfidenceSource.MODEL_STATED:
            raise ValueError("mock results cannot carry model_stated confidence")
        return self
