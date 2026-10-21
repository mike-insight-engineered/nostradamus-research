"""Experiment manifests: everything needed to reproduce a run."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from .base import StrictModel
from .enums import DatasetSplit, EvidenceLevel, PipelineId


class PromptTemplateRef(StrictModel):
    template_id: str
    version: str
    sha256: str


class ExperimentManifest(StrictModel):
    run_id: str
    created_at: datetime
    status: Literal["completed", "failed", "dry_run", "partial"]
    description: str | None = None
    pipeline: PipelineId
    provider: str
    model: str
    is_mock: bool
    provider_params: dict[str, Any] = Field(default_factory=dict)
    prompt_templates: list[PromptTemplateRef] = Field(default_factory=list)
    dataset_path: str
    dataset_sha256: str
    passage_ids: list[str]
    splits_included: list[DatasetSplit]
    test_split_accessed: bool = False
    test_access_reason: str | None = None
    data_origin_counts: dict[str, int] = Field(default_factory=dict)
    evidence_level: EvidenceLevel
    config_sha256: dict[str, str] = Field(default_factory=dict)
    git_commit: str | None = None
    git_dirty: bool | None = None
    package_version: str
    python_version: str
    dependency_lock_sha256: str | None = None
    retrieval_store_sha256: str | None = None
    n_results: int = 0
    n_failed: int = 0
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    total_cost_usd: float | None = None
    cost_note: str | None = None
    runtime_seconds: float | None = None
    notes: list[str] = Field(default_factory=list)
