from datetime import date

import pytest
from pydantic import ValidationError

from nostradamus_research.models.enums import EvidenceType, RecordType, VerificationStatus
from nostradamus_research.models.source import HistoricalSource, VerificationEvidence
from nostradamus_research.provenance.registry import RegistryError, SourceRegistry


def _src(**kw):
    data = {"source_id": "SRC-TEST-ONE", "record_type": "witness", "title": "Test witness"}
    data.update(kw)
    return HistoricalSource.model_validate(data)


def _ev(etype, status, by="Verifier A"):
    return VerificationEvidence(
        evidence_type=etype,
        supports_status=status,
        verified_by=by,
        verified_on=date(2026, 1, 1),
        description="Checked against record in detail.",
    )


def test_candidate_needs_no_evidence():
    assert _src().verification_status is VerificationStatus.CANDIDATE


def test_located_requires_identifier_and_access_date():
    with pytest.raises(ValidationError, match="located"):
        _src(verification_status="located")
    s = _src(
        verification_status="located",
        stable_url="https://example.org/x",
        date_accessed="2026-01-01",
    )
    assert s.verification_status is VerificationStatus.LOCATED


def test_provenance_checked_requires_catalogue_evidence():
    base = {
        "stable_url": "https://example.org/x",
        "date_accessed": "2026-01-01",
        "holding_institution": "Library",
        "catalogue_identifier": "CAT-1",
    }
    with pytest.raises(ValidationError, match="catalogue_record"):
        _src(verification_status="provenance_checked", **base)
    s = _src(
        verification_status="provenance_checked",
        verification_evidence=[
            _ev(EvidenceType.CATALOGUE_RECORD, VerificationStatus.PROVENANCE_CHECKED)
        ],
        **base,
    )
    assert s.verification_status is VerificationStatus.PROVENANCE_CHECKED


def test_transcription_verified_not_allowed_for_reference_works():
    with pytest.raises(ValidationError, match="only to witness"):
        _src(
            source_id="RES-X",
            record_type="reference_work",
            verification_status="transcription_verified",
            stable_url="u",
            date_accessed="2026-01-01",
            verification_evidence=[
                _ev(EvidenceType.OTHER, VerificationStatus.TRANSCRIPTION_VERIFIED)
            ],
        )


def test_expert_must_differ_from_transcription_checker():
    evidence = [
        _ev(EvidenceType.CATALOGUE_RECORD, VerificationStatus.PROVENANCE_CHECKED),
        _ev(
            EvidenceType.TRANSCRIPTION_CHECK,
            VerificationStatus.TRANSCRIPTION_VERIFIED,
            by="Same Person",
        ),
        _ev(EvidenceType.EXPERT_REVIEW, VerificationStatus.EXPERT_REVIEWED, by="Same Person"),
    ]
    kw = {
        "stable_url": "u",
        "date_accessed": "2026-01-01",
        "holding_institution": "L",
        "catalogue_identifier": "C",
        "locator": "f. 12r",
        "verification_status": "expert_reviewed",
    }
    with pytest.raises(ValidationError, match="someone other"):
        _src(verification_evidence=evidence, **kw)
    evidence[2] = _ev(
        EvidenceType.EXPERT_REVIEW, VerificationStatus.EXPERT_REVIEWED, by="Other Expert"
    )
    assert (
        _src(verification_evidence=evidence, **kw).verification_status
        is VerificationStatus.EXPERT_REVIEWED
    )


def test_synthetic_prefix_rule():
    with pytest.raises(ValidationError, match="SYN-"):
        _src(source_id="SYN-X")
    with pytest.raises(ValidationError, match="SYN-"):
        _src(data_origin="synthetic_fixture")


def test_registry_promotion_is_one_rung_at_a_time():
    reg = SourceRegistry([_src()])
    with pytest.raises(RegistryError, match="one rung"):
        reg.promote(
            "SRC-TEST-ONE",
            VerificationStatus.PROVENANCE_CHECKED,
            changed_by="Alice",
            reason="skip ahead",
        )
    with pytest.raises(RegistryError, match="date_accessed"):
        reg.promote(
            "SRC-TEST-ONE",
            VerificationStatus.LOCATED,
            changed_by="Alice",
            reason="found it",
            updates={"stable_url": "https://example.org"},
        )
    s = reg.promote(
        "SRC-TEST-ONE",
        VerificationStatus.LOCATED,
        changed_by="Alice",
        reason="found it",
        updates={"stable_url": "https://example.org", "date_accessed": date(2026, 1, 2)},
    )
    assert s.verification_status is VerificationStatus.LOCATED
    assert s.status_history[-1].from_status is VerificationStatus.CANDIDATE
    # demotion is always allowed
    s = reg.promote(
        "SRC-TEST-ONE", VerificationStatus.REJECTED, changed_by="Alice", reason="not authentic"
    )
    assert s.verification_status is VerificationStatus.REJECTED


def test_register_refuses_high_status_and_duplicates(tmp_path):
    reg = SourceRegistry(path=tmp_path / "r.jsonl")
    reg.register(_src())
    with pytest.raises(RegistryError, match="duplicate"):
        reg.register(_src())
    s = _src(
        source_id="SRC-TEST-TWO",
        verification_status="provenance_checked",
        stable_url="u",
        date_accessed="2026-01-01",
        holding_institution="L",
        catalogue_identifier="C",
        verification_evidence=[
            _ev(EvidenceType.CATALOGUE_RECORD, VerificationStatus.PROVENANCE_CHECKED)
        ],
    )
    with pytest.raises(RegistryError, match="promote"):
        reg.register(s)
    reg.save()
    loaded, errors = SourceRegistry.load(tmp_path / "r.jsonl")
    assert not errors and len(loaded) == 1


def test_project_registry_is_valid_and_unverified(cfg):
    reg, errors = SourceRegistry.load(cfg.path("source_registry"))
    assert not errors
    assert len(reg) >= 7
    # Integrity: no record is claimed beyond 'located' (found and accessed); provenance checks and
    # above require evidence recorded by a named person, which does not yet exist.
    assert all(
        s.verification_status in (VerificationStatus.CANDIDATE, VerificationStatus.LOCATED)
        for s in reg
    )
    assert all(s.date_accessed for s in reg if s.verification_status is VerificationStatus.LOCATED)
    titles = " ".join(s.title for s in reg)
    for resource in (
        "Bibliothèques Virtuelles Humanistes",
        "Gallica",
        "Moyen Français",
        "Huguet",
        "Frantext",
        "Perseus",
    ):
        assert resource in titles
    assert all(s.outstanding_work for s in reg)
    assert any(s.record_type is RecordType.WITNESS for s in reg)


def test_invalid_registry_lines_are_reported_with_line_numbers(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text(
        '{"source_id": "SRC-OK", "record_type": "witness", "title": "ok"}\n'
        '{"source_id": "bad id", "record_type": "witness", "title": "x"}\nnot json\n',
        encoding="utf-8",
    )
    reg, errors = SourceRegistry.load(path)
    assert len(reg) == 1
    assert {e.line for e in errors} == {2, 3}
    assert any("source_id" in e.message for e in errors)
