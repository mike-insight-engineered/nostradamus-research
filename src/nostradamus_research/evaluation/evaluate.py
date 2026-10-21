"""Combine translation results, references and reviews into evaluation records and summaries."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

from ..config import CorrectnessConfig, EvaluationConfig, StatisticsConfig
from ..linguistics.segmentation import word_count
from ..models.enums import (
    DataOrigin,
    EvidenceLevel,
    ReviewerProvenance,
    ReviewJudgement,
    TargetLanguage,
)
from ..models.evaluation import EvaluationResult
from ..models.passage import Passage
from ..models.review import HumanReview
from ..models.translation import TranslationResult
from ..utils.runtime import utc_now
from .metrics import compute_metrics
from .mqm import category_counts, penalty, severity_at_least
from .review_package import LinkedReview
from .statistics import Estimate, bootstrap_ci, wilson_interval


def review_label(review: HumanReview, lang: TargetLanguage, cfg: CorrectnessConfig) -> bool | None:
    """One reviewer's correctness label for one output language (None = excluded)."""
    judgement = review.judgement_fr if lang is TargetLanguage.MODERN_FRENCH else review.judgement_en
    if review.unresolvable or judgement is ReviewJudgement.UNRESOLVABLE:
        return None if cfg.exclude_unresolvable else False
    serious = any(
        severity_at_least(e.severity, cfg.unacceptable_at_or_above)
        for e in review.errors
        if e.target_language in (lang, None)
    )
    if judgement is None:
        return None
    return judgement is ReviewJudgement.ACCEPTABLE and not serious


def aggregate_labels(labels: list[bool | None], cfg: CorrectnessConfig) -> bool | None:
    vals = [v for v in labels if v is not None]
    if not vals:
        return None
    if cfg.aggregation == "all_reviewers":
        return all(vals)
    yes = sum(vals)
    no = len(vals) - yes
    return None if yes == no else yes > no


def evidence_level(passage: Passage, reviews: list[HumanReview]) -> EvidenceLevel:
    if passage.data_origin is DataOrigin.SYNTHETIC_FIXTURE or any(
        r.reviewer_provenance is ReviewerProvenance.SYNTHETIC_FIXTURE for r in reviews
    ):
        return EvidenceLevel.SYNTHETIC_FIXTURE
    if not reviews:
        return EvidenceLevel.AUTOMATED_ONLY
    if all(r.reviewer_provenance is ReviewerProvenance.EXPERT for r in reviews):
        return EvidenceLevel.EXPERT_REVIEWED
    return EvidenceLevel.HUMAN_NON_EXPERT


def evaluate_results(
    results: list[TranslationResult],
    passages: dict[str, Passage],
    reviews: list[LinkedReview],
    cfg: EvaluationConfig,
) -> list[EvaluationResult]:
    by_result: dict[str, list[HumanReview]] = defaultdict(list)
    for lr in reviews:
        by_result[lr.result_id].append(lr.review)
    out: list[EvaluationResult] = []
    for r in results:
        p = passages.get(r.passage_id)
        if p is None:
            continue
        revs = by_result.get(r.result_id, [])
        n_words = max(word_count(p.diplomatic_transcription), 1)
        for lang, hyp in (
            (TargetLanguage.MODERN_FRENCH, r.translation_fr),
            (TargetLanguage.ENGLISH, r.translation_en),
        ):
            refs = p.references_for(lang)
            notes: list[str] = []
            if not refs:
                notes.append("no reference translation: automated metrics unavailable")
            if hyp is None:
                notes.append("no output (pipeline error or parse failure)")
            mqm_pen: float | None = None
            errs = []
            if revs:
                per = [
                    penalty([e for e in rv.errors if e.target_language in (lang, None)],
                            cfg.mqm.severity_weights, source_words=n_words, per_words=cfg.mqm.per_source_words)
                    for rv in revs
                ]  # fmt: skip
                mqm_pen = sum(per) / len(per)
                errs = [e for rv in revs for e in rv.errors if e.target_language in (lang, None)]
            label = aggregate_labels(
                [review_label(rv, lang, cfg.correctness) for rv in revs], cfg.correctness
            )
            out.append(EvaluationResult(
                evaluation_id=f"{r.result_id}:{lang}",
                run_id=r.run_id, result_id=r.result_id, passage_id=p.passage_id, pipeline=r.pipeline,
                category=p.category, split=p.split, target_language=lang,
                metrics=compute_metrics(hyp, [x.text for x in refs], cfg.metrics),
                reference_ids=[x.reference_id for x in refs], n_references=len(refs),
                mqm_penalty=mqm_pen, mqm_error_counts=category_counts(errs),
                human_acceptable=label, review_ids=[rv.review_id for rv in revs],
                evidence_level=evidence_level(p, revs), notes=notes, created_at=utc_now(),
            ))  # fmt: skip
    return out


