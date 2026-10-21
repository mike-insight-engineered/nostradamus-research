"""Selection of the 20-passage feasibility (pilot) set from eligible passages.

Within each pilot group, passages are drawn round-robin across works (in a
seeded order) so that no single work dominates. Shortfalls are reported, never
filled with ineligible or synthetic passages.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field

from ..config import CorpusConfig
from ..models.enums import DataOrigin
from ..models.passage import Passage
from .stats import is_eligible


@dataclass
class PilotSelection:
    seed: int
    selected: dict[str, list[str]] = field(default_factory=dict)
    shortfall: dict[str, int] = field(default_factory=dict)
    excluded: dict[str, str] = field(default_factory=dict)

    @property
    def complete(self) -> bool:
        return not any(self.shortfall.values())

    def to_dict(self) -> dict[str, object]:
        return {"seed": self.seed, "selected": self.selected, "shortfall": self.shortfall,
                "complete": self.complete, "excluded": self.excluded}  # fmt: skip


def select_pilot(
    passages: list[Passage], cfg: CorpusConfig, *, seed: int, allow_synthetic: bool = False
) -> PilotSelection:
    sel = PilotSelection(seed=seed)
    pools: dict[str, dict[str, list[Passage]]] = defaultdict(lambda: defaultdict(list))
    for p in sorted(passages, key=lambda p: p.passage_id):
        if p.data_origin is DataOrigin.SYNTHETIC_FIXTURE and not allow_synthetic:
            sel.excluded[p.passage_id] = "synthetic fixture"
            continue
        if not is_eligible(p, cfg):
            sel.excluded[p.passage_id] = "not eligible (status or references)"
            continue
        pools[str(p.effective_pilot_group)][p.work_id].append(p)
    rng = random.Random(seed)
    for group, target in cfg.targets.pilot.items():
        works = pools.get(str(group), {})
        order = sorted(works)
        rng.shuffle(order)
        queues = {w: list(works[w]) for w in order}
        chosen: list[str] = []
        while len(chosen) < target and any(queues.values()):
            for w in order:
                if queues[w] and len(chosen) < target:
                    chosen.append(queues[w].pop(0).passage_id)
        sel.selected[str(group)] = chosen
        sel.shortfall[str(group)] = target - len(chosen)
    return sel
