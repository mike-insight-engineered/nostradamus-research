"""Experiment execution: passage selection, held-out protection, persistence, manifests."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import __version__
from ..config import AppConfig
from ..linguistics.retrieval import LexicalEvidenceStore
from ..models.enums import DataOrigin, DatasetSplit, EvidenceLevel, VerificationStatus, status_rank
from ..models.experiment import ExperimentManifest
from ..models.passage import Passage
from ..models.translation import TranslationResult
from ..utils.hashing import sha256_file, stable_hash
from ..utils.jsonl import append_jsonl, write_json, write_jsonl
from ..utils.runtime import git_commit, git_dirty, python_version, utc_now, utc_timestamp_slug
from .pipelines import PIPELINES, PipelineSettings, TranslationPipeline
from .prompts import PromptLibrary
from .providers.base import TranslationProvider


class HeldOutAccessError(PermissionError):
    pass


@dataclass
class Selection:
    passages: list[Passage]
    excluded: dict[str, str] = field(default_factory=dict)  # passage_id -> reason

    @property
    def touches_test(self) -> bool:
        return any(p.split is DatasetSplit.TEST for p in self.passages)


def select_passages(
    passages: list[Passage],
    *,
    splits: list[DatasetSplit] | None = None,
    passage_ids: list[str] | None = None,
    limit: int | None = None,
    minimum_status: VerificationStatus | None = None,
    allow_test_split: bool = False,
    test_access_reason: str | None = None,
) -> Selection:
    """Filter passages; refuses held-out passages unless explicitly authorised."""
    wanted = set(splits) if splits else None
    ids = set(passage_ids) if passage_ids else None
    sel = Selection(passages=[])
    for p in sorted(passages, key=lambda p: p.passage_id):
        if ids is not None and p.passage_id not in ids:
            continue
        if wanted is not None and p.split not in wanted:
            continue
        if minimum_status is not None and status_rank(p.verification_status) < status_rank(
            minimum_status
        ):
            sel.excluded[p.passage_id] = f"status {p.verification_status} below {minimum_status}"
            continue
        if p.split is DatasetSplit.TEST and not allow_test_split:
            sel.excluded[p.passage_id] = "held-out test passage (requires --allow-test-split)"
            continue
        sel.passages.append(p)
    if limit is not None:
        sel.passages = sel.passages[:limit]
    if sel.touches_test and not (test_access_reason and test_access_reason.strip()):
        raise HeldOutAccessError(
            "translating held-out test passages requires a stated reason (--test-reason); "
            "test-set access is logged and must not be used for prompt tuning or model selection"
        )
    if ids is not None:
        missing = ids - {p.passage_id for p in passages}
        for m in sorted(missing):
            sel.excluded[m] = "passage_id not found"
    return sel


def settings_from_config(cfg: AppConfig, pipeline_key: str) -> PipelineSettings:
    t = cfg.translation
    toggle = t.pipelines.get(pipeline_key)
    return PipelineSettings(
        prompt_versions=dict(t.prompt_versions),
        temperature=t.generation.temperature,
        max_tokens=t.generation.max_tokens,
        include_normalised_reading=t.include_normalised_reading,
        top_k=(toggle.top_k if toggle and toggle.top_k else t.retrieval.top_k),
        minimum_evidence_status=VerificationStatus(t.retrieval.minimum_evidence_status),
        allow_synthetic_evidence=t.retrieval.allow_synthetic_evidence,
        flag_speculative=t.flag_speculative_interpretation,
    )


def build_pipeline(
    pipeline_key: str,
    provider: TranslationProvider,
    settings: PipelineSettings,
    retriever: LexicalEvidenceStore | None,
    prompts: PromptLibrary | None = None,
) -> TranslationPipeline:
    from ..models.enums import PipelineId

    cls = PIPELINES[PipelineId(pipeline_key)]
    return cls(provider, prompts or PromptLibrary.load(), settings, retriever)


@dataclass
class RunOutput:
    manifest: ExperimentManifest
    results: list[TranslationResult]
    run_dir: Path | None
    plan: dict[str, Any]


def _evidence_level(passages: list[Passage]) -> EvidenceLevel:
    if any(p.data_origin is DataOrigin.SYNTHETIC_FIXTURE for p in passages):
        return EvidenceLevel.SYNTHETIC_FIXTURE
    return EvidenceLevel.AUTOMATED_ONLY


def run_experiment(
    cfg: AppConfig,
    pipeline: TranslationPipeline,
    selection: Selection,
    *,
    dataset_path: Path,
    dataset_sha256: str,
    runs_dir: Path,
    dry_run: bool = False,
    description: str | None = None,
    test_access_reason: str | None = None,
    ledger_path: Path | None = None,
    run_id: str | None = None,
) -> RunOutput:
    provider = pipeline.provider
    passages = selection.passages
    run_id = run_id or (
        f"{utc_timestamp_slug()}-{pipeline.pipeline_id.value}-{provider.name}-"
        f"{stable_hash([p.passage_id for p in passages])[:6]}"
    )
    origin_counts = Counter(str(p.data_origin) for p in passages)
    lock = cfg.root / "uv.lock"
    plan = {
        "run_id": run_id,
        "pipeline": pipeline.pipeline_id.value,
        "provider": provider.describe(),
        "n_passages": len(passages),
        "estimated_provider_calls": len(passages) * pipeline.calls_per_passage,
        "paid": provider.is_paid,
        "passage_ids": [p.passage_id for p in passages],
        "excluded": selection.excluded,
        "test_split_accessed": selection.touches_test,
    }
    manifest = ExperimentManifest(
        run_id=run_id,
        created_at=utc_now(),
        status="dry_run" if dry_run else "completed",
        description=description,
        pipeline=pipeline.pipeline_id,
        provider=provider.name,
        model=provider.model,
        is_mock=provider.name == "mock",
        provider_params={
            "temperature": pipeline.settings.temperature,
            "max_tokens": pipeline.settings.max_tokens,
            "top_k": pipeline.settings.top_k if pipeline.uses_retrieval else None,
            **{k: v for k, v in provider.describe().items() if k not in ("provider", "model")},
        },
        prompt_templates=[t.ref() for t in pipeline.templates],
        dataset_path=str(dataset_path),
        dataset_sha256=dataset_sha256,
        passage_ids=[p.passage_id for p in passages],
        splits_included=sorted({p.split for p in passages}, key=str),
        test_split_accessed=selection.touches_test,
        test_access_reason=test_access_reason if selection.touches_test else None,
        data_origin_counts=dict(origin_counts),
        evidence_level=_evidence_level(passages),
        config_sha256=cfg.file_hashes(),
        git_commit=git_commit(cfg.root),
        git_dirty=git_dirty(cfg.root),
        package_version=__version__,
        python_version=python_version(),
        dependency_lock_sha256=sha256_file(lock) if lock.is_file() else None,
        retrieval_store_sha256=(
            pipeline.retriever.content_hash()
            if pipeline.retriever and pipeline.uses_retrieval
            else None
        ),
    )
    if dry_run:
        return RunOutput(manifest, [], None, plan)

    t0 = time.perf_counter()
    results = [pipeline.translate(p, run_id) for p in passages]
    elapsed = round(time.perf_counter() - t0, 3)

    calls = [c for r in results for c in r.calls]
    ins = [c.usage.input_tokens for c in calls]
    outs = [c.usage.output_tokens for c in calls]
    costs = [c.cost_usd for c in calls]
    failed = sum(1 for r in results if not r.succeeded)
    manifest.n_results = len(results)
    manifest.n_failed = failed
    manifest.status = (
        "completed" if failed == 0 else ("failed" if failed == len(results) else "partial")
    )
    manifest.runtime_seconds = elapsed
    manifest.total_input_tokens = (
        sum(i for i in ins if i is not None) if calls and None not in ins else None
    )
    manifest.total_output_tokens = (
        sum(o for o in outs if o is not None) if calls and None not in outs else None
    )
    if calls and all(c is not None for c in costs):
        manifest.total_cost_usd = round(sum(c for c in costs if c is not None), 6)
        manifest.cost_note = "estimated from configured pricing"
    else:
        manifest.cost_note = (
            "mock provider: no cost"
            if provider.name == "mock"
            else "cost unknown (pricing or usage unavailable)"
        )

    run_dir = runs_dir / run_id
    write_jsonl(run_dir / "results.jsonl", results)
    write_json(run_dir / "manifest.json", manifest)
    if selection.touches_test and ledger_path is not None:
        append_jsonl(ledger_path, {
            "run_id": run_id, "accessed_at": utc_now().isoformat(), "pipeline": pipeline.pipeline_id.value,
            "provider": provider.name, "model": provider.model,
            "test_passage_ids": [p.passage_id for p in passages if p.split is DatasetSplit.TEST],
            "reason": test_access_reason, "dataset_sha256": dataset_sha256,
        })  # fmt: skip
    return RunOutput(manifest, results, run_dir, plan)
