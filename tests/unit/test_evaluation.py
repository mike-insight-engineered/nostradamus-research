from datetime import date

import pytest

from nostradamus_research.evaluation.agreement import reviewer_agreement
from nostradamus_research.evaluation.evaluate import (
    aggregate_labels,
    evaluate_results,
    review_label,
    summarise,
)
from nostradamus_research.evaluation.metrics import chrf, compute_metrics
from nostradamus_research.evaluation.mqm import (
    TAXONOMY,
    TaxonomyError,
    category_counts,
    parse_category,
    parse_severity,
    penalty,
    severity_at_least,
)
from nostradamus_research.evaluation.review_package import LinkedReview
from nostradamus_research.evaluation.statistics import bootstrap_ci, wilson_interval
from nostradamus_research.models.enums import ErrorCategory, EvidenceLevel, Severity, TargetLanguage
from nostradamus_research.models.review import HumanReview, MQMError
from nostradamus_research.translation.providers import MockProvider
from nostradamus_research.translation.runner import build_pipeline, settings_from_config

W = {Severity.NEUTRAL: 0, Severity.MINOR: 1, Severity.MAJOR: 5, Severity.CRITICAL: 25}


def _err(cat="omission", sev="major", lang="en"):
    return MQMError(category=cat, severity=sev, target_language=lang, note="n")


def _review(
    item="RI-1",
    reviewer="Expert One",
    fr="acceptable",
    en="acceptable",
    errors=(),
    prov="expert",
    **kw,
):
    return HumanReview(
        review_id=f"{item}:{reviewer}",
        review_item_id=item,
        package_id="P",
        reviewer_id=reviewer,
        reviewer_provenance=prov,
        reviewed_on=date(2026, 1, 1),
        judgement_fr=fr,
        judgement_en=en,
        errors=list(errors),
        **kw,
    )


# ---- MQM -------------------------------------------------------------------------
def test_taxonomy_covers_required_categories():
    required = {
        "mistranslation",
        "historical_lexical",
        "grammar",
        "omission",
        "unsupported_addition",
        "language_identification",
        "lost_ambiguity",
        "invented_specificity",
        "names_dates",
        "transcription",
    }
    assert required <= {c.value for c in TAXONOMY}
    assert set(TAXONOMY) == set(ErrorCategory)


def test_category_parsing_and_aliases():
    assert parse_category("Lost ambiguity") is ErrorCategory.LOST_AMBIGUITY
    assert parse_category("addition") is ErrorCategory.UNSUPPORTED_ADDITION
    with pytest.raises(TaxonomyError, match="valid"):
        parse_category("vibes")
    assert parse_severity("MAJOR") is Severity.MAJOR
    with pytest.raises(TaxonomyError):
        parse_severity("huge")


def test_penalty_and_counts():
    errs = [_err(sev="minor"), _err(sev="major"), _err(cat="names_dates", sev="critical")]
    assert penalty(errs, W, source_words=50, per_words=100) == pytest.approx((1 + 5 + 25) * 2)
    assert category_counts(errs) == {"names_dates": 1, "omission": 2}
    assert severity_at_least(Severity.CRITICAL, Severity.MAJOR) and not severity_at_least(
        Severity.MINOR, Severity.MAJOR
    )
    with pytest.raises(ValueError):
        penalty(errs, W, source_words=0)


# ---- metrics & statistics -----------------------------------------------------------
def test_chrf_behaviour():
    assert chrf("the clerk wrote a letter", ["the clerk wrote a letter"]) == pytest.approx(100.0)
    low = chrf("completely unrelated", ["the clerk wrote a letter"])
    multi = chrf(
        "the scribe wrote a letter", ["the clerk wrote a letter", "the scribe wrote a letter"]
    )
    assert low < 30 and multi == pytest.approx(100.0)
    with pytest.raises(ValueError):
        chrf("x", [])


def test_compute_metrics_handles_missing(cfg):
    m = compute_metrics(None, ["ref"], cfg.evaluation.metrics)
    assert set(m) == {"chrf", "chrf_pp"} and all(v is None for v in m.values())
    assert compute_metrics("ref", [], cfg.evaluation.metrics)["chrf"] is None


