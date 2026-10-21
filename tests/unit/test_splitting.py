from collections import Counter

from nostradamus_research.corpus.splitting import apply_plan, plan_splits, scale_targets
from nostradamus_research.models.enums import DatasetSplit
from tests.conftest import synthetic_passage

TARGETS = {"development": 48, "validation": 12, "test": 20}
CATS = (
    ["french_prose"] * 30
    + ["french_poetry"] * 20
    + ["latin_prose"] * 15
    + ["latin_verse"] * 5
    + ["mixed"] * 10
)


def _corpus_80():
    # 80 passages in 40 works of two passages each (same category within a work).
    return [synthetic_passage(i, f"W{i // 2:02d}", CATS[i]) for i in range(80)]


def test_scale_targets_sums_and_proportions():
    assert scale_targets(TARGETS, 80) == TARGETS
    s = scale_targets(TARGETS, 20)
    assert sum(s.values()) == 20 and s == {"development": 12, "validation": 3, "test": 5}
    assert sum(scale_targets(TARGETS, 13).values()) == 13


def test_full_corpus_hits_48_12_20_without_splitting_works():
    passages = _corpus_80()
    plan = plan_splits(passages, TARGETS, seed=1)
    assert plan.achieved == {"development": 48, "validation": 12, "test": 20}
    by_work: dict[str, set[str]] = {}
    for p in passages:
        by_work.setdefault(p.work_id, set()).add(plan.assignments[p.passage_id])
    assert all(len(s) == 1 for s in by_work.values())
    # Approximate genre representation: every split has more than one category.
    for split, counts in plan.category_counts.items():
        assert len(counts) >= 2, (split, counts)


def test_deterministic_for_seed_and_sensitive_to_seed():
    passages = _corpus_80()
    a = plan_splits(passages, TARGETS, seed=7).assignments
    assert a == plan_splits(list(reversed(passages)), TARGETS, seed=7).assignments
    assert a != plan_splits(passages, TARGETS, seed=8).assignments


def test_group_by_author_is_stricter():
    passages = [synthetic_passage(i, f"W{i}", author=f"AUTH{i // 4}") for i in range(20)]
    plan = plan_splits(passages, TARGETS, seed=3, group_by="author")
    by_author: dict[str, set[str]] = {}
    for p in passages:
        by_author.setdefault(p.author_id, set()).add(plan.assignments[p.passage_id])
    assert all(len(s) == 1 for s in by_author.values())


def test_locked_test_passages_stay_in_test():
    passages = _corpus_80()
    locked = {p.passage_id for p in passages[:4]}
    passages = [
        p.model_copy(update={"split": DatasetSplit.TEST}) if p.passage_id in locked else p
        for p in passages
    ]
    for seed in range(5):
        plan = plan_splits(passages, TARGETS, seed=seed)
        assert all(plan.assignments[pid] == "test" for pid in locked)


def test_oversized_group_is_warned_not_split():
    passages = [synthetic_passage(i, "BIG") for i in range(10)] + [
        synthetic_passage(10 + i, f"S{i}") for i in range(4)
    ]
    plan = plan_splits(passages, TARGETS, seed=0)
    assert len({plan.assignments[p.passage_id] for p in passages[:10]}) == 1
    assert plan.warnings


def test_apply_plan_sets_split_field():
    passages = _corpus_80()
    plan = plan_splits(passages, TARGETS, seed=1)
    applied = apply_plan(passages, plan)
    assert Counter(str(p.split) for p in applied) == Counter(plan.achieved)
