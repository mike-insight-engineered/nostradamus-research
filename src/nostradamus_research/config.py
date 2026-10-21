"""Typed configuration loaded from ``config/*.yaml``.

Every section forbids unknown keys so that typos fail loudly. Provider
configuration is read from ``config/providers.yaml`` (git-ignored, created by
copying ``providers.example.yaml``); when absent, the example file is used, in
which every paid provider is disabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .models.enums import CorpusCategory, PilotGroup, Severity
from .utils.hashing import sha256_file
from .utils.jsonl import format_validation_error
from .utils.paths import find_repo_root, resolve


class _Cfg(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConfigError(ValueError):
    """Raised for missing or invalid configuration, with readable messages."""


# --- project.yaml -------------------------------------------------------------------


class ProjectInfo(_Cfg):
    name: str
    title: str
    milestone: str
    milestone_title: str
    quality_dimensions: dict[str, str]


class PathsConfig(_Cfg):
    source_registry: str
    source_candidates: str
    passages: str
    lexical_evidence: str
    splits_dir: str
    runs_dir: str
    reports_dir: str
    report_templates_dir: str
    schemas_dir: str
    fixtures_dir: str
    backlog: str
    test_access_ledger: str


class IntegrityConfig(_Cfg):
    forbid_synthetic_in_corpus: bool = True
    require_diplomatic_hash: bool = True


class ProjectConfig(_Cfg):
    project: ProjectInfo
    paths: PathsConfig
    integrity: IntegrityConfig = Field(default_factory=IntegrityConfig)


# --- corpus.yaml --------------------------------------------------------------------


class CorpusTargets(_Cfg):
    full_corpus: dict[CorpusCategory, int]
    pilot: dict[PilotGroup, int]


class SplitConfig(_Cfg):
    seed: int
    group_by: Literal["work_id", "author"] = "work_id"
    targets: dict[Literal["development", "validation", "test"], int]

    @model_validator(mode="after")
    def _check(self) -> SplitConfig:
        if set(self.targets) != {"development", "validation", "test"}:
            raise ValueError("splits.targets must define development, validation and test")
        if any(v < 0 for v in self.targets.values()):
            raise ValueError("split targets must be non-negative")
        return self


class InclusionConfig(_Cfg):
    minimum_passage_status: str = "transcription_verified"
    minimum_references_per_language: int = 1


class LeakageConfig(_Cfg):
    near_duplicate_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    shingle_size: int = Field(default=5, ge=2)


class NormalisationConfig(_Cfg):
    default_rules: list[str] = Field(default_factory=list)


class CorpusConfig(_Cfg):
    targets: CorpusTargets
    splits: SplitConfig
    inclusion: InclusionConfig = Field(default_factory=InclusionConfig)
    leakage: LeakageConfig = Field(default_factory=LeakageConfig)
    normalisation: NormalisationConfig = Field(default_factory=NormalisationConfig)


# --- translation.yaml ---------------------------------------------------------------


class GenerationConfig(_Cfg):
    temperature: float | None = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=16)


class PipelineToggle(_Cfg):
    enabled: bool = True
    top_k: int | None = Field(default=None, ge=1)


class RetrievalConfig(_Cfg):
    minimum_evidence_status: str = "transcription_verified"
    allow_synthetic_evidence: bool = False
    top_k: int = Field(default=5, ge=1)


class TranslationConfig(_Cfg):
    default_provider: str = "mock"
    prompt_versions: dict[str, str]
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    pipelines: dict[str, PipelineToggle]
    include_normalised_reading: bool = False
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    flag_speculative_interpretation: bool = True
    held_out_requires_explicit_flag: bool = True


# --- evaluation.yaml ----------------------------------------------------------------


class MQMConfig(_Cfg):
    severity_weights: dict[Severity, float]
    per_source_words: int = Field(default=100, ge=1)


class ChrfConfig(_Cfg):
    char_order: int = 6
    word_order: int = 0
    beta: int = 2


class CometConfig(_Cfg):
    enabled: bool = False
    model: str = "Unbabel/wmt22-comet-da"


class MetricsConfig(_Cfg):
    chrf: ChrfConfig = Field(default_factory=ChrfConfig)
    chrf_plus_plus: bool = True
    sentence_bleu: bool = False
    comet: CometConfig = Field(default_factory=CometConfig)


class StatisticsConfig(_Cfg):
    bootstrap_resamples: int = Field(default=2000, ge=100)
    confidence_level: float = Field(default=0.95, gt=0.5, lt=1.0)
    min_n_for_bootstrap: int = Field(default=5, ge=2)
    seed: int = 12345


class CorrectnessConfig(_Cfg):
    target: Literal["fr", "en", "both"] = "both"
    unacceptable_at_or_above: Severity = Severity.MAJOR
    exclude_unresolvable: bool = True
    aggregation: Literal["all_reviewers", "majority"] = "all_reviewers"


class CalibrationConfig(_Cfg):
    n_bins: int = Field(default=5, ge=2)
    binning: Literal["uniform", "quantile"] = "uniform"
    min_items_for_calibration_claims: int = Field(default=50, ge=1)


class ReviewConfig(_Cfg):
    blinding_seed: int = 777
    min_reviewers_per_item: int = Field(default=2, ge=1)


class AgreementConfig(_Cfg):
    min_items_for_estimate: int = Field(default=10, ge=2)


class EvaluationConfig(_Cfg):
    mqm: MQMConfig
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    statistics: StatisticsConfig = Field(default_factory=StatisticsConfig)
    correctness: CorrectnessConfig = Field(default_factory=CorrectnessConfig)
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    agreement: AgreementConfig = Field(default_factory=AgreementConfig)


# --- providers.yaml -----------------------------------------------------------------


class PricingConfig(_Cfg):
    input_usd_per_million_tokens: float | None = None
    output_usd_per_million_tokens: float | None = None


class ProviderConfig(_Cfg):
    type: Literal["mock", "anthropic", "openai"]
    model: str
    enabled: bool = False
    api_key_env: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    timeout_seconds: float = 120.0
    max_retries: int = Field(default=4, ge=0)
    initial_backoff_seconds: float = Field(default=2.0, ge=0)
    max_backoff_seconds: float = Field(default=60.0, ge=0)
    requests_per_minute: float | None = Field(default=None, gt=0)
    pricing: PricingConfig = Field(default_factory=PricingConfig)

    @model_validator(mode="after")
    def _check(self) -> ProviderConfig:
        if self.type != "mock" and not self.api_key_env:
            raise ValueError(
                "non-mock providers must name api_key_env (keys are never stored in config)"
            )
        return self


class ProviderLogging(_Cfg):
    log_prompts: bool = False
    log_responses: bool = False


class ProvidersConfig(_Cfg):
    providers: dict[str, ProviderConfig]
    logging: ProviderLogging = Field(default_factory=ProviderLogging)


# --- loading ------------------------------------------------------------------------

CONFIG_FILES = {
    "project": "project.yaml",
    "corpus": "corpus.yaml",
    "translation": "translation.yaml",
    "evaluation": "evaluation.yaml",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"missing configuration file: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    return data


def _validate[C: BaseModel](model: type[C], data: dict[str, Any], path: Path) -> C:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        details = "\n  ".join(format_validation_error(exc))
        raise ConfigError(f"{path}: invalid configuration:\n  {details}") from exc


@dataclass(frozen=True)
class AppConfig:
    root: Path
    project: ProjectConfig
    corpus: CorpusConfig
    translation: TranslationConfig
    evaluation: EvaluationConfig

    def path(self, name: str) -> Path:
        """Resolve a named path from ``project.yaml`` against the repository root."""
        return resolve(self.root, getattr(self.project.paths, name))

    def file_hashes(self) -> dict[str, str]:
        return {
            stem: sha256_file(self.root / "config" / fname) for stem, fname in CONFIG_FILES.items()
        }


def load_config(root: Path | None = None) -> AppConfig:
    root = root or find_repo_root()
    cfg_dir = root / "config"
    p = {k: cfg_dir / v for k, v in CONFIG_FILES.items()}
    return AppConfig(
        root=root,
        project=_validate(ProjectConfig, _load_yaml(p["project"]), p["project"]),
        corpus=_validate(CorpusConfig, _load_yaml(p["corpus"]), p["corpus"]),
        translation=_validate(TranslationConfig, _load_yaml(p["translation"]), p["translation"]),
        evaluation=_validate(EvaluationConfig, _load_yaml(p["evaluation"]), p["evaluation"]),
    )


def providers_config_path(root: Path) -> Path:
    local = root / "config" / "providers.yaml"
    return local if local.is_file() else root / "config" / "providers.example.yaml"


def load_providers(root: Path, path: Path | None = None) -> ProvidersConfig:
    path = path or providers_config_path(root)
    return _validate(ProvidersConfig, _load_yaml(path), path)
