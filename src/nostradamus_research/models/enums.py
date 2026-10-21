"""Controlled vocabularies shared across the data model."""

from __future__ import annotations

from enum import StrEnum


class VerificationStatus(StrEnum):
    """Provenance/verification ladder for sources, passages and lexical evidence.

    Statuses are cumulative: each rung requires the evidence of all lower rungs.
    Discovering a digitised copy (``located``) is *not* authentication of a
    particular printed witness (``provenance_checked``).
    """

    CANDIDATE = "candidate"
    LOCATED = "located"
    PROVENANCE_CHECKED = "provenance_checked"
    TRANSCRIPTION_VERIFIED = "transcription_verified"
    EXPERT_REVIEWED = "expert_reviewed"
    REJECTED = "rejected"


STATUS_LADDER: tuple[VerificationStatus, ...] = (
    VerificationStatus.CANDIDATE,
    VerificationStatus.LOCATED,
    VerificationStatus.PROVENANCE_CHECKED,
    VerificationStatus.TRANSCRIPTION_VERIFIED,
    VerificationStatus.EXPERT_REVIEWED,
)


def status_rank(status: VerificationStatus) -> int:
    """Position on the ladder; ``rejected`` ranks below ``candidate``."""
    if status is VerificationStatus.REJECTED:
        return -1
    return STATUS_LADDER.index(status)


class RecordType(StrEnum):
    WITNESS = "witness"  # a specific printed edition / manuscript copy
    DIGITAL_REPOSITORY = "digital_repository"  # e.g. Gallica, BVH
    REFERENCE_WORK = "reference_work"  # e.g. Huguet, DMF
    TEXT_CORPUS = "text_corpus"  # e.g. Frantext, Perseus


class Language(StrEnum):
    """Source languages (ISO 639-3 where available)."""

    MIDDLE_FRENCH = "frm"  # sixteenth-century / Middle French
    LATIN = "lat"
    OCCITAN = "oci"
    MIXED = "mixed"  # substantial code-switching, typically French/Latin
    OTHER = "other"


class TargetLanguage(StrEnum):
    MODERN_FRENCH = "fr"
    ENGLISH = "en"


class Genre(StrEnum):
    PROSE = "prose"
    VERSE = "verse"


class CorpusCategory(StrEnum):
    FRENCH_PROSE = "french_prose"
    FRENCH_POETRY = "french_poetry"
    LATIN_PROSE = "latin_prose"
    LATIN_VERSE = "latin_verse"
    MIXED = "mixed"


class PilotGroup(StrEnum):
    FRENCH_PROSE = "french_prose"
    FRENCH_POETRY = "french_poetry"
    LATIN = "latin"
    MIXED_OR_DIFFICULT = "mixed_or_difficult"


class RightsStatus(StrEnum):
    UNKNOWN = "unknown"
    PUBLIC_DOMAIN = "public_domain"
    OPEN_LICENCE = "open_licence"
    PERMISSION_GRANTED = "permission_granted"
    RESTRICTED = "restricted"
    NOT_PERMITTED = "not_permitted"


COMMITTABLE_RIGHTS = frozenset(
    {RightsStatus.PUBLIC_DOMAIN, RightsStatus.OPEN_LICENCE, RightsStatus.PERMISSION_GRANTED}
)


class DataOrigin(StrEnum):
    HISTORICAL_SOURCE = "historical_source"
    SYNTHETIC_FIXTURE = "synthetic_fixture"


class DatasetSplit(StrEnum):
    UNASSIGNED = "unassigned"
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    TEST = "test"


class PipelineId(StrEnum):
    A_DIRECT = "A_direct"
    B_TWO_STAGE = "B_two_stage"
    C_RETRIEVAL = "C_retrieval"
    D_STRUCTURED = "D_structured"


class EvidenceType(StrEnum):
    CATALOGUE_RECORD = "catalogue_record"
    DIGITAL_FACSIMILE = "digital_facsimile"
    TRANSCRIPTION_CHECK = "transcription_check"
    EXPERT_REVIEW = "expert_review"
    RIGHTS_CHECK = "rights_check"
    OTHER = "other"


class TranslatorType(StrEnum):
    HUMAN_EXPERT = "human_expert"
    PUBLISHED_EDITION = "published_edition"
    HUMAN_NON_EXPERT = "human_non_expert"
    MACHINE = "machine"
    SYNTHETIC_FIXTURE = "synthetic_fixture"


class ErrorCategory(StrEnum):
    """MQM-inspired error taxonomy adapted for historical-language translation."""

    MISTRANSLATION = "mistranslation"
    HISTORICAL_LEXICAL = "historical_lexical"
    GRAMMAR = "grammar"
    OMISSION = "omission"
    UNSUPPORTED_ADDITION = "unsupported_addition"
    LANGUAGE_IDENTIFICATION = "language_identification"
    LOST_AMBIGUITY = "lost_ambiguity"
    INVENTED_SPECIFICITY = "invented_specificity"
    NAMES_DATES = "names_dates"
    TRANSCRIPTION = "transcription"
    FLUENCY = "fluency"
    OTHER = "other"


class Severity(StrEnum):
    NEUTRAL = "neutral"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


SEVERITY_ORDER: tuple[Severity, ...] = (
    Severity.NEUTRAL,
    Severity.MINOR,
    Severity.MAJOR,
    Severity.CRITICAL,
)


class ReviewJudgement(StrEnum):
    ACCEPTABLE = "acceptable"
    UNACCEPTABLE = "unacceptable"
    UNRESOLVABLE = "unresolvable"


class ReviewerProvenance(StrEnum):
    EXPERT = "expert"
    NON_EXPERT = "non_expert"
    SYNTHETIC_FIXTURE = "synthetic_fixture"


class ConfidenceSource(StrEnum):
    """Where a confidence value came from. It is *never* a calibrated probability."""

    MODEL_STATED = "model_stated"  # verbalised by the model; uncalibrated
    MOCK_DETERMINISTIC = "mock_deterministic"  # synthetic, for software tests only
    NONE = "none"  # provider gave nothing meaningful; no value is imputed


class EvidenceLevel(StrEnum):
    """What kind of evidence a reported result rests on (strongest last)."""

    SYNTHETIC_FIXTURE = "synthetic_fixture"
    AUTOMATED_ONLY = "automated_only"
    HUMAN_NON_EXPERT = "human_non_expert"
    EXPERT_REVIEWED = "expert_reviewed"


class BacklogStatus(StrEnum):
    NOT_STARTED = "Not started"
    IN_PROGRESS = "In progress"
    BLOCKED = "Blocked"
    READY_FOR_REVIEW = "Ready for review"
    COMPLETE = "Complete"
