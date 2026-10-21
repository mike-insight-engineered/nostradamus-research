"""Corpus-level provenance and licensing audit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ..models.enums import (
    COMMITTABLE_RIGHTS,
    DataOrigin,
    RecordType,
    TranslatorType,
    VerificationStatus,
    status_rank,
)
from ..models.passage import Passage
from .registry import SourceRegistry


@dataclass(frozen=True)
class AuditIssue:
    severity: Literal["error", "warning"]
    record_id: str
    code: str
    message: str


@dataclass
class ProvenanceAudit:
    issues: list[AuditIssue] = field(default_factory=list)
    n_sources: int = 0
    n_passages: int = 0

    @property
    def errors(self) -> list[AuditIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[AuditIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, severity: Literal["error", "warning"], rid: str, code: str, msg: str) -> None:
        self.issues.append(AuditIssue(severity, rid, code, msg))


def audit_corpus(
    registry: SourceRegistry,
    passages: list[Passage],
    *,
    forbid_synthetic: bool = True,
    minimum_status: VerificationStatus = VerificationStatus.TRANSCRIPTION_VERIFIED,
) -> ProvenanceAudit:
    """Cross-check passages against the source registry and rights policy."""
    audit = ProvenanceAudit(n_sources=len(registry), n_passages=len(passages))

    for src in registry:
        if forbid_synthetic and src.data_origin is DataOrigin.SYNTHETIC_FIXTURE:
            audit.add("error", src.source_id, "synthetic_in_registry",
                      "synthetic fixture source present in the research registry")  # fmt: skip
        if src.verification_status is VerificationStatus.CANDIDATE and not src.outstanding_work:
            audit.add("warning", src.source_id, "no_outstanding_work",
                      "candidate source lists no outstanding verification work")  # fmt: skip
        if src.rights_status not in COMMITTABLE_RIGHTS and src.record_type is RecordType.WITNESS:
            audit.add("warning", src.source_id, "rights_unconfirmed",
                      f"rights status '{src.rights_status}': do not commit scans or long extracts")  # fmt: skip

    seen_ids: set[str] = set()
    for p in passages:
        pid = p.passage_id
        if pid in seen_ids:
            audit.add("error", pid, "duplicate_passage_id", "passage_id appears more than once")
        seen_ids.add(pid)
        if forbid_synthetic and p.data_origin is DataOrigin.SYNTHETIC_FIXTURE:
            audit.add("error", pid, "synthetic_in_corpus",
                      "synthetic fixture passage present in the research corpus")  # fmt: skip
        if p.source_id not in registry:
            audit.add("error", pid, "unknown_source", f"source {p.source_id} is not registered")
            continue
        src = registry.get(p.source_id)
        if src.record_type is not RecordType.WITNESS:
            audit.add("error", pid, "source_not_witness",
                      f"passages must cite a witness record, not a {src.record_type}")  # fmt: skip
        if src.verification_status is VerificationStatus.REJECTED:
            audit.add("error", pid, "rejected_source", "cites a rejected source")
        elif status_rank(p.verification_status) > status_rank(
            src.verification_status
        ) and status_rank(p.verification_status) <= status_rank(
            VerificationStatus.PROVENANCE_CHECKED
        ):
            audit.add("error", pid, "status_exceeds_source",
                      f"passage status '{p.verification_status}' exceeds source status "
                      f"'{src.verification_status}'")  # fmt: skip
        if status_rank(p.verification_status) >= status_rank(
            VerificationStatus.TRANSCRIPTION_VERIFIED
        ) and status_rank(src.verification_status) < status_rank(
            VerificationStatus.PROVENANCE_CHECKED
        ):
            audit.add("error", pid, "unauthenticated_witness",
                      "verified transcription from a witness whose provenance is not checked")  # fmt: skip
        if status_rank(p.verification_status) < status_rank(minimum_status):
            audit.add("warning", pid, "below_inclusion_status",
                      f"status '{p.verification_status}' is below the inclusion minimum "
                      f"'{minimum_status}'; excluded from calibration runs")  # fmt: skip
        if src.rights_status not in COMMITTABLE_RIGHTS:
            audit.add("warning", pid, "transcription_rights",
                      f"source rights '{src.rights_status}': confirm the transcription may be "
                      "stored in this repository")  # fmt: skip
        if p.work_id != (src.work_id or p.work_id):
            audit.add("warning", pid, "work_id_mismatch",
                      f"passage work_id '{p.work_id}' differs from source work_id '{src.work_id}'")  # fmt: skip
        if not p.reference_translations:
            audit.add("warning", pid, "no_references", "no reference translations recorded")
        for ref in p.reference_translations:
            if ref.rights_status not in COMMITTABLE_RIGHTS:
                audit.add("warning", ref.reference_id, "reference_rights",
                          f"reference rights '{ref.rights_status}': confirm before committing text")  # fmt: skip
            if not ref.independent_of_evaluated_models:
                audit.add("error", ref.reference_id, "reference_not_independent",
                          "reference translation is not independent of the evaluated models")  # fmt: skip
            if ref.translator_type is TranslatorType.MACHINE:
                audit.add("error", ref.reference_id, "machine_reference",
                          "machine output cannot serve as a calibration reference")  # fmt: skip
    return audit
