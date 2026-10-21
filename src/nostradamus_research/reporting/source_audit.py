"""Report A — Historical Source Audit."""

from __future__ import annotations

from pathlib import Path

from ..models.enums import COMMITTABLE_RIGHTS, STATUS_LADDER, RecordType, VerificationStatus
from ..provenance.audit import ProvenanceAudit
from ..provenance.registry import SourceRegistry
from ..utils.runtime import utc_now
from .common import bullet, md_table, render_template


def render_source_audit(
    registry: SourceRegistry, audit: ProvenanceAudit, template: Path, *, registry_path: str
) -> str:
    sources = list(registry)
    counts = registry.status_counts()
    verified = [s for s in sources if s.verification_status not in (VerificationStatus.CANDIDATE,
                                                                     VerificationStatus.LOCATED,
                                                                     VerificationStatus.REJECTED)]  # fmt: skip
    if not sources:
        banner = "> **EMPTY REGISTRY.** No sources are registered."
    elif not verified:
        banner = (
            f"> **NO SOURCE HAS BEEN AUTHENTICATED.** All {len(sources)} records are at "
            "`candidate` or `located` status. Nothing here establishes the provenance of any witness."
        )
    else:
        banner = (
            f"> {len(verified)} of {len(sources)} records have documented provenance checks or higher. "
            "Statuses rest only on the evidence recorded in the registry."
        )
    if any(str(s.data_origin) == "synthetic_fixture" for s in sources):
        banner += (
            "\n>\n> **This registry contains SYNTHETIC fixture records (not research evidence).**"
        )

    status_rows = [
        (str(st), counts.get(str(st), 0)) for st in (*STATUS_LADDER, VerificationStatus.REJECTED)
    ]
    biblio = md_table(
        ["ID", "Type", "Title", "Author", "Date", "Printer/Publisher", "Place", "Holding", "Status"],
        [(s.source_id, s.record_type, s.title, s.author, s.date_text, s.printer_publisher,
          s.place_of_publication, s.holding_institution, s.verification_status) for s in sources],
    )  # fmt: skip
    verif_rows = []
    for s in sources:
        ev = "; ".join(
            f"{e.evidence_type} by {e.verified_by} on {e.verified_on}"
            for e in s.verification_evidence
        )
        verif_rows.append((s.source_id, s.verification_status, s.stable_url or s.persistent_identifier,
                           s.catalogue_identifier, s.date_accessed, ev or "none recorded"))  # fmt: skip
    witnesses = [s for s in sources if s.record_type is RecordType.WITNESS]
    trans_rows = [(s.source_id, s.title, s.scan_available, s.transcription_available, s.locator,
                   s.verification_status) for s in witnesses]  # fmt: skip
    lic_rows = [(s.source_id, s.rights_status, s.licence, s.rights_notes) for s in sources
                if s.rights_status not in COMMITTABLE_RIGHTS or s.rights_notes]  # fmt: skip
    concerns = [f"`{i.record_id}` [{i.severity}] {i.code}: {i.message}" for i in audit.issues]
    for s in sources:
        for w in s.outstanding_work:
            concerns.append(f"`{s.source_id}` outstanding: {w}")
        if s.uncertainty_notes:
            concerns.append(f"`{s.source_id}` uncertainty: {s.uncertainty_notes}")

    return render_template(
        template,
        banner=banner,
        generated_at=utc_now().isoformat(),
        registry_path=registry_path,
        n_sources=len(sources),
        status_table=md_table(["Status", "Records"], status_rows),
        bibliographic_table=biblio,
        verification_table=md_table(
            ["ID", "Status", "URL / PID", "Catalogue ID", "Accessed", "Evidence"], verif_rows
        ),
        transcription_table=md_table(
            ["ID", "Title", "Scan available", "Transcription available", "Locator", "Status"],
            trans_rows,
        )
        if trans_rows
        else "No witness records.",
        licensing_table=md_table(["ID", "Rights", "Licence", "Notes"], lic_rows)
        if lic_rows
        else "No open licensing issues.",
        concerns=bullet(concerns),
        n_errors=len(audit.errors),
        n_warnings=len(audit.warnings),
    )
