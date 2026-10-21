"""Historical source registry records (witnesses, repositories, reference works)."""

from __future__ import annotations

from datetime import date

from pydantic import Field, model_validator

from .base import SYNTHETIC_PREFIX, StrictModel
from .enums import (
    COMMITTABLE_RIGHTS,
    DataOrigin,
    EvidenceType,
    Genre,
    Language,
    RecordType,
    RightsStatus,
    VerificationStatus,
)
from .status_policy import source_status_problems

SOURCE_ID_PATTERN = r"^(SRC|RES|SYN)-[A-Z0-9][A-Z0-9\-]*$"


class VerificationEvidence(StrictModel):
    """One documented act of verification. Must name a real person or role."""

    evidence_type: EvidenceType
    supports_status: VerificationStatus
    description: str = Field(min_length=10, description="What was checked and how.")
    verified_by: str = Field(min_length=2)
    verified_on: date
    reference: str | None = Field(
        default=None, description="URL, catalogue number, image/page reference."
    )


class StatusChange(StrictModel):
    from_status: VerificationStatus
    to_status: VerificationStatus
    changed_by: str = Field(min_length=2)
    changed_on: date
    reason: str = Field(min_length=5)


class HistoricalSource(StrictModel):
    """A registered source. ``SRC-`` witnesses, ``RES-`` resources, ``SYN-`` fixtures."""

    source_id: str = Field(pattern=SOURCE_ID_PATTERN)
    record_type: RecordType
    data_origin: DataOrigin = DataOrigin.HISTORICAL_SOURCE
    title: str = Field(min_length=1)
    author: str | None = None
    work_id: str | None = None
    date_text: str | None = Field(default=None, description="As stated, e.g. '1532' or 'c. 1550'.")
    date_earliest: int | None = None
    date_latest: int | None = None
    languages: list[Language] = Field(default_factory=list)
    genres: list[Genre] = Field(default_factory=list)
    edition: str | None = None
    printer_publisher: str | None = None
    place_of_publication: str | None = None
    holding_institution: str | None = None
    catalogue_identifier: str | None = None
    stable_url: str | None = None
    persistent_identifier: str | None = None
    locator: str | None = Field(default=None, description="Exact page, folio or image reference.")
    scan_available: bool | None = None
    transcription_available: bool | None = None
    rights_status: RightsStatus = RightsStatus.UNKNOWN
    licence: str | None = None
    rights_notes: str | None = None
    verification_status: VerificationStatus = VerificationStatus.CANDIDATE
    verification_evidence: list[VerificationEvidence] = Field(default_factory=list)
    status_history: list[StatusChange] = Field(default_factory=list)
    date_accessed: date | None = None
    authenticity_notes: str | None = None
    uncertainty_notes: str | None = None
    outstanding_work: list[str] = Field(default_factory=list)
    notes: str | None = None

    @property
    def rights_permit_commit(self) -> bool:
        return self.rights_status in COMMITTABLE_RIGHTS

    @model_validator(mode="after")
    def _check(self) -> HistoricalSource:
        is_syn_id = self.source_id.startswith(SYNTHETIC_PREFIX)
        is_syn = self.data_origin is DataOrigin.SYNTHETIC_FIXTURE
        if is_syn_id != is_syn:
            raise ValueError(
                "source_id prefix 'SYN-' must be used if and only if data_origin is synthetic_fixture"
            )
        if (
            self.date_earliest is not None
            and self.date_latest is not None
            and self.date_earliest > self.date_latest
        ):
            raise ValueError("date_earliest must not be later than date_latest")
        problems = source_status_problems(self)
        if problems:
            raise ValueError(
                f"verification_status '{self.verification_status}' is not supported by the "
                "recorded evidence: " + "; ".join(problems)
            )
        return self
