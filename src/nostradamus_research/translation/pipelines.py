"""The four translation strategies (A–D) sharing one provider interface.

* **A — Direct**: historical text → modern French + English in one call.
* **B — Two-stage**: historical text → modern French; then French → English
  *without* the original, so staging error can be measured. The intermediate
  French is recorded.
* **C — Retrieval-augmented**: local, provenance-tracked lexical evidence is
  retrieved and supplied; with no verified evidence the model is told to
  abstain from evidence-dependent claims and the limitation is recorded.
* **D — Structured analysis**: software heuristics (language ID, clauses,
  morphology hints) plus retrieval feed an explicit nine-step analysis that
  ends in literal translations and recorded ambiguity.

Every pipeline translates the *diplomatic* transcription. None may introduce
interpretation; outputs are scanned by :mod:`.guardrails` and flagged.
"""

from __future__ import annotations

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

from ..linguistics.language_id import identify
from ..linguistics.morphology import hints
from ..linguistics.retrieval import LexicalEvidenceStore, RetrievalOutcome
from ..linguistics.segmentation import clauses
from ..models.enums import ConfidenceSource, DataOrigin, PipelineId, VerificationStatus
from ..models.evidence import LexicalEvidence
from ..models.passage import Passage
from ..models.translation import AlternativeReading, ProviderCallRecord, TranslationResult
from ..utils.hashing import sha256_text
from ..utils.runtime import utc_now
from .guardrails import speculative_flags
from .parsing import (
    ResponseParseError,
    as_alternatives,
    as_confidence,
    as_str,
    as_str_list,
    extract_json,
)
from .prompts import PromptLibrary, PromptTemplate
from .providers.base import ProviderError, ProviderRequest, TranslationProvider


@dataclass(frozen=True)
class PipelineSettings:
    prompt_versions: dict[str, str]
    temperature: float | None = 0.0
    max_tokens: int = 2048
    include_normalised_reading: bool = False
    top_k: int = 5
    minimum_evidence_status: VerificationStatus = VerificationStatus.TRANSCRIPTION_VERIFIED
    allow_synthetic_evidence: bool = False
    flag_speculative: bool = True


@dataclass
class _Context:
    passage: Passage
    run_id: str
    calls: list[ProviderCallRecord] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


