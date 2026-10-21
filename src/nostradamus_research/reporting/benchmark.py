"""Report B — Translation Benchmark."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models.evaluation import EvaluationResult
from ..models.experiment import ExperimentManifest
from ..models.passage import Passage
from ..utils.runtime import utc_now
from .common import bullet, evidence_banner, fmt_est, md_table, render_template


def render_benchmark(
    manifests: list[ExperimentManifest],
    evals: list[EvaluationResult],
    summary: dict[str, Any],
    passages: dict[str, Passage],
    template: Path,
) -> str:
    levels = [e.evidence_level for e in evals] + [m.evidence_level for m in manifests]
    cfg_rows = [(m.run_id, m.pipeline, m.provider, m.model, m.is_mock,
                 ", ".join(f"{t.template_id}@{t.version}" for t in m.prompt_templates),
                 m.provider_params.get("temperature"), m.status) for m in manifests]  # fmt: skip
    data_rows = [(m.run_id, m.dataset_sha256[:12], len(m.passage_ids), ", ".join(map(str, m.splits_included)),
                  m.test_split_accessed, m.data_origin_counts) for m in manifests]  # fmt: skip
    ref_ids = sorted({rid for e in evals for rid in e.reference_ids})
    ref_types = sorted({
        f"{r.translator_type} ({r.data_origin})"
        for p in passages.values() for r in p.reference_translations if r.reference_id in ref_ids
    })  # fmt: skip
    group_rows = [(g["pipeline"], g["target_language"], g["n_outputs"], fmt_est(g["chrf"]),
                   fmt_est(g["acceptance_rate"], 2), g["n_labelled"], fmt_est(g["mqm_penalty"]))
                  for g in summary.get("groups", [])]  # fmt: skip
    cat_rows = [(c["pipeline"], c["target_language"], c["category"], c["n"], c["mean_chrf"])
                for c in summary.get("by_category", [])]  # fmt: skip
    err_rows = [(g["pipeline"], g["target_language"],
                 ", ".join(f"{k}: {v}" for k, v in g["error_counts"].items()) or "none recorded")
                for g in summary.get("groups", [])]  # fmt: skip
    cost_rows = [(m.run_id, m.runtime_seconds, m.total_input_tokens, m.total_output_tokens,
                  m.total_cost_usd, m.cost_note) for m in manifests]  # fmt: skip
    st = summary.get("staging")
    staging = (
        f"Paired passages: {st['n_paired_passages']}. English chrF (B − A): {fmt_est(st['chrf_en_B_minus_A'])}. "
        f"English MQM penalty (B − A): {fmt_est(st['mqm_en_B_minus_A'])}. {st['interpretation']}."
        if st
        else "Not available (requires runs of both A_direct and B_two_stage on the same passages)."
    )
    limitations = [
        "chrF measures character n-gram overlap with references; it is not evidence of correctness.",
        "Acceptance rates use Wilson intervals; with tens of passages these intervals are wide.",
        "Pretraining contamination (models having seen these texts or translations) cannot be excluded.",
    ]
    if any(m.test_split_accessed for m in manifests):
        limitations.append("Held-out test passages were translated; see the test access ledger.")
    return render_template(
        template,
        banner=evidence_banner(levels),
        generated_at=utc_now().isoformat(),
        pipeline_table=md_table(
            ["Run", "Pipeline", "Provider", "Model", "Mock", "Prompts", "Temp.", "Status"], cfg_rows
        ),
        dataset_table=md_table(
            ["Run", "Dataset SHA-256", "Passages", "Splits", "Test accessed", "Origins"], data_rows
        ),
        reference_summary=f"{len(ref_ids)} reference translations used; types: {', '.join(ref_types) or 'none'}.",
        results_table=md_table(
            [
                "Pipeline",
                "Lang",
                "Outputs",
                "chrF (95% CI)",
                "Acceptable (95% CI)",
                "Labelled",
                "MQM penalty",
            ],
            group_rows,
        ),
        category_table=md_table(["Pipeline", "Lang", "Category", "n", "Mean chrF"], cat_rows),
        error_table=md_table(["Pipeline", "Lang", "Error counts"], err_rows),
        staging_analysis=staging,
        cost_table=md_table(
            ["Run", "Runtime (s)", "Input tokens", "Output tokens", "Cost (USD)", "Note"], cost_rows
        ),
        limitations=bullet(limitations),
    )
