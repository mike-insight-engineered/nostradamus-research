import pytest
from pydantic import ValidationError

from nostradamus_research.corpus.io import load_passages
from nostradamus_research.models.passage import Passage
from nostradamus_research.models.reference import ReferenceTranslation
from nostradamus_research.utils.hashing import sha256_text
from tests.conftest import TEST_FIXTURES, historical_passage_dict


def _ref(**kw):
    data = {
        "reference_id": "REF-1",
        "passage_id": "PSG-TEST-001",
        "target_language": "en",
        "text": "x",
        "translator": "Dr Example",
        "translator_type": "human_expert",
        "independent_of_evaluated_models": True,
    }
    data.update(kw)
    return data


def test_valid_passage(passage_dict):
    p = Passage.model_validate(passage_dict)
    assert p.effective_pilot_group.value == "french_prose"


def test_diplomatic_text_preserved_exactly():
    text = "  Ceſte  annee,&c.  \n"
    p = Passage.model_validate(historical_passage_dict(diplomatic_transcription=text))
    assert p.diplomatic_transcription == text


def test_silent_modification_is_detected(passage_dict):
    passage_dict["diplomatic_transcription"] = passage_dict["diplomatic_transcription"].replace(
        "ſ", "s"
    )
    with pytest.raises(ValidationError, match="does not match diplomatic_sha256"):
        Passage.model_validate(passage_dict)


def test_category_must_match_language_and_genre(passage_dict):
    passage_dict["category"] = "latin_prose"
    with pytest.raises(ValidationError, match="inconsistent"):
        Passage.model_validate(passage_dict)


def test_normalised_reading_requires_rules(passage_dict):
    passage_dict["normalised_reading"] = "Texte d'essai sans valeur historique."
    with pytest.raises(ValidationError, match="no silent normalisation"):
        Passage.model_validate(passage_dict)
    passage_dict["normalisation_rules"] = ["long_s"]
    assert Passage.model_validate(passage_dict).normalised_reading


def test_verified_status_requires_locator_facsimile_and_check(passage_dict):
    passage_dict["verification_status"] = "transcription_verified"
    with pytest.raises(ValidationError) as exc:
        Passage.model_validate(passage_dict)
    msg = str(exc.value)
    assert "locator" in msg and "facsimile_reference" in msg and "transcription_checked" in msg
    passage_dict.update(
        locator="sig. A2r",
        facsimile_reference="https://example.org/img",
        review_history=[{"on": "2026-01-01", "by": "Checker", "action": "transcription_checked"}],
    )
    assert Passage.model_validate(passage_dict)


def test_multiple_references_and_wrong_passage(passage_dict):
    passage_dict["reference_translations"] = [_ref(), _ref(reference_id="REF-2", text="y")]
    assert len(Passage.model_validate(passage_dict).references_for("en")) == 2
    passage_dict["reference_translations"] = [_ref(passage_id="PSG-OTHER")]
    with pytest.raises(ValidationError, match="belongs to passage"):
        Passage.model_validate(passage_dict)


def test_machine_reference_cannot_be_independent():
    with pytest.raises(ValidationError, match="machine"):
        ReferenceTranslation.model_validate(_ref(translator_type="machine"))
    with pytest.raises(ValidationError, match="source_citation"):
        ReferenceTranslation.model_validate(_ref(translator_type="published_edition"))


def test_interpretations_kept_separate_from_assertions(passage_dict):
    passage_dict["historical_assertions"] = [
        {"statement": "s", "evidence": ["cat. rec."], "asserted_by": "A", "status": "verified"}
    ]
    passage_dict["proposed_interpretations"] = [
        {"statement": "i", "proposed_by": "B", "rationale": "r"}
    ]
    p = Passage.model_validate(passage_dict)
    assert p.proposed_interpretations[0].quality_dimension == "QC3"
    assert p.proposed_interpretations[0].evidence_strength == "unassessed"
    with pytest.raises(ValidationError):
        Passage.model_validate(
            {
                **passage_dict,
                "historical_assertions": [
                    {"statement": "s", "evidence": [], "asserted_by": "A", "status": "verified"}
                ],
            }
        )


def test_incomplete_and_invalid_records_report_line_and_field():
    result = load_passages(TEST_FIXTURES / "invalid_passages.jsonl")
    assert not result.ok
    lines = {e.line for e in result.errors}
    assert lines == {1, 2, 3, 4}
    messages = " ".join(e.message for e in result.errors)
    assert "work_id" in messages  # missing required field
    assert "diplomatic_sha256" in messages
    assert "invalid JSON" in messages
    assert "language" in messages


def test_fixtures_are_all_synthetic(fixture_passages):
    assert fixture_passages and all(p.passage_id.startswith("SYN-") for p in fixture_passages)
    for p in fixture_passages:
        assert sha256_text(p.diplomatic_transcription) == p.diplomatic_sha256
        assert {str(r.target_language) for r in p.reference_translations} == {"fr", "en"}
