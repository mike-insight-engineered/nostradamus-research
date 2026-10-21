"""Automated reference-based metrics.

chrF / chrF++ (sacrebleu) are reported per output against *all* available
references for that language. They measure surface similarity to the
references only: a faithful translation worded differently can score low, and
a fluent mistranslation can score high. They are never treated as proof of
correctness; human MQM review is the primary evidence.

COMET is optional (``uv sync --extra comet``) and isolated here.
"""

from __future__ import annotations

from typing import Any

from sacrebleu.metrics import BLEU, CHRF

from ..config import MetricsConfig


class OptionalDependencyError(RuntimeError):
    pass


def chrf(hypothesis: str, references: list[str], *, char_order: int = 6, word_order: int = 0,
         beta: int = 2) -> float:  # fmt: skip
    if not references:
        raise ValueError("chrF requires at least one reference")
    metric = CHRF(char_order=char_order, word_order=word_order, beta=beta)
    return float(metric.sentence_score(hypothesis, references).score)


def sentence_bleu(hypothesis: str, references: list[str]) -> float:
    if not references:
        raise ValueError("BLEU requires at least one reference")
    return float(BLEU(effective_order=True).sentence_score(hypothesis, references).score)


def compute_metrics(
    hypothesis: str | None, references: list[str], cfg: MetricsConfig
) -> dict[str, float | None]:
    """All enabled sentence-level metrics; ``None`` when no hypothesis or no reference."""
    names = (
        ["chrf"]
        + (["chrf_pp"] if cfg.chrf_plus_plus else [])
        + (["bleu"] if cfg.sentence_bleu else [])
    )
    if not hypothesis or not references:
        return dict.fromkeys(names)
    c = cfg.chrf
    out: dict[str, float | None] = {"chrf": chrf(hypothesis, references, char_order=c.char_order,
                                                 word_order=c.word_order, beta=c.beta)}  # fmt: skip
    if cfg.chrf_plus_plus:
        out["chrf_pp"] = chrf(
            hypothesis, references, char_order=c.char_order, word_order=2, beta=c.beta
        )
    if cfg.sentence_bleu:
        out["bleu"] = sentence_bleu(hypothesis, references)
    return out


def comet_scores(
    sources: list[str], hypotheses: list[str], references: list[str], model_name: str
) -> list[float]:  # pragma: no cover - requires optional heavy dependency
    """Segment-level COMET scores. Requires the optional ``comet`` extra."""
    try:
        from comet import download_model, load_from_checkpoint
    except ImportError as exc:
        raise OptionalDependencyError(
            "COMET is not installed; run `uv sync --extra comet` (downloads PyTorch and a model)"
        ) from exc
    model: Any = load_from_checkpoint(download_model(model_name))
    data = [
        {"src": s, "mt": h, "ref": r}
        for s, h, r in zip(sources, hypotheses, references, strict=True)
    ]
    output = model.predict(data, batch_size=8, gpus=0)
    return [float(x) for x in output.scores]
