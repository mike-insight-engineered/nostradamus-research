"""Pydantic v2 data model. JSON Schemas in ``schemas/`` are generated from these classes."""

from pydantic import BaseModel

from .enums import (
    BacklogStatus,
    ConfidenceSource,
    CorpusCategory,
    DataOrigin,
    DatasetSplit,
    ErrorCategory,
    EvidenceLevel,
    EvidenceType,
    Genre,
    Language,
    PilotGroup,
    PipelineId,
    RecordType,
    ReviewerProvenance,
    ReviewJudgement,
    RightsStatus,
    Severity,
    TargetLanguage,
    TranslatorType,
    VerificationStatus,
)
from .evaluation import EvaluationResult
from .evidence import EvidenceKind, LexicalEvidence
from .experiment import ExperimentManifest, PromptTemplateRef
from .passage import (
    AmbiguityAnnotation,
    DifficultWord,
    HistoricalAssertion,
    LinguisticAnnotation,
    Passage,
    ProposedInterpretation,
    ReviewEvent,
    TextualVariant,
)
from .reference import ReferenceTranslation
from .review import HumanReview, MQMError
from .source import HistoricalSource, StatusChange, VerificationEvidence
from .translation import AlternativeReading, ProviderCallRecord, TokenUsage, TranslationResult

# Models published as JSON Schemas (file stem -> model).
SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "historical_source": HistoricalSource,
    "passage": Passage,
    "reference_translation": ReferenceTranslation,
    "translation_result": TranslationResult,
    "human_review": HumanReview,
    "evaluation_result": EvaluationResult,
    "experiment_manifest": ExperimentManifest,
    "lexical_evidence": LexicalEvidence,
}

__all__ = [
    "SCHEMA_MODELS",
    "AlternativeReading",
    "AmbiguityAnnotation",
    "BacklogStatus",
    "ConfidenceSource",
    "CorpusCategory",
    "DataOrigin",
    "DatasetSplit",
    "DifficultWord",
    "ErrorCategory",
    "EvaluationResult",
    "EvidenceKind",
    "EvidenceLevel",
    "EvidenceType",
    "ExperimentManifest",
    "Genre",
    "HistoricalAssertion",
    "HistoricalSource",
    "HumanReview",
    "Language",
    "LexicalEvidence",
    "LinguisticAnnotation",
    "MQMError",
    "Passage",
    "PilotGroup",
    "PipelineId",
    "PromptTemplateRef",
    "ProposedInterpretation",
    "ProviderCallRecord",
    "RecordType",
    "ReferenceTranslation",
    "ReviewEvent",
    "ReviewJudgement",
    "ReviewerProvenance",
    "RightsStatus",
    "Severity",
    "StatusChange",
    "TargetLanguage",
    "TextualVariant",
    "TokenUsage",
    "TranslationResult",
    "TranslatorType",
    "VerificationEvidence",
    "VerificationStatus",
]
