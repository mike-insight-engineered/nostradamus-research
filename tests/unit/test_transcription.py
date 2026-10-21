import pytest

from nostradamus_research.models.passage import Passage
from nostradamus_research.transcription.integrity import compare_corpora
from nostradamus_research.transcription.normalisation import (
    DEFAULT_SAFE_RULES,
    RULES,
    NormalisationError,
    check_safeguards,
    normalise,
)
from nostradamus_research.transcription.tei import diplomatic_text_from_tei, passage_to_tei
from nostradamus_research.utils.hashing import sha256_text
from tests.conftest import historical_passage_dict


def test_long_s_normalisation_records_every_change():
    src = "Ceſte maiſon eſt ſienne."
    res = normalise(src, ["long_s"])
    assert res.normalised == "Ceste maison est sienne."
    assert res.original == src  # input untouched
    assert len(res.changes) == src.count("ſ")
    assert all(c.rule == "long_s" and c.original == "ſ" for c in res.changes)


def test_editorial_rules_are_never_default():
    assert set(DEFAULT_SAFE_RULES) == {n for n, r in RULES.items() if not r.editorial}
    for name in ("u_v_consonantal", "i_j_initial", "nasal_tilde", "ampersand", "v_u_initial_vowel"):
        assert name not in DEFAULT_SAFE_RULES


def test_no_lexical_modernisation_rule_exists():
    assert not any("modern" in name for name in RULES)
    # Spelling such as 'faict', 'estoit' is untouched by every safe rule.
    assert normalise("il faict & estoit", DEFAULT_SAFE_RULES).normalised == "il faict & estoit"


@pytest.mark.parametrize(
    ("rule", "src", "expected"),
    [
        ("u_v_consonantal", "auoir", "avoir"),
        ("v_u_initial_vowel", "vn homme", "un homme"),
        ("i_j_initial", "iamais", "jamais"),
        ("nasal_tilde", "cõme", "comme"),
        ("nasal_tilde", "mõde", "monde"),
        ("ampersand", "pain & vin", "pain et vin"),
        ("ligatures_ae_oe", "Cæsar", "Caesar"),
    ],
)
def test_individual_rules(rule, src, expected):
    assert normalise(src, [rule]).normalised == expected


def test_unknown_rule_rejected():
    with pytest.raises(NormalisationError, match="unknown"):
        normalise("x", ["modernise_everything"])


def test_safeguards_block_punctuation_or_word_changes():
    with pytest.raises(NormalisationError, match="punctuation"):
        check_safeguards("a, b.", "a b.")
    with pytest.raises(NormalisationError, match="number of words"):
        check_safeguards("a b c", "a bc")


def test_tei_roundtrip_preserves_diplomatic_text():
    text = "Ceſte annee,\nles bledz & vins."
    p = Passage.model_validate(
        historical_passage_dict(
            diplomatic_transcription=text, normalised_reading="x", normalisation_rules=["long_s"]
        )
    )
    xml = passage_to_tei(p)
    assert 'type="diplomatic"' in xml and 'type="normalised"' in xml
    assert diplomatic_text_from_tei(xml) == text


def test_tei_choice_keeps_abbreviation_not_expansion():
    xml = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><ab type="diplomatic">'
        "<choice><abbr>cõme</abbr><expan>comme</expan></choice> dict<lb/>le <choice><orig>vng</orig>"
        "<reg>un</reg></choice> clerc<note>editorial note</note></ab></body></text></TEI>"
    )
    assert diplomatic_text_from_tei(xml) == "cõme dict\nle vng clerc"


def test_tei_without_diplomatic_layer_rejected():
    with pytest.raises(ValueError, match="diplomatic"):
        diplomatic_text_from_tei('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text/></TEI>')


def test_compare_corpora_flags_undocumented_changes():
    old = Passage.model_validate(historical_passage_dict())
    new_text = "Texte corrigé."
    new = Passage.model_validate(
        historical_passage_dict(
            diplomatic_transcription=new_text, diplomatic_sha256=sha256_text(new_text)
        )
    )
    changes = compare_corpora([old], [new])
    assert len(changes) == 1 and "UNDOCUMENTED" in changes[0].detail
    documented = Passage.model_validate(
        {
            **new.model_dump(),
            "review_history": [
                {
                    "on": "2026-01-01",
                    "by": "Checker",
                    "action": "transcription_checked",
                    "notes": "corrected misreading",
                }
            ],
        }
    )
    assert compare_corpora([old], [documented])[0].detail == "documented correction"
