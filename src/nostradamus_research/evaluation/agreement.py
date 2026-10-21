"""Inter-reviewer agreement on acceptability judgements and MQM penalties."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations

import numpy as np
from scipy import stats
from sklearn.metrics import cohen_kappa_score

from ..models.enums import ReviewJudgement, Severity, TargetLanguage
from ..models.review import HumanReview


@dataclass
class AgreementResult:
    target_language: str
    n_items_multi_reviewed: int
    n_reviewer_pairs: int
    percent_agreement: float | None
    mean_cohen_kappa: float | None
    penalty_spearman: float | None
    pairwise: list[dict[str, object]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _judgement(r: HumanReview, lang: TargetLanguage) -> ReviewJudgement | None:
    return r.judgement_fr if lang is TargetLanguage.MODERN_FRENCH else r.judgement_en


def _weighted_errors(r: HumanReview, lang: TargetLanguage, weights: dict[Severity, float]) -> float:
    return sum(weights.get(e.severity, 0.0) for e in r.errors if e.target_language in (lang, None))


def reviewer_agreement(
    reviews: list[HumanReview],
    lang: TargetLanguage,
    *,
    weights: dict[Severity, float],
    min_items: int = 10,
) -> AgreementResult:
    by_item: dict[str, dict[str, HumanReview]] = defaultdict(dict)
    for r in reviews:
        by_item[r.review_item_id][r.reviewer_id] = r
    multi = {i: rv for i, rv in by_item.items() if len(rv) >= 2}
    reviewers = sorted({rid for rv in multi.values() for rid in rv})
    res = AgreementResult(str(lang), len(multi), 0, None, None, None)
    if not multi:
        res.notes.append("no items were reviewed by two or more reviewers")
        return res

    agree = total = 0
    kappas: list[float] = []
    pen_a: list[float] = []
    pen_b: list[float] = []
    for a, b in combinations(reviewers, 2):
        shared = [i for i, rv in multi.items() if a in rv and b in rv]
        ja = [_judgement(multi[i][a], lang) for i in shared]
        jb = [_judgement(multi[i][b], lang) for i in shared]
        pairs = [(x, y) for x, y in zip(ja, jb, strict=True) if x is not None and y is not None]
        if not pairs:
            continue
        res.n_reviewer_pairs += 1
        agree += sum(1 for x, y in pairs if x == y)
        total += len(pairs)
        labels_a = [str(x) for x, _ in pairs]
        labels_b = [str(y) for _, y in pairs]
        kappa: float | None = None
        if len(set(labels_a) | set(labels_b)) > 1:
            k = float(cohen_kappa_score(labels_a, labels_b))
            kappa = None if np.isnan(k) else k
        if kappa is not None:
            kappas.append(kappa)
        res.pairwise.append({"reviewers": [a, b], "n_items": len(pairs), "cohen_kappa": kappa,
                             "percent_agreement": sum(1 for x, y in pairs if x == y) / len(pairs)})  # fmt: skip
        for i in shared:
            pen_a.append(_weighted_errors(multi[i][a], lang, weights))
            pen_b.append(_weighted_errors(multi[i][b], lang, weights))

    res.percent_agreement = agree / total if total else None
    res.mean_cohen_kappa = float(np.mean(kappas)) if kappas else None
    if len(pen_a) >= 3 and len(set(pen_a)) > 1 and len(set(pen_b)) > 1:
        rho = stats.spearmanr(pen_a, pen_b).statistic
        res.penalty_spearman = None if np.isnan(rho) else float(rho)
    if len(multi) < min_items:
        res.notes.append(
            f"only {len(multi)} multiply-reviewed items (< {min_items}); agreement estimates are unstable"
        )
    if not kappas:
        res.notes.append("Cohen's kappa undefined (a single category was used throughout)")
    return res
