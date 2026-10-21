"""Reference translations used as evaluation targets."""

from __future__ import annotations

from pydantic import Field, model_validator

from .base import SYNTHETIC_PREFIX, StrictModel
from .enums import DataOrigin, RightsStatus, TargetLanguage, TranslatorType


class ReferenceTranslation(StrictModel):
    """One legitimate reference translation. A passage may have several per language."""

    reference_id: str = Field(pattern=r"^(REF|SYN-REF)-[A-Z0-9][A-Z0-9\-]*$")
    passage_id: str
    target_language: TargetLanguage
    text: str = Field(min_length=1)
    data_origin: DataOrigin = DataOrigin.HISTORICAL_SOURCE
    translator: str = Field(min_length=2)
    translator_type: TranslatorType
    reviewer: str | None = None
    source_citation: str | None = Field(
        default=None, description="Published edition / page if taken from a publication."
    )
    rights_status: RightsStatus = RightsStatus.UNKNOWN
    licence: str | None = None
    independent_of_evaluated_models: bool = Field(
        description="False if any evaluated model or pipeline contributed to this text."
    )
    is_literal: bool | None = Field(
        default=None, description="True for a deliberately literal rendering."
    )
    notes: str | None = None

    @model_validator(mode="after")
    def _check(self) -> ReferenceTranslation:
        is_syn = self.data_origin is DataOrigin.SYNTHETIC_FIXTURE
        if self.reference_id.startswith(SYNTHETIC_PREFIX) != is_syn:
            raise ValueError(
                "reference_id prefix 'SYN-' must be used iff data_origin is synthetic_fixture"
            )
        if is_syn != (self.translator_type is TranslatorType.SYNTHETIC_FIXTURE):
            raise ValueError(
                "translator_type 'synthetic_fixture' must be used iff data_origin is synthetic_fixture"
            )
        if self.translator_type is TranslatorType.MACHINE and self.independent_of_evaluated_models:
            raise ValueError(
                "a machine-produced reference cannot be marked independent_of_evaluated_models"
            )
        if self.translator_type is TranslatorType.PUBLISHED_EDITION and not self.source_citation:
            raise ValueError("a published_edition reference requires source_citation")
        return self
