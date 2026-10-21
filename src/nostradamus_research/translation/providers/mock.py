"""Deterministic offline mock provider.

The mock is NOT a translation system. It exists so pipelines, persistence,
evaluation and reporting can be exercised offline and in CI at zero cost.

Behaviour:

* Output depends only on the request's structured ``metadata`` and the seed,
  so identical inputs always produce identical outputs.
* For the labelled demonstration, an optional *fixture oracle* (built only from
  ``SYN-`` fixture references, keyed by source-text hash) supplies text that is
  then deterministically perturbed (omissions, word swaps) so the demo exhibits
  a spread of quality. Pipelines never see references; only the mock does.
* Without an oracle, a tiny built-in glossary produces placeholder output.
* ``confidence_mode="deterministic"`` emits a synthetic confidence derived from
  a hash (labelled ``mock_deterministic``); ``"none"`` emits null.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any, Literal

from ...linguistics.segmentation import fold, tokenize
from ...models.translation import TokenUsage
from ...transcription.normalisation import normalise
from .base import ProviderError, ProviderRequest, ProviderResponse, TranslationProvider

_GLOSSARY: dict[str, tuple[str, str]] = {
    "le": ("le", "the"),
    "la": ("la", "the"),
    "les": ("les", "the"),
    "et": ("et", "and"),
    "vne": ("une", "a"),
    "ung": ("un", "a"),
    "de": ("de", "of"),
    "que": ("que", "that"),
    "eſtoit": ("était", "was"),
    "estoit": ("était", "was"),
    "est": ("est", "is"),
    "il": ("il", "he"),
    "ne": ("ne", "not"),
    "rien": ("rien", "nothing"),
    "mais": ("mais", "but"),
    "ſon": ("son", "his"),
    "son": ("son", "his"),
    "in": ("dans", "in"),
    "sed": ("mais", "but"),
    "liber": ("livre", "book"),
}

FixtureOracle = Mapping[str, Mapping[str, str]]  # source_sha256 -> {"fr": ..., "en": ...}


def _h(*parts: object) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def _perturb(text: str, key: int) -> tuple[str, bool]:
    """Deterministically degrade ``text``; returns (text, was_perturbed)."""
    words = text.split(" ")
    mode = key % 5
    if len(words) < 4 or mode in (0, 1):
        return text, False
    if mode == 2:  # omission of a word near the end
        i = len(words) - 1 - (key // 5) % 2
        return " ".join(words[:i] + words[i + 1 :]), True
    if mode == 3:  # swap two adjacent words
        i = (key // 7) % (len(words) - 1)
        words[i], words[i + 1] = words[i + 1], words[i]
        return " ".join(words), True
    # mode 4: truncate the last clause
    cut = max(2, len(words) * 2 // 3)
    return " ".join(words[:cut]), True


def _glossary_render(text: str, lang: Literal["fr", "en"]) -> str:
    safe = normalise(text, ["long_s"]).normalised
    out = []
    for tok in tokenize(text):
        entry = _GLOSSARY.get(tok.text) or _GLOSSARY.get(fold(tok.text))
        if entry:
            out.append(entry[0] if lang == "fr" else entry[1])
        else:
            out.append(
                fold(tok.text) if lang == "en" else normalise(tok.text, ["long_s"]).normalised
            )
    return " ".join(out) if out else safe


class MockProvider(TranslationProvider):
    name = "mock"
    is_paid = False

    def __init__(
        self,
        model: str = "mock-deterministic-v1",
        *,
        seed: int = 0,
        oracle: FixtureOracle | None = None,
        confidence_mode: Literal["deterministic", "none"] = "deterministic",
        fail_tasks: frozenset[str] = frozenset(),
        malformed_tasks: frozenset[str] = frozenset(),
        **kwargs: Any,
    ):
        super().__init__(model, **kwargs)
        self.seed = seed
        self.oracle = oracle or {}
        self.confidence_mode = confidence_mode
        self.fail_tasks = fail_tasks
        self.malformed_tasks = malformed_tasks
        self.calls: list[ProviderRequest] = []

    def describe(self) -> dict[str, Any]:
        return {**super().describe(), "seed": self.seed, "oracle": bool(self.oracle),
                "confidence_mode": self.confidence_mode}  # fmt: skip

    # -- helpers --------------------------------------------------------------------
    def _target(
        self, md: Mapping[str, Any], lang: Literal["fr", "en"], salt: str
    ) -> tuple[str, bool]:
        sha = str(md.get("source_sha256", ""))
        key = _h(self.seed, sha, lang, salt)
        ref = self.oracle.get(sha, {}).get(lang)
        if ref is not None:
            return _perturb(ref, key)
        src = str(
            md.get("french_text")
            if lang == "en" and md.get("french_text")
            else md.get("source_text", "")
        )
        return _glossary_render(src, lang), True

    def _confidence(self, md: Mapping[str, Any], perturbed: bool, salt: str) -> float | None:
        if self.confidence_mode == "none":
            return None
        frac = (_h(self.seed, md.get("source_sha256", ""), "conf", salt) % 1000) / 1000
        # Higher for unperturbed output, with overlap so calibration is non-trivial.
        return round((0.62 + 0.33 * frac) if not perturbed else (0.35 + 0.45 * frac), 3)

    def _payload(self, request: ProviderRequest) -> dict[str, Any]:
        md = request.metadata
        task = request.task
        salt = str(md.get("pipeline", ""))
        if task in ("translate_direct", "translate_with_evidence"):
            fr, p1 = self._target(md, "fr", salt)
            en, p2 = self._target(md, "en", salt)
            payload: dict[str, Any] = {
                "translation_fr": fr,
                "translation_en": en,
                "alternatives": [],
                "unresolved_ambiguities": [],
                "self_reported_confidence": self._confidence(md, p1 or p2, salt),
            }
            if task == "translate_with_evidence":
                payload["evidence_used"] = list(md.get("evidence_ids", []))[:2]
            return payload
        if task == "translate_to_modern_french":
            fr, p = self._target(md, "fr", salt + "B1")
            return {
                "translation_fr": fr,
                "self_reported_confidence": self._confidence(md, p, salt + "B1"),
            }
        if task == "translate_french_to_english":
            en, p = self._target(md, "en", salt + "B2")
            return {
                "translation_en": en,
                "self_reported_confidence": self._confidence(md, p, salt + "B2"),
            }
        if task == "structured_analysis":
            fr, p1 = self._target(md, "fr", salt)
            en, p2 = self._target(md, "en", salt)
            lang = md.get("heuristic_language", {})
            return {
                "language_identification": {
                    "primary": lang.get("language", "unknown"),
                    "code_switching": lang.get("code_switch_spans", []),
                },
                "segmentation": {"clauses": list(md.get("clauses", []))},
                "morphology": [
                    {"form": h["form"], "note": h["hint"]} for h in md.get("morph_hints", [])
                ][:5],
                "syntax_notes": ["mock: no syntactic analysis performed"],
                "polysemous_terms": [],
                "evidence_used": list(md.get("evidence_ids", []))[:2],
                "literal_translation_fr": fr,
                "literal_translation_en": en,
                "alternatives": [],
                "unresolved_ambiguities": [],
                "self_reported_confidence": self._confidence(md, p1 or p2, salt),
            }
        raise ProviderError(f"mock provider does not support task {task!r}")

    def _send(self, request: ProviderRequest) -> ProviderResponse:
        self.calls.append(request)
        if request.task in self.fail_tasks:
            raise ProviderError(f"mock configured to fail task {request.task}")
        if request.task in self.malformed_tasks:
            text = "this is not JSON"
        else:
            text = json.dumps(self._payload(request), ensure_ascii=False)
        usage = TokenUsage(
            input_tokens=len(request.system.split()) + len(request.user.split()),
            output_tokens=len(text.split()),
        )
        return ProviderResponse(
            text=text,
            provider=self.name,
            model=self.model,
            usage=usage,
            response_id=f"mock-{_h(request.prompt_sha256, self.seed):x}",
            stop_reason="end_turn",
        )
