"""End-to-end OFFLINE demonstration on synthetic fixtures with the mock provider.

Exercises every stage — validation, audit, splitting, leakage checks, four
pipelines, persistence, automated metrics, blinded review export, (synthetic)
review import, agreement, calibration and reporting — at zero cost.

Everything produced is labelled synthetic. Nothing here is research evidence.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from .calibration.analysis import analyse
from .calibration.dataset import build_items, group_reviews
from .config import AppConfig
from .corpus.io import dataset_version, load_lexical_evidence, load_passages
from .corpus.leakage import check_leakage
from .corpus.splitting import apply_plan, plan_splits
from .evaluation.agreement import reviewer_agreement
from .evaluation.evaluate import evaluate_results, summarise
from .evaluation.review_package import (
    build_review_package,
    import_reviews,
    write_linked_reviews,
    write_review_package,
)
from .evaluation.synthetic import simulate_reviews
from .linguistics.retrieval import LexicalEvidenceStore
from .models.enums import PipelineId, TargetLanguage
from .provenance.audit import audit_corpus
from .provenance.registry import SourceRegistry
from .reporting.benchmark import render_benchmark
from .reporting.calibration_report import render_calibration
from .reporting.source_audit import render_source_audit
from .translation.providers.mock import MockProvider
from .translation.runner import Selection, build_pipeline, run_experiment, settings_from_config
from .utils.jsonl import write_json, write_jsonl

DEMO_REASON = "offline synthetic demonstration (fixtures only; not research evaluation)"


class DemoError(RuntimeError):
    pass


def run_demo(cfg: AppConfig, out_dir: Path) -> dict[str, Any]:
    fx = cfg.path("fixtures_dir")
    templates = cfg.path("report_templates_dir")
    reports = out_dir / "reports"

    registry, reg_errors = SourceRegistry.load(fx / "synthetic_sources.jsonl")
    loaded = load_passages(fx / "synthetic_passages.jsonl")
    evidence = load_lexical_evidence(fx / "synthetic_lexical_evidence.jsonl")
    if reg_errors or loaded.errors or evidence.errors:
        raise DemoError(
            "fixture validation failed: "
            + "; ".join(map(str, [*reg_errors, *loaded.errors, *evidence.errors]))
        )
    audit = audit_corpus(registry, loaded.records, forbid_synthetic=False)

    plan = plan_splits(loaded.records, {str(k): v for k, v in cfg.corpus.splits.targets.items()}, seed=cfg.corpus.splits.seed,
                       group_by=cfg.corpus.splits.group_by)  # fmt: skip
    passages = apply_plan(loaded.records, plan)
    plan.dataset_sha256 = dataset_version(passages)
    write_json(out_dir / "splits.json", plan.to_dict())
    write_jsonl(out_dir / "passages_with_splits.jsonl", passages)
    leakage = check_leakage(passages, evidence=evidence.records,
                            near_duplicate_threshold=cfg.corpus.leakage.near_duplicate_threshold,
                            shingle_size=cfg.corpus.leakage.shingle_size, group_by=cfg.corpus.splits.group_by)  # fmt: skip
    by_id = {p.passage_id: p for p in passages}

    # Oracle built ONLY from synthetic fixture references; pipelines never see it.
    oracle = {
        p.diplomatic_sha256: {str(r.target_language): r.text for r in p.reference_translations}
        for p in passages
    }
    store = LexicalEvidenceStore(evidence.records)
    selection = Selection(passages=sorted(passages, key=lambda p: p.passage_id))
    manifests, results = [], []
    for pid in PipelineId:
        settings = replace(settings_from_config(cfg, pid.value), allow_synthetic_evidence=True)
        pipeline = build_pipeline(pid.value, MockProvider(oracle=oracle), settings, store)
        out = run_experiment(cfg, pipeline, selection, dataset_path=fx / "synthetic_passages.jsonl",
                             dataset_sha256=plan.dataset_sha256, runs_dir=out_dir / "runs",
                             description="SYNTHETIC offline demonstration", test_access_reason=DEMO_REASON,
                             ledger_path=out_dir / "test_access_ledger.jsonl",
                             run_id=f"demo-{pid.value}")  # fmt: skip
        manifests.append(out.manifest)
        results.extend(out.results)

    # Blinded review package, then SYNTHETIC reviews (clearly labelled) imported back.
    package = build_review_package(results, by_id, registry, package_id="DEMO-PKG-001",
                                   seed=cfg.evaluation.review.blinding_seed)  # fmt: skip
    write_review_package(
        package, out_dir / "review", instructions_template=templates / "human-review.md"
    )
    synthetic_path = out_dir / "review" / "synthetic_reviews.jsonl"
    write_jsonl(
        synthetic_path, simulate_reviews(package.items, by_id, package_id=package.package_id)
    )
    assert package.key_path is not None
    imported = import_reviews(synthetic_path, package.key_path, allow_synthetic=True)
    if not imported.ok:
        raise DemoError("review import failed: " + "; ".join(map(str, imported.errors[:5])))
    write_linked_reviews(out_dir / "linked_reviews.jsonl", imported.reviews)

    weights = cfg.evaluation.mqm.severity_weights
    agreement = {
        str(lang): reviewer_agreement([lr.review for lr in imported.reviews], lang, weights=weights,
                                      min_items=cfg.evaluation.agreement.min_items_for_estimate).__dict__
        for lang in TargetLanguage
    }  # fmt: skip
    evals = evaluate_results(results, by_id, imported.reviews, cfg.evaluation)
    summary = summarise(evals, cfg.evaluation.statistics)
    write_jsonl(out_dir / "evaluation.jsonl", evals)
    write_json(out_dir / "evaluation_summary.json", {**summary, "agreement": agreement})

    reviews_by_result = group_reviews(imported.reviews)  # type: ignore[arg-type]
    items = build_items(results, reviews_by_result, by_id, cfg.evaluation.correctness)
    overall = analyse(items, cfg.evaluation.calibration, cfg.evaluation.statistics.confidence_level)
    per_pipe = {
        str(pid): analyse([i for i in items if i.pipeline is pid], cfg.evaluation.calibration,
                          cfg.evaluation.statistics.confidence_level)
        for pid in PipelineId
    }  # fmt: skip
    write_json(out_dir / "calibration.json", {"overall": overall.to_dict(),
                                              "by_pipeline": {k: v.to_dict() for k, v in per_pipe.items()}})  # fmt: skip

    reports.mkdir(parents=True, exist_ok=True)
    (reports / "source-audit.md").write_text(
        render_source_audit(registry, audit, templates / "source-audit.md",
                            registry_path=str(fx / "synthetic_sources.jsonl")), encoding="utf-8")  # fmt: skip
    (reports / "benchmark-report.md").write_text(
        render_benchmark(manifests, evals, summary, by_id, templates / "benchmark-report.md"),
        encoding="utf-8",
    )
    (reports / "calibration-report.md").write_text(
        render_calibration(overall, per_pipe, templates / "calibration-report.md",
                           inputs=[str(out_dir / "runs"), str(out_dir / "linked_reviews.jsonl")]),
        encoding="utf-8")  # fmt: skip

    return {
        "out_dir": str(out_dir),
        "n_passages": len(passages),
        "splits": plan.achieved,
        "leakage_errors": len(leakage.errors),
        "audit_errors": len(audit.errors),
        "runs": [m.run_id for m in manifests],
        "n_results": len(results),
        "n_failed": sum(m.n_failed for m in manifests),
        "n_review_items": len(package.items),
        "n_reviews": len(imported.reviews),
        "ece": overall.ece,
        "reports": sorted(str(p) for p in reports.glob("*.md")),
    }
