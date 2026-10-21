"""Detection of silent changes to diplomatic transcriptions."""

from __future__ import annotations

from dataclasses import dataclass

from ..models.passage import Passage
from ..utils.hashing import sha256_text


@dataclass(frozen=True)
class TranscriptionChange:
    passage_id: str
    field: str
    detail: str


def lock_hash(text: str) -> str:
    """Hash to store in ``diplomatic_sha256`` when a transcription is first registered."""
    return sha256_text(text)


def compare_corpora(old: list[Passage], new: list[Passage]) -> list[TranscriptionChange]:
    """List passages whose diplomatic transcription changed between two corpus versions.

    Any change must be accompanied by a ``transcription_checked`` or ``comment``
    review event explaining the correction; otherwise it is reported.
    """
    before = {p.passage_id: p for p in old}
    changes: list[TranscriptionChange] = []
    for p in new:
        prev = before.get(p.passage_id)
        if prev is None or prev.diplomatic_sha256 == p.diplomatic_sha256:
            continue
        documented = len(p.review_history) > len(prev.review_history) and any(
            e.action in ("transcription_checked", "comment")
            for e in p.review_history[len(prev.review_history) :]
        )
        changes.append(
            TranscriptionChange(
                p.passage_id,
                "diplomatic_transcription",
                "documented correction" if documented else "UNDOCUMENTED change",
            )
        )
    return changes
