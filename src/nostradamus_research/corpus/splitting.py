"""Deterministic, group-aware dataset partitioning.

Passages are grouped (by ``work_id`` or author) and whole groups are assigned to
development / validation / test, so related passages never straddle partitions.
Group order is fixed by a seeded shuffle; assignment is greedy towards the
largest proportional deficit with a mild preference for category balance.

Held-out protection: any group that already contains a ``test`` passage stays in
``test`` (``respect_test_lock``), so re-running the splitter can never
reshuffle a frozen test set into development.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Literal

from ..models.enums import DatasetSplit
from ..models.passage import Passage
from ..utils.hashing import stable_hash

SPLITS = (DatasetSplit.DEVELOPMENT, DatasetSplit.VALIDATION, DatasetSplit.TEST)


@dataclass
class SplitPlan:
    seed: int
    group_by: str
    targets: dict[str, int]
    assignments: dict[str, str]
    achieved: dict[str, int]
    category_counts: dict[str, dict[str, int]]
    groups: dict[str, str]
    warnings: list[str] = field(default_factory=list)
    dataset_sha256: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "group_by": self.group_by,
            "targets": self.targets,
            "achieved": self.achieved,
            "category_counts": self.category_counts,
            "groups": self.groups,
            "assignments": self.assignments,
            "warnings": self.warnings,
            "dataset_sha256": self.dataset_sha256,
            "plan_sha256": stable_hash(self.assignments),
        }


def scale_targets(base: dict[str, int], n: int) -> dict[str, int]:
    """Scale target counts to ``n`` passages with largest-remainder rounding."""
    total = sum(base.values())
    if total == 0 or n == 0:
        return dict.fromkeys(base, 0)
    raw = {k: v * n / total for k, v in base.items()}
    floors = {k: int(v) for k, v in raw.items()}
    remaining = n - sum(floors.values())
    for k in sorted(raw, key=lambda k: (raw[k] - floors[k], base[k]), reverse=True)[:remaining]:
        floors[k] += 1
    return floors


def group_key(p: Passage, group_by: Literal["work_id", "author"]) -> str:
    return p.work_id if group_by == "work_id" else p.group_key_author


def plan_splits(
    passages: list[Passage],
    targets: dict[str, int],
    *,
    seed: int,
    group_by: Literal["work_id", "author"] = "work_id",
    respect_test_lock: bool = True,
) -> SplitPlan:
    scaled = scale_targets(targets, len(passages))
    groups: dict[str, list[Passage]] = defaultdict(list)
    for p in sorted(passages, key=lambda p: p.passage_id):
        groups[group_key(p, group_by)].append(p)

    order = sorted(groups)
    random.Random(seed).shuffle(order)
    # Larger groups first (stable w.r.t. the seeded order) so they place cleanly.
    order.sort(key=lambda g: len(groups[g]), reverse=True)

    current: Counter[str] = Counter()
    cat_counts: dict[str, Counter[str]] = {str(s): Counter() for s in SPLITS}
    group_assign: dict[str, str] = {}
    warnings: list[str] = []

    locked = {
        g for g, members in groups.items()
        if respect_test_lock and any(m.split is DatasetSplit.TEST for m in members)
    }  # fmt: skip
    for g in sorted(locked):
        group_assign[g] = str(DatasetSplit.TEST)
        current[str(DatasetSplit.TEST)] += len(groups[g])
        for m in groups[g]:
            cat_counts[str(DatasetSplit.TEST)][str(m.category)] += 1
    if locked:
        warnings.append(
            f"{len(locked)} group(s) kept in test because they contain locked test passages"
        )

    for g in order:
        if g in group_assign:
            continue
        members = groups[g]
        size = len(members)
        main_cat = Counter(str(m.category) for m in members).most_common(1)[0][0]
        candidates = [str(s) for s in SPLITS if scaled[str(s)] > 0] or [
            str(DatasetSplit.DEVELOPMENT)
        ]
        fitting = [s for s in candidates if current[s] + size <= scaled[s]]
        pool = fitting or candidates

        def score(s: str, *, _size: int = size, _cat: str = main_cat) -> tuple[float, float, int]:
            target = max(scaled[s], 1)
            deficit = (scaled[s] - current[s]) / target
            assigned = sum(cat_counts[s].values())
            share = cat_counts[s][_cat] / assigned if assigned else 0.0
            return (
                deficit - 0.25 * share,
                -abs(scaled[s] - current[s] - _size),
                -SPLITS.index(DatasetSplit(s)),
            )

        choice = max(pool, key=score)
        if not fitting:
            warnings.append(
                f"group '{g}' ({size} passages) exceeds remaining capacity; placed in {choice}"
            )
        group_assign[g] = choice
        current[choice] += size
        for m in members:
            cat_counts[choice][str(m.category)] += 1

    assignments = {m.passage_id: group_assign[g] for g, members in groups.items() for m in members}
    for s in SPLITS:
        if current[str(s)] != scaled[str(s)]:
            warnings.append(
                f"{s}: achieved {current[str(s)]} vs scaled target {scaled[str(s)]} "
                "(group isolation takes priority over exact sizes)"
            )
    return SplitPlan(
        seed=seed,
        group_by=group_by,
        targets=scaled,
        assignments=dict(sorted(assignments.items())),
        achieved={str(s): current[str(s)] for s in SPLITS},
        category_counts={s: dict(sorted(c.items())) for s, c in cat_counts.items()},
        groups=dict(sorted(group_assign.items())),
        warnings=warnings,
    )


def apply_plan(passages: list[Passage], plan: SplitPlan) -> list[Passage]:
    """Return copies of ``passages`` with ``split`` set from ``plan``."""
    return [
        p.model_copy(update={"split": DatasetSplit(plan.assignments[p.passage_id])})
        if p.passage_id in plan.assignments
        else p
        for p in passages
    ]
