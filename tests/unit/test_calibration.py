import pytest

from nostradamus_research.calibration.abstention import (
    AbstentionPolicy,
    TestSplitTuningError,
    select_threshold,
)
from nostradamus_research.calibration.analysis import analyse
from nostradamus_research.calibration.dataset import CalibrationItem
from nostradamus_research.calibration.metrics import (
    area_under_risk_coverage,
    brier_score,
    coverage_risk_curve,
    expected_calibration_error,
    max_calibration_error,
    reliability_bins,
)
from nostradamus_research.config import CalibrationConfig
from nostradamus_research.models.enums import (
    ConfidenceSource,
    DatasetSplit,
    EvidenceLevel,
    PipelineId,
)


def _item(conf, correct, split=DatasetSplit.VALIDATION, src=ConfidenceSource.MODEL_STATED):
    return CalibrationItem(
        "r",
        "p",
        PipelineId.A_DIRECT,
        split,
        conf,
        src if conf is not None else ConfidenceSource.NONE,
        correct,
        EvidenceLevel.EXPERT_REVIEWED,
    )


def test_perfectly_calibrated_bins_have_zero_ece():
    conf = [0.25] * 4 + [0.75] * 4
    correct = [True, False, False, False, True, True, True, False]
    bins = reliability_bins(conf, correct, n_bins=2)
    assert [b.count for b in bins] == [4, 4]
    assert expected_calibration_error(bins) == pytest.approx(0.0)
    assert max_calibration_error(bins) == pytest.approx(0.0)


def test_known_ece_and_brier():
    conf, correct = [0.9, 0.9, 0.9, 0.9], [True, False, False, False]
    bins = reliability_bins(conf, correct, n_bins=10)
    assert expected_calibration_error(bins) == pytest.approx(0.65)
    assert brier_score(conf, correct) == pytest.approx((0.01 + 3 * 0.81) / 4)
    assert bins[-1].accuracy_low is not None and bins[-1].accuracy_high is not None


def test_confidence_one_falls_in_last_bin_and_validation():
    bins = reliability_bins([1.0, 0.0], [True, False], n_bins=4)
    assert bins[-1].count == 1 and bins[0].count == 1
    with pytest.raises(ValueError):
        reliability_bins([1.2], [True])
    with pytest.raises(ValueError):
        brier_score([0.5], [True, False])


def test_quantile_binning():
    bins = reliability_bins(
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        [False, False, True, True, True, True],
        n_bins=3,
        strategy="quantile",
    )
    assert sum(b.count for b in bins) == 6


def test_coverage_risk_curve():
    pts = coverage_risk_curve([0.2, 0.5, 0.9, 0.9], [False, True, True, True])
    assert pts[0].coverage == 1.0 and pts[0].error_rate == pytest.approx(0.25)
    assert pts[-1].coverage == 0.5 and pts[-1].error_rate == 0.0
    assert area_under_risk_coverage(pts) is not None


def test_abstention_policy():
    policy = AbstentionPolicy(threshold=0.6)
    assert (
        policy.decide(0.7) == "answer"
        and policy.decide(0.5) == "abstain"
        and policy.decide(None) == "abstain"
    )
    stats = policy.evaluate(
        [_item(0.9, True), _item(0.8, False), _item(0.2, False), _item(None, True)]
    )
    assert stats["n_answered"] == 2 and stats["error_rate_when_answering"] == 0.5


def test_threshold_selection_refuses_test_items():
    items = [_item(0.9, True), _item(0.5, False), _item(0.7, True)]
    assert select_threshold(items, max_error_rate=0.0) == 0.7
    with pytest.raises(TestSplitTuningError):
        select_threshold([*items, _item(0.8, True, split=DatasetSplit.TEST)], max_error_rate=0.1)


def test_analysis_never_imputes_confidence():
    items = [
        _item(0.9, True),
        _item(0.4, False),
        _item(None, True),
        _item(None, False),
        _item(0.7, None),
    ]
    res = analyse(items, CalibrationConfig(n_bins=5, min_items_for_calibration_claims=50))
    assert (
        res.n_items == 5
        and res.n_labelled == 4
        and res.n_usable == 2
        and res.n_with_confidence == 3
    )
    assert res.accuracy.value == 0.5 and res.accuracy.n == 4
    assert not res.sufficient_sample
    assert any("no value was imputed" in n for n in res.notes)
    assert any("not a calibrated probability" in n for n in res.notes)


def test_analysis_with_no_usable_items():
    res = analyse([_item(None, True)], CalibrationConfig())
    assert res.ece is None and res.brier is None and res.bins == []
