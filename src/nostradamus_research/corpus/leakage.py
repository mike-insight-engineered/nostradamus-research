"""Duplicate and leakage detection across dataset partitions and retrieval material.

Pretraining contamination (a model having seen a text or its translation during
training) cannot be detected here and is documented as a limitation; these
checks cover what *this project* controls.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Literal

from ..models.enums import DatasetSplit
from ..models.evidence import LexicalEvidence
from ..models.passage import Passage

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_WS = re.compile(r"\s+")


def comparison_key(text: str) -> str:
    """Aggressively folded form used ONLY for similarity comparison, never stored."""
    t = unicodedata.normalize("NFKC", text).replace("ſ", "s").casefold()
    t = _PUNCT.sub(" ", t)
    return _WS.sub(" ", t).strip()


def shingles(text: str, k: int) -> set[str]:
    t = comparison_key(text)
    if len(t) <= k:
        return {t} if t else set()
    return {t[i : i + k] for i in range(len(t) - k + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def containment(needle: set[str], haystack: set[str]) -> float:
    """Fraction of ``needle`` shingles found in ``haystack`` (detects quoted excerpts)."""
    return len(needle & haystack) / len(needle) if needle else 0.0


@dataclass(frozen=True)
class LeakageFinding:
    severity: Literal["error", "warning"]
    code: str
    ids: tuple[str, ...]
    detail: str


@dataclass
class LeakageReport:
    findings: list[LeakageFinding] = field(default_factory=list)

    @property
    def errors(self) -> list[LeakageFinding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def ok(self) -> bool:
        return not self.errors


def check_leakage(
    passages: list[Passage],
    *,
    assignments: dict[str, str] | None = None,
    evidence: list[LexicalEvidence] | None = None,
    near_duplicate_threshold: float = 0.8,
    shingle_size: int = 5,
    group_by: Literal["work_id", "author"] = "work_id",
) -> LeakageReport:
    report = LeakageReport()
    split_of = {p.passage_id: (assignments or {}).get(p.passage_id, str(p.split)) for p in passages}
    sh = {p.passage_id: shingles(p.diplomatic_transcription, shingle_size) for p in passages}

    # 1. exact and near duplicates (any split)
    exact: dict[str, list[str]] = defaultdict(list)
    for p in passages:
        exact[comparison_key(p.diplomatic_transcription)].append(p.passage_id)
    for ids in exact.values():
        if len(ids) > 1:
            report.findings.append(
                LeakageFinding(
                    "error", "exact_duplicate", tuple(sorted(ids)), "identical text after folding"
                )
            )
    exact_pairs = {tuple(sorted(ids[:2])) for ids in exact.values() if len(ids) > 1}
    for a, b in combinations(sorted(sh), 2):
        if (a, b) in exact_pairs:
            continue
        sim = jaccard(sh[a], sh[b])
        if sim >= near_duplicate_threshold:
            cross = split_of[a] != split_of[b]
            report.findings.append(
                LeakageFinding(
                    "error" if cross else "warning",
                    "near_duplicate",
                    (a, b),
                    f"Jaccard {sim:.2f} ({split_of[a]} / {split_of[b]})",
                )
            )

    # 2. shared work/author/witness across partitions
    def _cross(attr: str, key_fn, severity: Literal["error", "warning"]) -> None:  # type: ignore[no-untyped-def]
        by_key: dict[str, set[str]] = defaultdict(set)
        members: dict[str, list[str]] = defaultdict(list)
        for p in passages:
            s = split_of[p.passage_id]
            if s == str(DatasetSplit.UNASSIGNED):
                continue
            k = key_fn(p)
            by_key[k].add(s)
            members[k].append(p.passage_id)
        for k, splits in by_key.items():
            if len(splits) > 1:
                report.findings.append(
                    LeakageFinding(
                        severity,
                        f"shared_{attr}",
                        tuple(sorted(members[k])),
                        f"{attr} '{k}' spans {sorted(splits)}",
                    )
                )

    _cross("work", lambda p: p.work_id, "error")
    _cross("author", lambda p: p.group_key_author, "error" if group_by == "author" else "warning")
    _cross("source", lambda p: p.source_id, "warning")

    # 3. held-out references / text appearing in non-test material
    test_ids = [pid for pid, s in split_of.items() if s == str(DatasetSplit.TEST)]
    by_id = {p.passage_id: p for p in passages}
    other_texts: list[tuple[str, set[str]]] = []
    for p in passages:
        if split_of[p.passage_id] != str(DatasetSplit.TEST):
            for r in p.reference_translations:
                other_texts.append((r.reference_id, shingles(r.text, shingle_size)))
    for tid in test_ids:
        for r in by_id[tid].reference_translations:
            rs = shingles(r.text, shingle_size)
            for oid, os_ in other_texts:
                if jaccard(rs, os_) >= near_duplicate_threshold:
                    report.findings.append(
                        LeakageFinding(
                            "error",
                            "test_reference_leak",
                            (r.reference_id, oid),
                            "held-out reference near-duplicates a non-test reference",
                        )
                    )

    # 4. retrieval material overlapping held-out text or references
    for ev in evidence or []:
        texts = [t for t in (ev.quotation, ev.sense) if t]
        for tid in test_ids:
            tp = by_id[tid]
            targets = [("text", sh[tid])] + [
                (r.reference_id, shingles(r.text, shingle_size)) for r in tp.reference_translations
            ]
            for t in texts:
                es = shingles(t, shingle_size)
                for label, target in targets:
                    if len(es) >= 3 and containment(es, target) >= near_duplicate_threshold:
                        report.findings.append(
                            LeakageFinding(
                                "error",
                                "retrieval_overlaps_test",
                                (ev.evidence_id, tid),
                                f"evidence text overlaps held-out {label}",
                            )
                        )
    return report
