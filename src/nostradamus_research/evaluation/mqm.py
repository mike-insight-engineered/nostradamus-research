"""MQM-inspired error taxonomy adapted to historical-language translation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from ..models.enums import SEVERITY_ORDER, ErrorCategory, Severity
from ..models.review import MQMError


@dataclass(frozen=True)
class CategoryInfo:
    dimension: str
    description: str


TAXONOMY: dict[ErrorCategory, CategoryInfo] = {
    ErrorCategory.MISTRANSLATION: CategoryInfo(
        "accuracy", "Target meaning differs from the source meaning."
    ),
    ErrorCategory.HISTORICAL_LEXICAL: CategoryInfo(
        "historical",
        "A word is given its modern sense where the period sense differs "
        "(faux ami diachronique), or a period sense is unsupported.",
    ),
    ErrorCategory.GRAMMAR: CategoryInfo(
        "linguistic",
        "Historical morphology or syntax misanalysed (e.g. tense, case, agreement, "
        "word order), changing meaning.",
    ),
    ErrorCategory.OMISSION: CategoryInfo("accuracy", "Source content is missing from the target."),
    ErrorCategory.UNSUPPORTED_ADDITION: CategoryInfo(
        "accuracy", "Target contains content not supported by the source."
    ),
    ErrorCategory.LANGUAGE_IDENTIFICATION: CategoryInfo(
        "linguistic", "Source language or code-switch misidentified (e.g. Latin read as French)."
    ),
    ErrorCategory.LOST_AMBIGUITY: CategoryInfo(
        "historical",
        "A genuine ambiguity in the source is resolved without justification or "
        "without recording the alternatives.",
    ),
    ErrorCategory.INVENTED_SPECIFICITY: CategoryInfo(
        "historical", "Target names a person, place, date or event the source does not specify."
    ),
    ErrorCategory.NAMES_DATES: CategoryInfo(
        "accuracy", "Proper names, numerals or dates rendered incorrectly."
    ),
    ErrorCategory.TRANSCRIPTION: CategoryInfo(
        "source", "The error originates in the transcription (QC1), not the translation."
    ),
    ErrorCategory.FLUENCY: CategoryInfo("fluency", "Target is ungrammatical or unidiomatic."),
    ErrorCategory.OTHER: CategoryInfo("other", "Any other issue; describe in the note."),
}

_ALIASES = {
    "addition": ErrorCategory.UNSUPPORTED_ADDITION,
    "lexical": ErrorCategory.HISTORICAL_LEXICAL,
    "grammatical": ErrorCategory.GRAMMAR,
    "names": ErrorCategory.NAMES_DATES,
    "dates": ErrorCategory.NAMES_DATES,
    "language_id": ErrorCategory.LANGUAGE_IDENTIFICATION,
    "ambiguity": ErrorCategory.LOST_AMBIGUITY,
    "specificity": ErrorCategory.INVENTED_SPECIFICITY,
}


class TaxonomyError(ValueError):
    pass


def parse_category(value: str) -> ErrorCategory:
    v = value.strip().lower().replace("-", "_").replace(" ", "_")
    try:
        return ErrorCategory(v)
    except ValueError:
        if v in _ALIASES:
            return _ALIASES[v]
    raise TaxonomyError(
        f"unknown MQM category {value!r}; valid: {[c.value for c in ErrorCategory]}"
    )


def parse_severity(value: str) -> Severity:
    try:
        return Severity(value.strip().lower())
    except ValueError:
        raise TaxonomyError(
            f"unknown severity {value!r}; valid: {[s.value for s in Severity]}"
        ) from None


def severity_at_least(severity: Severity, threshold: Severity) -> bool:
    return SEVERITY_ORDER.index(severity) >= SEVERITY_ORDER.index(threshold)


def penalty(
    errors: Iterable[MQMError],
    weights: Mapping[Severity, float],
    *,
    source_words: int,
    per_words: int = 100,
) -> float:
    """Weighted error penalty normalised per ``per_words`` source words (lower is better)."""
    if source_words <= 0:
        raise ValueError("source_words must be positive")
    total = sum(weights.get(e.severity, 0.0) for e in errors)
    return total * per_words / source_words


def category_counts(errors: Iterable[MQMError]) -> dict[str, int]:
    return dict(sorted(Counter(str(e.category) for e in errors).items()))


def dimension_counts(errors: Iterable[MQMError]) -> dict[str, int]:
    return dict(sorted(Counter(TAXONOMY[e.category].dimension for e in errors).items()))
