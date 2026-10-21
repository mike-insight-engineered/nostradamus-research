from dataclasses import replace

import pytest

from nostradamus_research.linguistics.retrieval import LexicalEvidenceStore
from nostradamus_research.models.enums import ConfidenceSource, PipelineId, VerificationStatus
from nostradamus_research.translation.guardrails import speculative_flags
from nostradamus_research.translation.parsing import ResponseParseError, as_confidence, extract_json
from nostradamus_research.translation.pipelines import (
    PIPELINES,
    PipelineSettings,
    TranslationPipeline,
    parse_pipeline_id,
)
from nostradamus_research.translation.prompts import PromptError, PromptLibrary, parse_template
from nostradamus_research.translation.providers import MockProvider

VERSIONS = {
    "direct": "1.0.0",
    "two_stage_to_french": "1.0.0",
    "two_stage_french_to_english": "1.0.0",
    "retrieval_augmented": "1.0.0",
    "structured_analysis": "1.0.0",
}
SETTINGS = PipelineSettings(prompt_versions=VERSIONS)


def _pipeline(pid, provider=None, settings=SETTINGS, store=None):
    return PIPELINES[pid](provider or MockProvider(), PromptLibrary.load(), settings, store)


@pytest.mark.parametrize("pid", list(PipelineId))
def test_every_pipeline_produces_a_typed_result(pid, fixture_passages, oracle, fixture_evidence):
    store = LexicalEvidenceStore(fixture_evidence)
    settings = replace(SETTINGS, allow_synthetic_evidence=True)
    p = fixture_passages[0]
    r = _pipeline(pid, MockProvider(oracle=oracle), settings, store).translate(p, "run-x")
    assert r.succeeded and r.error is None
    assert r.translation_fr and r.translation_en
    assert r.pipeline is pid and r.is_mock and r.provider == "mock"
    assert r.confidence_source is ConfidenceSource.MOCK_DETERMINISTIC
    assert r.source_text_sha256 == p.diplomatic_sha256
    assert len(r.calls) == PIPELINES[pid].calls_per_passage
    assert all(c.prompt_version == "1.0.0" and len(c.prompt_sha256) == 64 for c in r.calls)
    assert r.prompt_versions


def test_two_stage_records_intermediate_and_withholds_original(fixture_passages):
    prov = MockProvider()
    r = _pipeline(PipelineId.B_TWO_STAGE, prov).translate(fixture_passages[0], "r")
    assert r.intermediate_fr == r.translation_fr
    stage2 = prov.calls[1]
    assert stage2.task == "translate_french_to_english"
    assert fixture_passages[0].diplomatic_transcription not in stage2.user  # original withheld
    assert set(r.analysis["stage_confidences"]) == {"stage1", "stage2"}


def test_retrieval_without_verified_evidence_abstains(fixture_passages, fixture_evidence):
    prov = MockProvider()
    store = LexicalEvidenceStore(fixture_evidence)  # synthetic only; not allowed by default
    r = _pipeline(PipelineId.C_RETRIEVAL, prov, store=store).translate(fixture_passages[0], "r")
    assert r.retrieval_status == "no_evidence" and r.retrieved_evidence_ids == []
    assert any("not permitted" in lim for lim in r.limitations)
    assert "NO VERIFIED EVIDENCE AVAILABLE" in prov.calls[0].user


def test_synthetic_evidence_is_labelled_in_prompt(fixture_passages, fixture_evidence):
    prov = MockProvider()
    settings = replace(
        SETTINGS,
        allow_synthetic_evidence=True,
        minimum_evidence_status=VerificationStatus.EXPERT_REVIEWED,
    )
    r = _pipeline(
        PipelineId.C_RETRIEVAL, prov, settings, LexicalEvidenceStore(fixture_evidence)
    ).translate(fixture_passages[0], "r")
    assert r.retrieval_status == "unverified_or_synthetic_evidence"
    assert "SYNTHETIC FIXTURE" in prov.calls[0].user


