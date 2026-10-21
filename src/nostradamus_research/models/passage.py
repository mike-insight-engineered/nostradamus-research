"""Canonical historical passage record.

Key integrity properties enforced here:

* ``diplomatic_transcription`` is stored exactly as transcribed and locked by
  ``diplomatic_sha256``; any later change breaks validation.
* A ``normalised_reading`` is a separate, optional, *editorial* layer and must
  list the normalisation rules that produced it (no silent modernisation).
* Verified historical assertions (QC1/QC2) and proposed interpretations (QC3)
  are stored in separate fields and never mixed.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from ..utils.hashing import sha256_text
from .base import SYNTHETIC_PREFIX, StrictModel
from .enums import (
    CorpusCategory,
    DataOrigin,
    DatasetSplit,
    Genre,
    Language,
    PilotGroup,
    TargetLanguage,
    VerificationStatus,
    status_rank,
)
from .reference import ReferenceTranslation

PASSAGE_ID_PATTERN = r"^(PSG|SYN-PSG)-[A-Z0-9][A-Z0-9\-]*$"


class TextualVariant(StrictModel):
    witness_id: str = Field(description="Source ID of the witness carrying this reading.")
    location: str = Field(description="Where in the passage the variant occurs.")
    reading: str
    notes: str | None = None


class DifficultWord(StrictModel):
    form: str = Field(description="Exact form as it appears in the diplomatic transcription.")
    lemma: str | None = None
    candidate_senses: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class LinguisticAnnotation(StrictModel):
    span: str
    annotation_type: Literal[
        "morphology", "syntax", "orthography", "code_switching", "metre", "other"
    ]
    description: str
    annotator: str
    evidence_ids: list[str] = Field(default_factory=list)


class AmbiguityAnnotation(StrictModel):
    span: str
    readings: list[str] = Field(min_length=2)
    resolution: Literal["unresolved", "resolved"] = "unresolved"
    resolution_basis: str | None = None
    annotator: str

    @model_validator(mode="after")
    def _check(self) -> AmbiguityAnnotation:
        if self.resolution == "resolved" and not self.resolution_basis:
            raise ValueError("a resolved ambiguity must state its resolution_basis")
        return self


class HistoricalAssertion(StrictModel):
    """A checked statement of fact about the text (QC1/QC2), with evidence."""

    statement: str
    evidence: list[str] = Field(min_length=1, description="Citations or registry/evidence IDs.")
    asserted_by: str
    status: Literal["verified", "disputed"]


class ProposedInterpretation(StrictModel):
    """A QC3 interpretive proposal. Never treated as established fact."""

    statement: str
    proposed_by: str
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    evidence_strength: Literal["unassessed", "weak", "moderate", "strong"] = "unassessed"
    quality_dimension: Literal["QC3"] = "QC3"


class ReviewEvent(StrictModel):
    on: date
    by: str
    action: Literal[
        "created",
        "transcription_checked",
        "reference_added",
        "annotated",
        "status_changed",
        "split_assigned",
        "comment",
    ]
    notes: str | None = None
    from_status: VerificationStatus | None = None
    to_status: VerificationStatus | None = None


def expected_category(language: Language, genre: Genre) -> CorpusCategory:
    if language is Language.MIDDLE_FRENCH:
        return CorpusCategory.FRENCH_PROSE if genre is Genre.PROSE else CorpusCategory.FRENCH_POETRY
    if language is Language.LATIN:
        return CorpusCategory.LATIN_PROSE if genre is Genre.PROSE else CorpusCategory.LATIN_VERSE
    return CorpusCategory.MIXED


def default_pilot_group(category: CorpusCategory) -> PilotGroup:
    return {
        CorpusCategory.FRENCH_PROSE: PilotGroup.FRENCH_PROSE,
        CorpusCategory.FRENCH_POETRY: PilotGroup.FRENCH_POETRY,
        CorpusCategory.LATIN_PROSE: PilotGroup.LATIN,
        CorpusCategory.LATIN_VERSE: PilotGroup.LATIN,
        CorpusCategory.MIXED: PilotGroup.MIXED_OR_DIFFICULT,
    }[category]


class Passage(StrictModel):
    passage_id: str = Field(pattern=PASSAGE_ID_PATTERN)
    source_id: str
    data_origin: DataOrigin = DataOrigin.HISTORICAL_SOURCE
    author_id: str | None = None
    author: str | None = None
    work_id: str = Field(min_length=1, description="Grouping key for leakage-safe splitting.")
    witness_id: str | None = Field(default=None, description="Edition/witness identifier.")
    language: Language
    secondary_languages: list[Language] = Field(default_factory=list)
    genre: Genre
    category: CorpusCategory
    pilot_group: PilotGroup | None = Field(
        default=None, description="Override, e.g. a hard French passage counted as difficult."
    )
    difficulty_flags: list[str] = Field(default_factory=list)
    date_text: str | None = None
    date_earliest: int | None = None
    date_latest: int | None = None

    # --- QC1: transcription layers -------------------------------------------------
    diplomatic_transcription: str = Field(
        min_length=1,
        description="Exact transcription; spelling, punctuation and abbreviations as printed.",
    )
    diplomatic_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    transcription_format: Literal["plain", "tei"] = "plain"
    transcribed_by: str | None = None
    typography_notes: str | None = None
    spelling_notes: str | None = None
    normalised_reading: str | None = Field(
        default=None, description="Editorial normalisation; never replaces the diplomatic text."
    )
    normalisation_rules: list[str] = Field(default_factory=list)
    normalised_by: str | None = None
    locator: str | None = Field(default=None, description="Page/folio/signature in the witness.")
    facsimile_reference: str | None = Field(
        default=None, description="Image URL or IIIF reference."
    )
    textual_variants: list[TextualVariant] = Field(default_factory=list)

    # --- QC2: linguistic layers ----------------------------------------------------
    difficult_words: list[DifficultWord] = Field(default_factory=list)
    linguistic_annotations: list[LinguisticAnnotation] = Field(default_factory=list)
    lexical_evidence_ids: list[str] = Field(default_factory=list)
    reference_translations: list[ReferenceTranslation] = Field(default_factory=list)
    ambiguities: list[AmbiguityAnnotation] = Field(default_factory=list)

    # --- Assertions vs interpretations (kept apart) --------------------------------
    historical_assertions: list[HistoricalAssertion] = Field(default_factory=list)
    proposed_interpretations: list[ProposedInterpretation] = Field(default_factory=list)

    # --- Workflow ---------------------------------------------------------------------
    verification_status: VerificationStatus = VerificationStatus.CANDIDATE
    split: DatasetSplit = DatasetSplit.UNASSIGNED
    review_history: list[ReviewEvent] = Field(default_factory=list)
    notes: str | None = None

    @property
    def effective_pilot_group(self) -> PilotGroup:
        return self.pilot_group or default_pilot_group(self.category)

    @property
    def group_key_author(self) -> str:
        return self.author_id or self.author or self.work_id

    def references_for(self, language: TargetLanguage) -> list[ReferenceTranslation]:
        return [r for r in self.reference_translations if r.target_language == language]

    @model_validator(mode="after")
    def _check(self) -> Passage:
        problems: list[str] = []
        is_syn = self.data_origin is DataOrigin.SYNTHETIC_FIXTURE
        if self.passage_id.startswith(SYNTHETIC_PREFIX) != is_syn:
            problems.append(
                "passage_id prefix 'SYN-' must be used iff data_origin is synthetic_fixture"
            )
        if self.source_id.startswith(SYNTHETIC_PREFIX) != is_syn:
            problems.append(
                "synthetic passages must cite SYN- sources and historical passages must not"
            )
        if sha256_text(self.diplomatic_transcription) != self.diplomatic_sha256:
            problems.append(
                "diplomatic_transcription does not match diplomatic_sha256 — the transcription "
                "has been modified since registration. Diplomatic text may only change through a "
                "documented correction (see docs/transcription-policy.md)."
            )
        expected = expected_category(self.language, self.genre)
        if self.category is not expected:
            problems.append(
                f"category '{self.category}' is inconsistent with language '{self.language}' "
                f"and genre '{self.genre}' (expected '{expected}')"
            )
        if self.normalised_reading is not None and not self.normalisation_rules:
            problems.append(
                "normalised_reading requires normalisation_rules (no silent normalisation)"
            )
        for ref in self.reference_translations:
            if ref.passage_id != self.passage_id:
                problems.append(f"reference {ref.reference_id} belongs to passage {ref.passage_id}")
            if (ref.data_origin is DataOrigin.SYNTHETIC_FIXTURE) != is_syn:
                problems.append(f"reference {ref.reference_id} data_origin differs from passage")
        ref_ids = [r.reference_id for r in self.reference_translations]
        if len(ref_ids) != len(set(ref_ids)):
            problems.append("duplicate reference_id within passage")
        if status_rank(self.verification_status) >= status_rank(
            VerificationStatus.TRANSCRIPTION_VERIFIED
        ):
            if not self.locator:
                problems.append("transcription_verified passages require a locator")
            if not self.facsimile_reference:
                problems.append("transcription_verified passages require a facsimile_reference")
            if not any(e.action == "transcription_checked" for e in self.review_history):
                problems.append(
                    "transcription_verified passages require a 'transcription_checked' review event"
                )
        if (
            self.date_earliest is not None
            and self.date_latest is not None
            and self.date_earliest > self.date_latest
        ):
            problems.append("date_earliest must not be later than date_latest")
        if problems:
            raise ValueError("; ".join(problems))
        return self