class TranslationPipeline(ABC):
    pipeline_id: ClassVar[PipelineId]
    template_ids: ClassVar[tuple[str, ...]]
    calls_per_passage: ClassVar[int] = 1
    uses_retrieval: ClassVar[bool] = False

    def __init__(
        self,
        provider: TranslationProvider,
        prompts: PromptLibrary,
        settings: PipelineSettings,
        retriever: LexicalEvidenceStore | None = None,
    ):
        self.provider = provider
        self.prompts = prompts
        self.settings = settings
        self.retriever = retriever
        # Fail fast if a pinned template version is missing.
        self._templates = {tid: self._template(tid) for tid in self.template_ids}

    def _template(self, template_id: str) -> PromptTemplate:
        return self.prompts.get(template_id, self.settings.prompt_versions.get(template_id))

    @property
    def templates(self) -> list[PromptTemplate]:
        return list(self._templates.values())

    # -- shared plumbing ------------------------------------------------------------
    def _base_values(self, p: Passage) -> dict[str, str]:
        block = ""
        if self.settings.include_normalised_reading and p.normalised_reading:
            block = (
                "\nEditorial normalised reading (rules: "
                f"{', '.join(p.normalisation_rules)}; for orientation only — translate the "
                f"diplomatic text):\n<<<\n{p.normalised_reading}\n>>>\n"
            )
        return {
            "language": str(p.language),
            "genre": str(p.genre),
            "date_text": p.date_text or "unknown",
            "source_text": p.diplomatic_transcription,
            "normalised_block": block,
        }

    def _base_metadata(self, p: Passage) -> dict[str, Any]:
        return {
            "passage_id": p.passage_id,
            "pipeline": str(self.pipeline_id),
            "source_text": p.diplomatic_transcription,
            "source_sha256": p.diplomatic_sha256,
        }

    def _call(
        self,
        ctx: _Context,
        stage: str,
        template_id: str,
        values: dict[str, str],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        tmpl = self._templates[template_id]
        system, user = tmpl.render(**values)
        request = ProviderRequest(
            task=tmpl.task,
            system=system,
            user=user,
            template_id=tmpl.template_id,
            template_version=tmpl.version,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
            metadata=metadata,
        )
        started = utc_now()
        t0 = time.perf_counter()
        record = ProviderCallRecord(
            call_id=uuid.uuid4().hex[:12], stage=stage, provider=self.provider.name,
            model=self.provider.model, task=tmpl.task, prompt_template_id=tmpl.template_id,
            prompt_version=tmpl.version, prompt_sha256=request.prompt_sha256,
            temperature=request.temperature, max_tokens=request.max_tokens,
            started_at=started, duration_seconds=0.0,
        )  # fmt: skip
        try:
            response = self.provider.complete(request)
        except ProviderError as exc:
            record.duration_seconds = round(time.perf_counter() - t0, 4)
            record.error = str(exc)
            ctx.calls.append(record)
            raise
        record.duration_seconds = round(time.perf_counter() - t0, 4)
        record.model = response.model
        record.attempts = response.attempts
        record.usage = response.usage
        record.response_id = response.response_id
        record.stop_reason = response.stop_reason
        record.cost_usd, record.cost_note = self.provider.cost(response.usage)
        ctx.calls.append(record)
        try:
            return extract_json(response.text)
        except ResponseParseError as exc:
            ctx.parse_errors.append(f"{stage}: {exc}")
            raise

    def _confidence_source(self, value: float | None) -> ConfidenceSource:
        if value is None:
            return ConfidenceSource.NONE
        return (
            ConfidenceSource.MOCK_DETERMINISTIC
            if self.provider.name == "mock"
            else ConfidenceSource.MODEL_STATED
        )

    def _retrieve(self, text: str, ctx: _Context) -> RetrievalOutcome:
        if self.retriever is None:
            outcome = RetrievalOutcome(status="no_evidence")
            outcome.limitations.append(
                "No lexical evidence store configured; evidence-dependent claims were not permitted."
            )
        else:
            outcome = self.retriever.retrieve(
                text,
                top_k=self.settings.top_k,
                minimum_status=self.settings.minimum_evidence_status,
                allow_synthetic=self.settings.allow_synthetic_evidence,
            )
        ctx.limitations.extend(outcome.limitations)
        return outcome

    @staticmethod
    def evidence_block(entries: list[LexicalEvidence]) -> str:
        if not entries:
            return (
                "NO VERIFIED EVIDENCE AVAILABLE. Do not make claims that depend on historical "
                "lexical evidence; translate conservatively and record the limitation."
            )
        lines = []
        for e in entries:
            tag = (
                " [SYNTHETIC FIXTURE — not historical evidence]"
                if e.data_origin is DataOrigin.SYNTHETIC_FIXTURE
                else ""
            )
            loc = f", {e.locator}" if e.locator else ""
            quote = f' Quotation: "{e.quotation}"' if e.quotation else ""
            lines.append(
                f"- [{e.evidence_id}] {e.headword} ({e.kind}; status {e.verification_status}){tag}: "
                f"{e.sense}. Source: {e.citation}{loc}.{quote}"
            )
        return "\n".join(lines)

    # -- public API -------------------------------------------------------------------
    def translate(self, passage: Passage, run_id: str) -> TranslationResult:
        ctx = _Context(passage, run_id)
        fields: dict[str, Any] = {}
        error: str | None = None
        try:
            fields = self._run(passage, ctx)
        except ProviderError as exc:
            error = f"provider error: {exc}"
        except ResponseParseError as exc:
            error = f"unparseable response: {exc}"

        confidence = fields.pop("stated_confidence", None)
        result = TranslationResult(
            result_id=f"{run_id}:{passage.passage_id}",
            run_id=run_id,
            passage_id=passage.passage_id,
            pipeline=self.pipeline_id,
            provider=self.provider.name,
            model=ctx.calls[-1].model if ctx.calls else self.provider.model,
            is_mock=self.provider.name == "mock",
            data_origin=passage.data_origin,
            source_text_sha256=sha256_text(passage.diplomatic_transcription),
            stated_confidence=confidence,
            confidence_source=self._confidence_source(confidence),
            limitations=ctx.limitations,
            parse_errors=ctx.parse_errors,
            error=error,
            prompt_versions={t.template_id: t.version for t in self.templates},
            calls=ctx.calls,
            created_at=utc_now(),
            **fields,
        )
        if self.settings.flag_speculative:
            flags = []
            for out in (result.translation_fr, result.translation_en, result.intermediate_fr):
                flags += speculative_flags(out, passage.diplomatic_transcription)
            result.guardrail_flags = sorted(set(result.guardrail_flags) | set(flags))
        return result

    @abstractmethod
    def _run(self, p: Passage, ctx: _Context) -> dict[str, Any]:
        """Return TranslationResult field values (plus ``stated_confidence``)."""


class DirectPipeline(TranslationPipeline):
    pipeline_id = PipelineId.A_DIRECT
    template_ids = ("direct",)

    def _run(self, p: Passage, ctx: _Context) -> dict[str, Any]:
        out = self._call(ctx, "direct", "direct", self._base_values(p), self._base_metadata(p))
        return {
            "translation_fr": as_str(out.get("translation_fr")),
            "translation_en": as_str(out.get("translation_en")),
            "alternatives": as_alternatives(out.get("alternatives")),
            "unresolved_ambiguities": as_str_list(out.get("unresolved_ambiguities")),
            "stated_confidence": as_confidence(out.get("self_reported_confidence")),
        }


class TwoStagePipeline(TranslationPipeline):
    pipeline_id = PipelineId.B_TWO_STAGE
    template_ids = ("two_stage_to_french", "two_stage_french_to_english")
    calls_per_passage = 2

    def _run(self, p: Passage, ctx: _Context) -> dict[str, Any]:
        s1 = self._call(ctx, "stage1_to_french", "two_stage_to_french", self._base_values(p),
                        self._base_metadata(p))  # fmt: skip
        fr = as_str(s1.get("translation_fr"))
        if fr is None:
            raise ResponseParseError("stage 1 returned no translation_fr")
        s2 = self._call(ctx, "stage2_french_to_english", "two_stage_french_to_english",
                        {"french_text": fr}, {**self._base_metadata(p), "french_text": fr})  # fmt: skip
        c1 = as_confidence(s1.get("self_reported_confidence"))
        c2 = as_confidence(s2.get("self_reported_confidence"))
        analysis = {"stage_confidences": {"stage1": c1, "stage2": c2},
                    "confidence_rule": "min(stage1, stage2); null if either is null"}  # fmt: skip
        return {
            "translation_fr": fr,
            "intermediate_fr": fr,
            "translation_en": as_str(s2.get("translation_en")),
            "analysis": analysis,
            "stated_confidence": min(c1, c2) if c1 is not None and c2 is not None else None,
        }


class RetrievalAugmentedPipeline(TranslationPipeline):
    pipeline_id = PipelineId.C_RETRIEVAL
    template_ids = ("retrieval_augmented",)
    uses_retrieval = True

    def _run(self, p: Passage, ctx: _Context) -> dict[str, Any]:
        outcome = self._retrieve(p.diplomatic_transcription, ctx)
        ids = [e.evidence_id for e in outcome.entries]
        values = {**self._base_values(p), "evidence_block": self.evidence_block(outcome.entries)}
        out = self._call(ctx, "retrieval_translate", "retrieval_augmented", values,
                         {**self._base_metadata(p), "evidence_ids": ids})  # fmt: skip
        cited = as_str_list(out.get("evidence_used"))
        flags = [f"cited_unsupplied_evidence: {c!r}" for c in cited if c not in ids]
        return {
            "translation_fr": as_str(out.get("translation_fr")),
            "translation_en": as_str(out.get("translation_en")),
            "alternatives": as_alternatives(out.get("alternatives")),
            "unresolved_ambiguities": as_str_list(out.get("unresolved_ambiguities")),
            "retrieved_evidence_ids": ids,
            "retrieval_status": outcome.status,
            "analysis": {"evidence_cited": cited},
            "guardrail_flags": flags,
            "stated_confidence": as_confidence(out.get("self_reported_confidence")),
        }


class StructuredAnalysisPipeline(TranslationPipeline):
    pipeline_id = PipelineId.D_STRUCTURED
    template_ids = ("structured_analysis",)
    uses_retrieval = True

    def _run(self, p: Passage, ctx: _Context) -> dict[str, Any]:
        text = p.diplomatic_transcription
        lang = identify(text)
        segs = clauses(text)
        morph = [{"form": h.form, "hint": h.hint} for h in hints(text, p.language)]
        pre = {"language": lang.as_dict(), "clauses": segs, "morphology_hints": morph}
        outcome = self._retrieve(text, ctx)
        ids = [e.evidence_id for e in outcome.entries]
        values = {
            **self._base_values(p),
            "linguistic_hints": json.dumps(pre, ensure_ascii=False, indent=2),
            "evidence_block": self.evidence_block(outcome.entries),
        }
        md = {**self._base_metadata(p), "evidence_ids": ids, "heuristic_language": lang.as_dict(),
              "clauses": segs, "morph_hints": morph}  # fmt: skip
        out = self._call(ctx, "structured_analysis", "structured_analysis", values, md)
        cited = as_str_list(out.get("evidence_used"))
        flags = [f"cited_unsupplied_evidence: {c!r}" for c in cited if c not in ids]
        analysis = {k: v for k, v in out.items()
                    if k not in ("literal_translation_fr", "literal_translation_en",
                                 "self_reported_confidence")}  # fmt: skip
        analysis["software_preanalysis"] = pre
        alternatives: list[AlternativeReading] = as_alternatives(out.get("alternatives"))
        for term in out.get("polysemous_terms") or []:
            if isinstance(term, dict) and isinstance(term.get("term"), str):
                senses = as_str_list(term.get("period_senses"))
                if len(senses) > 1:
                    alternatives.append(AlternativeReading(span=term["term"], readings=senses,
                                                           note="polysemous term (pipeline D)"))  # fmt: skip
        return {
            "translation_fr": as_str(out.get("literal_translation_fr")),
            "translation_en": as_str(out.get("literal_translation_en")),
            "alternatives": alternatives,
            "unresolved_ambiguities": as_str_list(out.get("unresolved_ambiguities")),
            "retrieved_evidence_ids": ids,
            "retrieval_status": outcome.status,
            "analysis": analysis,
            "guardrail_flags": flags,
            "stated_confidence": as_confidence(out.get("self_reported_confidence")),
        }


PIPELINES: dict[PipelineId, type[TranslationPipeline]] = {
    PipelineId.A_DIRECT: DirectPipeline,
    PipelineId.B_TWO_STAGE: TwoStagePipeline,
    PipelineId.C_RETRIEVAL: RetrievalAugmentedPipeline,
    PipelineId.D_STRUCTURED: StructuredAnalysisPipeline,
}


def parse_pipeline_id(value: str) -> PipelineId:
    """Accept 'A', 'a', 'A_direct' etc."""
    v = value.strip()
    for pid in PipelineId:
        if v == pid.value or v.upper() == pid.value[0]:
            return pid
    raise ValueError(
        f"unknown pipeline {value!r}; choose from {[p.value for p in PipelineId]} or A-D"
    )
