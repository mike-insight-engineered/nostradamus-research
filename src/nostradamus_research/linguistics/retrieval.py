"""Local lexical-evidence retrieval (no hosted vector database).

The store is a JSONL file of :class:`LexicalEvidence` records. Retrieval is a
transparent exact/variant-form match on folded tokens, ranked by match count
and verification status. Entries below the configured status or of synthetic
origin are excluded unless explicitly allowed, and the retrieval outcome says
whether the evidence returned is verified. When nothing verified matches, the
caller must abstain from evidence-dependent claims.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..corpus.io import load_lexical_evidence
from ..models.enums import DataOrigin, VerificationStatus, status_rank
from ..models.evidence import LexicalEvidence
from ..models.translation import RetrievalStatus
from ..utils.hashing import stable_hash
from .segmentation import fold, tokenize


@dataclass
class RetrievalOutcome:
    entries: list[LexicalEvidence] = field(default_factory=list)
    status: RetrievalStatus = "no_evidence"
    excluded_unverified: int = 0
    limitations: list[str] = field(default_factory=list)


class LexicalEvidenceStore:
    def __init__(self, entries: list[LexicalEvidence]):
        self.entries = entries
        self._index: dict[str, list[LexicalEvidence]] = defaultdict(list)
        for e in entries:
            for form in e.all_forms:
                for tok in tokenize(form) or []:
                    self._index[fold(tok.text)].append(e)

    @classmethod
    def from_file(cls, path: Path) -> LexicalEvidenceStore:
        result = load_lexical_evidence(path)
        if result.errors:
            raise ValueError("invalid lexical evidence: " + "; ".join(map(str, result.errors[:5])))
        return cls(result.records)

    def content_hash(self) -> str:
        return stable_hash([e.model_dump(mode="json") for e in self.entries])

    def retrieve(
        self,
        text: str,
        *,
        top_k: int = 5,
        minimum_status: VerificationStatus = VerificationStatus.TRANSCRIPTION_VERIFIED,
        allow_synthetic: bool = False,
    ) -> RetrievalOutcome:
        hits: dict[str, int] = defaultdict(int)
        by_id: dict[str, LexicalEvidence] = {}
        for tok in tokenize(text):
            for e in self._index.get(fold(tok.text), []):
                hits[e.evidence_id] += 1
                by_id[e.evidence_id] = e

        outcome = RetrievalOutcome()
        eligible: list[LexicalEvidence] = []
        for eid in hits:
            e = by_id[eid]
            synthetic = e.data_origin is DataOrigin.SYNTHETIC_FIXTURE
            verified = status_rank(e.verification_status) >= status_rank(minimum_status)
            if (synthetic and allow_synthetic) or (not synthetic and verified):
                eligible.append(e)
            else:
                outcome.excluded_unverified += 1
        eligible.sort(
            key=lambda e: (-hits[e.evidence_id], -status_rank(e.verification_status), e.evidence_id)
        )
        outcome.entries = eligible[:top_k]

        if not outcome.entries:
            outcome.status = "no_evidence"
            outcome.limitations.append(
                "No verified historical lexical evidence matched this passage; "
                "evidence-dependent claims were not permitted."
            )
        elif any(e.data_origin is DataOrigin.SYNTHETIC_FIXTURE for e in outcome.entries):
            outcome.status = "unverified_or_synthetic_evidence"
            outcome.limitations.append(
                "Retrieved evidence includes SYNTHETIC fixture entries (software demonstration only)."
            )
        else:
            outcome.status = "verified_evidence"
        if outcome.excluded_unverified:
            outcome.limitations.append(
                f"{outcome.excluded_unverified} matching evidence entr(y/ies) excluded as unverified."
            )
        return outcome