def _est_dict(e: Estimate) -> dict[str, Any]:
    return {
        "value": e.value,
        "low": e.low,
        "high": e.high,
        "n": e.n,
        "method": e.method,
        "note": e.note,
    }


def summarise(evals: list[EvaluationResult], stats_cfg: StatisticsConfig) -> dict[str, Any]:
    """Per-pipeline and per-category summaries with uncertainty intervals."""
    if not evals:
        return {"groups": [], "by_category": [], "evidence_levels": {}, "n_evaluations": 0}
    df = pd.DataFrame([{
        "pipeline": str(e.pipeline), "lang": str(e.target_language), "category": str(e.category),
        "split": str(e.split), "chrf": e.metrics.get("chrf"), "mqm": e.mqm_penalty,
        "acceptable": e.human_acceptable, "level": str(e.evidence_level), "passage_id": e.passage_id,
        "errors": e.mqm_error_counts,
    } for e in evals])  # fmt: skip

    def ci(values: list[float]) -> Estimate:
        return bootstrap_ci(values, n_resamples=stats_cfg.bootstrap_resamples,
                            confidence=stats_cfg.confidence_level, seed=stats_cfg.seed,
                            min_n=stats_cfg.min_n_for_bootstrap)  # fmt: skip

    groups = []
    for (pipe, lang), g in df.groupby(["pipeline", "lang"], sort=True):
        labels = [bool(v) for v in g["acceptable"] if v is not None and not pd.isna(v)]
        err_totals: dict[str, int] = defaultdict(int)
        for d in g["errors"]:
            for k, v in d.items():
                err_totals[k] += v
        groups.append({
            "pipeline": pipe, "target_language": lang, "n_outputs": len(g),
            "chrf": _est_dict(ci([float(x) for x in g["chrf"].dropna()])),
            "mqm_penalty": _est_dict(ci([float(x) for x in g["mqm"].dropna()])),
            "acceptance_rate": _est_dict(wilson_interval(sum(labels), len(labels), stats_cfg.confidence_level)),
            "n_labelled": len(labels),
            "error_counts": dict(sorted(err_totals.items())),
            "evidence_levels": dict(g["level"].value_counts().sort_index()),
        })  # fmt: skip
    by_cat = []
    for (pipe, lang, cat), g in df.groupby(["pipeline", "lang", "category"], sort=True):
        vals = [float(x) for x in g["chrf"].dropna()]
        by_cat.append({"pipeline": pipe, "target_language": lang, "category": cat, "n": len(g),
                       "mean_chrf": (sum(vals) / len(vals)) if vals else None})  # fmt: skip
    return {
        "n_evaluations": len(evals),
        "groups": groups,
        "by_category": by_cat,
        "evidence_levels": {k: int(v) for k, v in df["level"].value_counts().sort_index().items()},
        "staging": staging_comparison(evals, stats_cfg),
    }


def staging_comparison(
    evals: list[EvaluationResult], stats_cfg: StatisticsConfig
) -> dict[str, Any] | None:
    """Paired B − A comparison on English outputs: does staging through French lose meaning?"""
    en = [e for e in evals if e.target_language is TargetLanguage.ENGLISH]
    a = {e.passage_id: e for e in en if e.pipeline.value == "A_direct"}
    b = {e.passage_id: e for e in en if e.pipeline.value == "B_two_stage"}
    shared = sorted(set(a) & set(b))
    if not shared:
        return None
    diffs = [
        b[p].metrics["chrf"] - a[p].metrics["chrf"]  # type: ignore[operator]
        for p in shared
        if a[p].metrics.get("chrf") is not None and b[p].metrics.get("chrf") is not None
    ]
    mqm_diffs = [b[p].mqm_penalty - a[p].mqm_penalty for p in shared  # type: ignore[operator]
                 if a[p].mqm_penalty is not None and b[p].mqm_penalty is not None]  # fmt: skip
    est = bootstrap_ci(diffs, n_resamples=stats_cfg.bootstrap_resamples, confidence=stats_cfg.confidence_level,
                       seed=stats_cfg.seed, min_n=stats_cfg.min_n_for_bootstrap)  # fmt: skip
    mest = bootstrap_ci(mqm_diffs, n_resamples=stats_cfg.bootstrap_resamples,
                        confidence=stats_cfg.confidence_level, seed=stats_cfg.seed,
                        min_n=stats_cfg.min_n_for_bootstrap)  # fmt: skip
    return {
        "n_paired_passages": len(shared),
        "chrf_en_B_minus_A": _est_dict(est),
        "mqm_en_B_minus_A": _est_dict(mest),
        "interpretation": "negative chrF difference or positive MQM difference suggests staging loss; "
        "intervals spanning 0 are inconclusive",
    }