def test_bootstrap_and_wilson():
    small = bootstrap_ci([1.0, 2.0], min_n=5)
    assert small.value == 1.5 and small.low is None
    est = bootstrap_ci([float(i) for i in range(20)], n_resamples=500, seed=1)
    assert est.low < est.value < est.high
    assert (
        bootstrap_ci([1.0] * 10, seed=1).low == bootstrap_ci([1.0] * 10, seed=1).low
    )  # deterministic
    w = wilson_interval(15, 20)
    assert (
        w.value == 0.75
        and w.low == pytest.approx(0.531, abs=1e-3)
        and w.high == pytest.approx(0.888, abs=1e-3)
    )
    assert wilson_interval(0, 0).value is None


# ---- correctness labels ---------------------------------------------------------------
def test_review_label_rules(cfg):
    c = cfg.evaluation.correctness
    assert review_label(_review(), TargetLanguage.ENGLISH, c) is True
    assert review_label(_review(errors=[_err(sev="major")]), TargetLanguage.ENGLISH, c) is False
    assert review_label(_review(errors=[_err(sev="minor")]), TargetLanguage.ENGLISH, c) is True
    assert (
        review_label(_review(errors=[_err(sev="major", lang="fr")]), TargetLanguage.ENGLISH, c)
        is True
    )
    assert (
        review_label(_review(errors=[_err(sev="critical", lang=None)]), TargetLanguage.ENGLISH, c)
        is False
    )
    assert review_label(_review(en="unresolvable"), TargetLanguage.ENGLISH, c) is None
    assert aggregate_labels([True, False], c) is False  # all_reviewers rule
    assert aggregate_labels([None, None], c) is None


def test_evaluate_and_summarise(cfg, fixture_passages, oracle):
    pl = build_pipeline(
        "A_direct", MockProvider(oracle=oracle), settings_from_config(cfg, "A_direct"), None
    )
    results = [pl.translate(p, "r") for p in fixture_passages]
    by_id = {p.passage_id: p for p in fixture_passages}
    reviews = [
        LinkedReview(
            _review(item=f"RI-{i}", reviewer="SYNTHETIC-R", prov="synthetic_fixture"),
            r.result_id,
            r.run_id,
            r.passage_id,
            str(r.pipeline),
        )
        for i, r in enumerate(results)
    ]
    evals = evaluate_results(results, by_id, reviews, cfg.evaluation)
    assert len(evals) == 2 * len(results)
    assert all(e.evidence_level is EvidenceLevel.SYNTHETIC_FIXTURE for e in evals)
    assert all(e.metrics["chrf"] is not None and e.n_references == 1 for e in evals)
    s = summarise(evals, cfg.evaluation.statistics)
    assert {g["target_language"] for g in s["groups"]} == {"fr", "en"}
    assert s["groups"][0]["acceptance_rate"]["value"] == 1.0
    assert s["staging"] is None  # only pipeline A present


# ---- agreement ------------------------------------------------------------------------------
def test_agreement_metrics():
    revs = []
    for i in range(12):
        a = "acceptable" if i % 2 else "unacceptable"
        b = a if i < 10 else ("acceptable" if a == "unacceptable" else "unacceptable")
        revs += [
            _review(
                item=f"RI-{i}",
                reviewer="Expert A",
                en=a,
                errors=[_err()] if a == "unacceptable" else [],
            ),
            _review(
                item=f"RI-{i}",
                reviewer="Expert B",
                en=b,
                errors=[_err()] if b == "unacceptable" else [],
            ),
        ]
    res = reviewer_agreement(revs, TargetLanguage.ENGLISH, weights=W, min_items=10)
    assert res.n_items_multi_reviewed == 12 and res.n_reviewer_pairs == 1
    assert res.percent_agreement == pytest.approx(10 / 12)
    assert 0 < res.mean_cohen_kappa < 1
    assert res.penalty_spearman is not None and not res.notes


def test_agreement_with_too_few_items_is_flagged():
    revs = [_review(item="RI-1", reviewer="Expert A"), _review(item="RI-1", reviewer="Expert B")]
    res = reviewer_agreement(revs, TargetLanguage.ENGLISH, weights=W, min_items=10)
    assert any("unstable" in n for n in res.notes) and res.mean_cohen_kappa is None
