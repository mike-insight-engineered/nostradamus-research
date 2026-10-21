"""Corpus statistics compared against composition targets."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ..config import CorpusConfig
from ..models.enums import TargetLanguage, VerificationStatus, status_rank
from ..models.passage import Passage


@dataclass
class TargetProgress:
    label: str
    target: int
    eligible: int
    total: int

    @property
    def met(self) -> bool:
        return self.eligible >= self.target


@dataclass
class CorpusStats:
    n_passages: int
    n_eligible: int
    by_category: Counter[str] = field(default_factory=Counter)
    by_status: Counter[str] = field(default_factory=Counter)
    by_split: Counter[str] = field(default_factory=Counter)
    by_origin: Counter[str] = field(default_factory=Counter)
    n_works: int = 0
    n_authors: int = 0
    references_fr: int = 0
    references_en: int = 0
    pilot_progress: list[TargetProgress] = field(default_factory=list)
    full_progress: list[TargetProgress] = field(default_factory=list)


def is_eligible(p: Passage, cfg: CorpusConfig) -> bool:
    """Eligible = verified to the inclusion minimum with enough references in both languages."""
    min_status = VerificationStatus(cfg.inclusion.minimum_passage_status)
    n_refs = cfg.inclusion.minimum_references_per_language
    return (
        status_rank(p.verification_status) >= status_rank(min_status)
        and len(p.references_for(TargetLanguage.MODERN_FRENCH)) >= n_refs
        and len(p.references_for(TargetLanguage.ENGLISH)) >= n_refs
    )


def compute_stats(passages: list[Passage], cfg: CorpusConfig) -> CorpusStats:
    eligible = [p for p in passages if is_eligible(p, cfg)]
    stats = CorpusStats(n_passages=len(passages), n_eligible=len(eligible))
    for p in passages:
        stats.by_category[str(p.category)] += 1
        stats.by_status[str(p.verification_status)] += 1
        stats.by_split[str(p.split)] += 1
        stats.by_origin[str(p.data_origin)] += 1
        stats.references_fr += len(p.references_for(TargetLanguage.MODERN_FRENCH))
        stats.references_en += len(p.references_for(TargetLanguage.ENGLISH))
    stats.n_works = len({p.work_id for p in passages})
    stats.n_authors = len({p.group_key_author for p in passages})

    pilot_all = Counter(str(p.effective_pilot_group) for p in passages)
    pilot_ok = Counter(str(p.effective_pilot_group) for p in eligible)
    for group, target in cfg.targets.pilot.items():
        stats.pilot_progress.append(
            TargetProgress(str(group), target, pilot_ok[str(group)], pilot_all[str(group)])
        )
    full_ok = Counter(str(p.category) for p in eligible)
    for cat, target in cfg.targets.full_corpus.items():
        stats.full_progress.append(
            TargetProgress(str(cat), target, full_ok[str(cat)], stats.by_category[str(cat)])
        )
    return stats
