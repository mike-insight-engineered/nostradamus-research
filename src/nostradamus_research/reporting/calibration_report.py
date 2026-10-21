"""Report C — Confidence Calibration."""

from __future__ import annotations

from pathlib import Path

from ..calibration.analysis import CalibrationAnalysis
from ..utils.runtime import utc_now
from .common import bullet, evidence_banner, md_table, render_template


def _f(v: float | None, d: int = 3) -> str:
    return "n/a" if v is None else f"{v:.{d}f}"


def render_calibration(
    overall: CalibrationAnalysis,
    by_pipeline: dict[str, CalibrationAnalysis],
    template: Path,
    *,
    inputs: list[str],
) -> str:
    acc = overall.accuracy
    metric_rows = [("Overall", a.n_items, a.n_labelled, a.n_usable, _f(a.mean_stated_confidence),
                    acc.fmt(3) if (a is overall) else a.accuracy.fmt(3), _f(a.ece), _f(a.brier), _f(a.aurc))
                   for a in [overall]]  # fmt: skip
    metric_rows += [(k, a.n_items, a.n_labelled, a.n_usable, _f(a.mean_stated_confidence), a.accuracy.fmt(3),
                     _f(a.ece), _f(a.brier), _f(a.aurc)) for k, a in sorted(by_pipeline.items())]  # fmt: skip
    bin_rows = [(f"[{b.lower:.2f}, {b.upper:.2f}{']' if b.upper >= 1 else ')'}", b.count, _f(b.mean_confidence),
                 _f(b.accuracy), f"[{_f(b.accuracy_low, 2)}, {_f(b.accuracy_high, 2)}]" if b.count else "—",
                 _f(b.gap)) for b in overall.bins]  # fmt: skip
    cov_rows = [(_f(c.threshold), f"{c.coverage:.2f}", c.n_retained, _f(c.error_rate),
                 f"[{_f(c.error_low, 2)}, {_f(c.error_high, 2)}]") for c in overall.coverage]  # fmt: skip

    observations = []
    if (
        overall.ece is not None
        and overall.mean_stated_confidence is not None
        and acc.value is not None
    ):
        direction = (
            "over-confident" if overall.mean_stated_confidence > acc.value else "under-confident"
        )
        observations.append(
            f"Mean stated confidence {overall.mean_stated_confidence:.2f} vs empirical correctness "
            f"rate {acc.value:.2f}: descriptively {direction} (ECE {overall.ece:.3f})."
        )
    sparse = [b for b in overall.bins if 0 < b.count < 5]
    if sparse:
        observations.append(
            f"{len(sparse)} bin(s) contain fewer than 5 items; their accuracy is unreliable."
        )
    empty = [b for b in overall.bins if b.count == 0]
    if empty:
        observations.append(f"{len(empty)} bin(s) are empty.")

    limitations = [
        "Stated confidence is the model's own verbalised estimate (or a mock value); it is not a "
        "probability and was never imputed where absent.",
        "Correctness labels derive from reviewer judgements under the rule in config/evaluation.yaml.",
        "ECE depends on the binning scheme; with small n it is dominated by sampling noise.",
        "A held-out set of 20 passages cannot establish a precise accuracy rate: a Wilson 95% interval "
        "for 15/20 correct is roughly [0.53, 0.89].",
    ]
    return render_template(
        template,
        banner=evidence_banner(overall.evidence_levels.keys()),
        generated_at=utc_now().isoformat(),
        inputs=bullet(f"`{i}`" for i in inputs),
        sufficiency=(
            "Sample size meets the configured minimum for calibration claims."
            if overall.sufficient_sample
            else "**Sample size is BELOW the configured minimum for calibration claims. All figures below are descriptive only.**"
        ),
        confidence_sources=", ".join(
            f"{k}: {v}" for k, v in sorted(overall.confidence_sources.items())
        )
        or "none",
        metrics_table=md_table(
            [
                "Scope",
                "Items",
                "Labelled",
                "Usable",
                "Mean stated conf.",
                "Empirical correctness (95% CI)",
                "ECE",
                "Brier",
                "AURC",
            ],
            metric_rows,
        ),
        reliability_table=md_table(
            ["Bin", "n", "Mean conf.", "Accuracy", "95% CI", "Gap"], bin_rows
        )
        if bin_rows
        else "No usable items.",
        coverage_table=md_table(
            ["Threshold", "Coverage", "Retained", "Error rate", "95% CI"], cov_rows
        )
        if cov_rows
        else "No usable items.",
        observations=bullet(observations, "No observations (insufficient data)."),
        notes=bullet(overall.notes),
        limitations=bullet(limitations),
    )
