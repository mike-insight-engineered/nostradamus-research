"""Evidence requirements for each verification status.

This module is the single machine-readable statement of the policy described in
``docs/source-authentication.md``. Requirements are cumulative: a record at
``transcription_verified`` must also satisfy ``located`` and
``provenance_checked``. The checks operate on plain attributes to avoid import
cycles; they are invoked by model validators and by the registry.
"""

from __future__ import annotations

from typing import Any, Protocol

from .enums import EvidenceType, RecordType, VerificationStatus, status_rank


class _Evidence(Protocol):
    evidence_type: EvidenceType
    verified_by: str
    supports_status: VerificationStatus


def _evidence_for(
    evidence: list[Any], status: VerificationStatus, types: set[EvidenceType]
) -> list[_Evidence]:
    return [
        e
        for e in evidence
        if e.evidence_type in types and status_rank(e.supports_status) >= status_rank(status)
    ]


def source_status_problems(source: Any) -> list[str]:
    """Return unmet requirements for ``source.verification_status`` (empty if OK)."""
    status: VerificationStatus = source.verification_status
    problems: list[str] = []
    if status is VerificationStatus.REJECTED:
        if not (source.notes or source.status_history):
            problems.append(
                "status 'rejected' requires notes or a status_history entry giving the reason"
            )
        return problems

    rank = status_rank(status)
    evidence = list(source.verification_evidence)
    is_witness = source.record_type is RecordType.WITNESS

    if rank >= status_rank(VerificationStatus.LOCATED):
        if not (source.stable_url or source.persistent_identifier or source.catalogue_identifier):
            problems.append(
                "status 'located' requires stable_url, persistent_identifier or catalogue_identifier"
            )
        if source.date_accessed is None:
            problems.append("status 'located' requires date_accessed")

    if rank >= status_rank(VerificationStatus.PROVENANCE_CHECKED):
        if is_witness:
            if not source.holding_institution:
                problems.append("status 'provenance_checked' requires holding_institution")
            if not source.catalogue_identifier:
                problems.append("status 'provenance_checked' requires catalogue_identifier")
            if not _evidence_for(
                evidence, VerificationStatus.PROVENANCE_CHECKED, {EvidenceType.CATALOGUE_RECORD}
            ):
                problems.append(
                    "status 'provenance_checked' requires catalogue_record evidence matching "
                    "the edition, printer and date of this witness"
                )
        elif not _evidence_for(evidence, VerificationStatus.PROVENANCE_CHECKED, set(EvidenceType)):
            problems.append(
                "status 'provenance_checked' requires documented evidence for this resource"
            )

    if rank >= status_rank(VerificationStatus.TRANSCRIPTION_VERIFIED):
        if not is_witness:
            problems.append(
                f"status '{status}' applies only to witness records, not {source.record_type}"
            )
        else:
            if not source.locator:
                problems.append("status 'transcription_verified' requires a page/folio locator")
            if not _evidence_for(
                evidence,
                VerificationStatus.TRANSCRIPTION_VERIFIED,
                {EvidenceType.TRANSCRIPTION_CHECK},
            ):
                problems.append(
                    "status 'transcription_verified' requires transcription_check evidence "
                    "against facsimile images"
                )

    if rank >= status_rank(VerificationStatus.EXPERT_REVIEWED):
        experts = _evidence_for(
            evidence, VerificationStatus.EXPERT_REVIEWED, {EvidenceType.EXPERT_REVIEW}
        )
        if not experts:
            problems.append("status 'expert_reviewed' requires expert_review evidence")
        else:
            checkers = {
                e.verified_by
                for e in evidence
                if e.evidence_type is EvidenceType.TRANSCRIPTION_CHECK
            }
            if all(e.verified_by in checkers for e in experts):
                problems.append(
                    "expert_review evidence must come from someone other than the "
                    "transcription checker"
                )
    return problems


def allowed_transition(current: VerificationStatus, new: VerificationStatus) -> bool:
    """Promotion moves one rung at a time; demotion or rejection is always allowed."""
    if new is VerificationStatus.REJECTED or status_rank(new) <= status_rank(current):
        return True
    if current is VerificationStatus.REJECTED:
        return new is VerificationStatus.CANDIDATE
    return status_rank(new) == status_rank(current) + 1
