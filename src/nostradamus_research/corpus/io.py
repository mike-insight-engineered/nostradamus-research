"""Loading passages and lexical evidence; dataset versioning."""

from __future__ import annotations

from pathlib import Path

from ..models.evidence import LexicalEvidence
from ..models.passage import Passage
from ..utils.hashing import stable_hash
from ..utils.jsonl import LoadResult, RecordError, load_models


def load_passages(path: Path) -> LoadResult[Passage]:
    result = load_models(path, Passage, "passage_id")
    seen: set[str] = set()
    for p in result.records:
        if p.passage_id in seen:
            result.errors.append(RecordError(str(path), 0, p.passage_id, "duplicate passage_id"))
        seen.add(p.passage_id)
    return result


def load_lexical_evidence(path: Path) -> LoadResult[LexicalEvidence]:
    if not path.exists():
        return LoadResult()
    return load_models(path, LexicalEvidence, "evidence_id")


def dataset_version(passages: list[Passage]) -> str:
    """Content hash of a passage set, independent of file order and formatting."""
    payload = sorted(
        (p.model_dump(mode="json") for p in passages), key=lambda d: str(d["passage_id"])
    )
    return stable_hash(payload)
