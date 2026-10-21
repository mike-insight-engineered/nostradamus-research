"""Historical lexical evidence used by retrieval-augmented pipelines.

Entries must cite a real, checkable source. Nothing in this repository creates
dictionary entries automatically: every historical entry is added by a person
and is only treated as *verified* once a named verifier has checked the
citation against the source.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import Field, model_validator

from .base import SYNTHETIC_PREFIX, StrictModel
from .enums import DataOrigin, Language, RightsStatus, VerificationStatus, status_rank


class EvidenceKind(StrEnum):
    DICTIONARY_ENTRY = "dictionary_entry"
    PERIOD_USAGE = "period_usage"
    GRAMMAR_REFERENCE = "grammar_reference"
    LITERARY_EXAMPLE = "literary_example"


class LexicalEvidence(StrictModel):
    evidence_id: str = Field(pattern=r"^(LEX|SYN-LEX)-[A-Z0-9][A-Z0-9\-]*$")
    data_origin: DataOrigin = DataOrigin.HISTORICAL_SOURCE
    kind: EvidenceKind
    headword: str = Field(min_length=1)
    variant_forms: list[str] = Field(default_factory=list)
    language: Language
    sense: str = Field(min_length=1, description="Gloss/sense as given by the cited source.")
    citation: str = Field(min_length=5, description="Full bibliographic citation of the source.")
    source_id: str | None = Field(default=None, description="Registry ID of the cited resource.")
    locator: str | None = None
    quotation: str | None = Field(default=None, description="Exact quotation, if rights permit.")
    url: str | None = None
    rights_status: RightsStatus = RightsStatus.UNKNOWN
    verification_status: VerificationStatus = VerificationStatus.CANDIDATE
    verified_by: str | None = None
    verified_on: date | None = None
    notes: str | None = None

    @property
    def all_forms(self) -> list[str]:
        return [self.headword, *self.variant_forms]

    @model_validator(mode="after")
    def _check(self) -> LexicalEvidence:
        is_syn = self.data_origin is DataOrigin.SYNTHETIC_FIXTURE
        if self.evidence_id.startswith(SYNTHETIC_PREFIX) != is_syn:
            raise ValueError(
                "evidence_id prefix 'SYN-' must be used iff data_origin is synthetic_fixture"
            )
        if status_rank(self.verification_status) >= status_rank(
            VerificationStatus.LOCATED
        ) and not (self.locator or self.url):
            raise ValueError("evidence at 'located' or above requires a locator or url")
        if status_rank(self.verification_status) >= status_rank(
            VerificationStatus.TRANSCRIPTION_VERIFIED
        ) and not (self.verified_by and self.verified_on):
            raise ValueError(
                "verified lexical evidence requires verified_by and verified_on "
                "(a named person who checked the citation against the source)"
            )
        return self
