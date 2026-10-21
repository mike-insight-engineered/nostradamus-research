from nostradamus_research.linguistics.language_id import identify
from nostradamus_research.linguistics.morphology import hints
from nostradamus_research.linguistics.retrieval import LexicalEvidenceStore
from nostradamus_research.linguistics.segmentation import clauses, fold, tokenize
from nostradamus_research.models.enums import Language, VerificationStatus
from nostradamus_research.models.evidence import LexicalEvidence


def test_tokenize_preserves_spans():
    text = "Ceſte annee, l'homme"
    toks = tokenize(text)
    assert [t.text for t in toks] == ["Ceſte", "annee", "l'homme"]
    assert all(text[t.start : t.end] == t.text for t in toks)
    assert fold("l'Homme") == "homme" and fold("Ceſte") == "ceste"


def test_clauses_split_on_punctuation_and_lines():
    assert clauses("Quand le ſoleil, il dict: rien.\nEt puis / fin") == [
        "Quand le ſoleil",
        "il dict",
        "rien",
        "Et puis",
        "fin",
    ]


def test_language_identification():
    assert (
        identify(
            "Le clerc eſcript vne lettre a ſon maiſtre, & luy dict que le vent eſtoit froid."
        ).language
        is Language.MIDDLE_FRENCH
    )
    assert (
        identify("Magister discipulis dixit sed tempus fugit, neque enim hic est.").language
        is Language.LATIN
    )
    mixed = identify("Le docteur dict que nous sommes, sed tempus fugit atque hic est non ad nos.")
    assert mixed.language is Language.MIXED
    assert mixed.code_switch_spans
    assert identify("12345").language is Language.OTHER


def test_morphology_hints_are_flags():
    found = {(h.form, h.hint.split()[0]) for h in hints("il eſtoit faict", Language.MIDDLE_FRENCH)}
    assert any(f == "faict" for f, _ in found)
    assert any(h.form == "mercatorum" for h in hints("mercatorum", Language.LATIN))


def _ev(eid, status="candidate", origin="historical_source", **kw):
    data = {
        "evidence_id": eid,
        "data_origin": origin,
        "kind": "dictionary_entry",
        "headword": "bled",
        "language": "frm",
        "sense": "grain",
        "citation": "Test citation for unit tests",
        "verification_status": status,
    }
    data.update(kw)
    return LexicalEvidence.model_validate(data)


def test_retrieval_excludes_unverified_and_synthetic_by_default():
    verified = _ev(
        "LEX-V1",
        "transcription_verified",
        locator="p. 1",
        verified_by="Checker",
        verified_on="2026-01-01",
    )
    store = LexicalEvidenceStore(
        [_ev("LEX-U1"), verified, _ev("SYN-LEX-1", origin="synthetic_fixture")]
    )
    out = store.retrieve("les bled furent bons")
    assert [e.evidence_id for e in out.entries] == ["LEX-V1"]
    assert out.status == "verified_evidence" and out.excluded_unverified == 2
    out = store.retrieve("les bled furent bons", allow_synthetic=True)
    assert "SYN-LEX-1" in [e.evidence_id for e in out.entries]
    assert out.status == "unverified_or_synthetic_evidence"


def test_retrieval_abstains_when_nothing_verified():
    out = LexicalEvidenceStore([_ev("LEX-U1")]).retrieve(
        "bled", minimum_status=VerificationStatus.TRANSCRIPTION_VERIFIED
    )
    assert out.entries == [] and out.status == "no_evidence"
    assert any("not permitted" in m for m in out.limitations)


def test_verified_evidence_requires_named_verifier():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="verified_by"):
        _ev("LEX-X", "transcription_verified", locator="p. 1")


def test_project_evidence_store_contains_no_fabricated_entries(cfg):
    path = cfg.path("lexical_evidence")
    assert path.exists()
    assert (
        path.read_text(encoding="utf-8").strip() == ""
    )  # empty until a person adds checked entries
