from nostradamus_research.corpus.leakage import check_leakage, comparison_key, jaccard, shingles
from nostradamus_research.models.evidence import LexicalEvidence
from tests.conftest import synthetic_passage


def _codes(report):
    return {f.code for f in report.findings}


def test_comparison_key_folds_typography_only_for_comparison():
    assert comparison_key("Ceſte  Annee, & c.") == "ceste annee c"
    assert jaccard(shingles("abcdef", 3), shingles("abcdef", 3)) == 1.0


def test_exact_and_near_duplicates():
    a = synthetic_passage(
        1, "A", text="Le clerc eſcript vne lettre a ſon maiſtre et luy dict bonjour."
    )
    b = synthetic_passage(
        2, "B", text="Le clerc escript vne lettre a son maistre et luy dict bonjour."
    )
    c = synthetic_passage(
        3, "C", text="Le clerc eſcript vne lettre a ſon maiſtre et luy dict bonsoir."
    )
    d = synthetic_passage(4, "D", text="Completely different words about the harbour and ships.")
    rep = check_leakage(
        [a, b, c, d],
        assignments={
            a.passage_id: "development",
            b.passage_id: "development",
            c.passage_id: "test",
            d.passage_id: "test",
        },
    )
    assert "exact_duplicate" in _codes(rep)
    near = [f for f in rep.findings if f.code == "near_duplicate"]
    assert near and all(f.severity == "error" for f in near)  # crosses dev/test


def test_shared_work_across_splits_is_an_error():
    a, b = synthetic_passage(1, "A"), synthetic_passage(2, "A")
    rep = check_leakage([a, b], assignments={a.passage_id: "development", b.passage_id: "test"})
    assert "shared_work" in _codes(rep) and not rep.ok


def test_retrieval_material_overlapping_test_text_is_flagged():
    t = synthetic_passage(
        1, "A", text="Hic liber ad probationem programmatis scriptus est neque historiam narrat."
    )
    ev = LexicalEvidence(
        evidence_id="SYN-LEX-X",
        data_origin="synthetic_fixture",
        kind="literary_example",
        headword="liber",
        language="lat",
        sense="book",
        citation="Synthetic test citation",
        quotation="liber ad probationem programmatis scriptus est",
    )
    rep = check_leakage([t], assignments={t.passage_id: "test"}, evidence=[ev])
    assert "retrieval_overlaps_test" in _codes(rep)


def test_test_reference_near_duplicate_of_dev_reference(fixture_passages):
    a, b = fixture_passages[0], fixture_passages[3]
    b2 = b.model_copy(
        update={
            "reference_translations": [
                r.model_copy(update={"text": a.reference_translations[1].text})
                if str(r.target_language) == "en"
                else r
                for r in b.reference_translations
            ]
        }
    )
    rep = check_leakage([a, b2], assignments={a.passage_id: "development", b2.passage_id: "test"})
    assert "test_reference_leak" in _codes(rep)


def test_clean_fixture_corpus_has_no_errors(fixture_passages):
    assert check_leakage(fixture_passages).ok