def test_structured_analysis_contains_all_steps(fixture_passages):
    p = next(x for x in fixture_passages if x.category.value == "mixed")
    prov = MockProvider()
    r = _pipeline(PipelineId.D_STRUCTURED, prov).translate(p, "r")
    for key in (
        "language_identification",
        "segmentation",
        "morphology",
        "syntax_notes",
        "polysemous_terms",
        "evidence_used",
        "software_preanalysis",
    ):
        assert key in r.analysis
    assert "Heuristic pre-analysis" in prov.calls[0].user


def test_unparseable_response_becomes_error_result(fixture_passages):
    prov = MockProvider(malformed_tasks=frozenset({"translate_direct"}))
    r = _pipeline(PipelineId.A_DIRECT, prov).translate(fixture_passages[0], "r")
    assert not r.succeeded and "unparseable" in r.error and r.parse_errors
    assert r.stated_confidence is None and r.confidence_source is ConfidenceSource.NONE


def test_provider_failure_becomes_error_result(fixture_passages):
    prov = MockProvider(fail_tasks=frozenset({"translate_to_modern_french"}))
    r = _pipeline(PipelineId.B_TWO_STAGE, prov).translate(fixture_passages[0], "r")
    assert not r.succeeded and "provider error" in r.error
    assert r.calls[0].error


def test_no_confidence_is_never_imputed(fixture_passages):
    r = _pipeline(PipelineId.A_DIRECT, MockProvider(confidence_mode="none")).translate(
        fixture_passages[0], "r"
    )
    assert r.stated_confidence is None and r.confidence_source is ConfidenceSource.NONE


def test_guardrails_flag_interpretation_not_in_source():
    assert speculative_flags("This quatrain predicts the French Revolution.", "Le roy viendra")
    assert speculative_flags("The king will come.", "Le roy viendra") == []
    # Terms already in the source are not flagged.
    assert speculative_flags("a prophecy", "une prophecy ancienne") == []


def test_guardrail_flags_attached_to_result(fixture_passages):
    class Speculative(MockProvider):
        def _payload(self, request):
            out = super()._payload(request)
            out["translation_en"] = "This foretells the coming of Napoleon."
            return out

    r = _pipeline(PipelineId.A_DIRECT, Speculative()).translate(fixture_passages[0], "r")
    assert any("prophecy_language" in f for f in r.guardrail_flags)
    assert any("later_historical_figure" in f for f in r.guardrail_flags)
    assert (
        r.translation_en == "This foretells the coming of Napoleon."
    )  # flagged, not silently altered


def test_prompt_version_pinning():
    with pytest.raises(PromptError, match="pins"):
        _pipeline(
            PipelineId.A_DIRECT,
            settings=replace(SETTINGS, prompt_versions={**VERSIONS, "direct": "9.9.9"}),
        )


def test_prompt_templates_parse_and_render():
    lib = PromptLibrary.load()
    assert set(lib.templates) == set(VERSIONS)
    t = lib.get("direct")
    with pytest.raises(PromptError, match="missing values"):
        t.render(source_text="x")
    system, user = t.render(
        language="frm", genre="prose", date_text="1550", source_text="TEXT", normalised_block=""
    )
    assert "TEXT" in user and "{{" not in user and "prophec" in system.lower()
    with pytest.raises(PromptError, match="front matter"):
        parse_template("[system]\nx\n[user]\ny")


def test_extract_json_variants():
    assert extract_json('Sure! ```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('prefix {"a": "x}y", "b": {"c": 2}} suffix') == {"a": "x}y", "b": {"c": 2}}
    assert extract_json('{"a": "esc \\" quote"}') == {"a": 'esc " quote'}
    with pytest.raises(ResponseParseError):
        extract_json("no json here")
    assert as_confidence(0.7) == 0.7 and as_confidence(1.5) is None and as_confidence("0.5") is None
    assert as_confidence(True) is None


def test_parse_pipeline_id():
    assert parse_pipeline_id("a") is PipelineId.A_DIRECT
    assert parse_pipeline_id("D_structured") is PipelineId.D_STRUCTURED
    with pytest.raises(ValueError):
        parse_pipeline_id("Z")


def test_pipeline_base_is_abstract():
    with pytest.raises(TypeError):
        TranslationPipeline(MockProvider(), PromptLibrary.load(), SETTINGS)  # type: ignore[abstract]
