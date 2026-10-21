import json

import pytest

from nostradamus_research.models.enums import DatasetSplit, EvidenceLevel, VerificationStatus
from nostradamus_research.models.experiment import ExperimentManifest
from nostradamus_research.models.translation import TranslationResult
from nostradamus_research.translation.providers import MockProvider
from nostradamus_research.translation.runner import (
    HeldOutAccessError,
    Selection,
    build_pipeline,
    run_experiment,
    select_passages,
    settings_from_config,
)
from nostradamus_research.utils.jsonl import load_models


def _with_splits(passages):
    splits = [DatasetSplit.DEVELOPMENT, DatasetSplit.VALIDATION, DatasetSplit.TEST]
    return [p.model_copy(update={"split": splits[i % 3]}) for i, p in enumerate(passages)]


def test_test_split_excluded_by_default(fixture_passages):
    ps = _with_splits(fixture_passages)
    sel = select_passages(ps)
    assert all(p.split is not DatasetSplit.TEST for p in sel.passages)
    assert any("held-out" in r for r in sel.excluded.values())


def test_test_split_requires_reason(fixture_passages):
    ps = _with_splits(fixture_passages)
    with pytest.raises(HeldOutAccessError, match="reason"):
        select_passages(ps, allow_test_split=True)
    sel = select_passages(ps, allow_test_split=True, test_access_reason="final evaluation")
    assert sel.touches_test


def test_minimum_status_filter(fixture_passages):
    sel = select_passages(
        fixture_passages, minimum_status=VerificationStatus.TRANSCRIPTION_VERIFIED
    )
    assert sel.passages == [] and len(sel.excluded) == len(fixture_passages)


def test_run_persists_results_manifest_and_ledger(cfg, tmp_path, fixture_passages):
    ps = _with_splits(fixture_passages)[:6]
    sel = select_passages(ps, allow_test_split=True, test_access_reason="unit test")
    pl = build_pipeline("A_direct", MockProvider(), settings_from_config(cfg, "A_direct"), None)
    ledger = tmp_path / "ledger.jsonl"
    out = run_experiment(
        cfg,
        pl,
        sel,
        dataset_path=tmp_path / "d.jsonl",
        dataset_sha256="x" * 64,
        runs_dir=tmp_path / "runs",
        test_access_reason="unit test",
        ledger_path=ledger,
        run_id="r1",
    )
    assert out.run_dir == tmp_path / "runs" / "r1"
    results = load_models(out.run_dir / "results.jsonl", TranslationResult)
    assert results.ok and len(results.records) == 6
    manifest = ExperimentManifest.model_validate(
        json.loads((out.run_dir / "manifest.json").read_text(encoding="utf-8"))
    )
    assert manifest.evidence_level is EvidenceLevel.SYNTHETIC_FIXTURE
    assert manifest.test_split_accessed and manifest.test_access_reason == "unit test"
    assert (
        manifest.prompt_templates[0].template_id == "direct"
        and len(manifest.prompt_templates[0].sha256) == 64
    )
    assert set(manifest.config_sha256) == {"project", "corpus", "translation", "evaluation"}
    assert manifest.is_mock and manifest.total_cost_usd is None and "mock" in manifest.cost_note
    assert manifest.total_input_tokens and manifest.n_failed == 0
    entry = json.loads(ledger.read_text(encoding="utf-8").strip())
    assert entry["run_id"] == "r1" and entry["reason"] == "unit test" and entry["test_passage_ids"]


def test_dry_run_writes_nothing(cfg, tmp_path, fixture_passages):
    pl = build_pipeline(
        "B_two_stage", MockProvider(), settings_from_config(cfg, "B_two_stage"), None
    )
    out = run_experiment(
        cfg,
        pl,
        Selection(fixture_passages[:3]),
        dataset_path=tmp_path / "d",
        dataset_sha256="0",
        runs_dir=tmp_path / "runs",
        dry_run=True,
    )
    assert out.results == [] and out.run_dir is None and not (tmp_path / "runs").exists()
    assert out.plan["estimated_provider_calls"] == 6
    assert out.manifest.status == "dry_run"
