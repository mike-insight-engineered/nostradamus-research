"""Shared report helpers: templates, tables, evidence banners."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from string import Template
from typing import Any

from ..models.enums import EvidenceLevel

BANNERS: dict[EvidenceLevel, str] = {
    EvidenceLevel.SYNTHETIC_FIXTURE: (
        "> **WARNING — SYNTHETIC FIXTURE DATA. NOT RESEARCH EVIDENCE.**\n"
        "> Some or all inputs are synthetic test fixtures and/or mock-provider outputs and/or "
        "synthetic reviews. Nothing in this report says anything about historical translation quality."
    ),
    EvidenceLevel.AUTOMATED_ONLY: (
        "> **AUTOMATED METRICS ONLY — NOT EXPERT VALIDATED.**\n"
        "> Reference-based metrics (e.g. chrF) measure surface similarity to references; they do not "
        "establish translation correctness."
    ),
    EvidenceLevel.HUMAN_NON_EXPERT: (
        "> **NON-EXPERT HUMAN REVIEW.** At least some judgements come from reviewers not recorded as "
        "domain experts. Treat results as preliminary."
    ),
    EvidenceLevel.EXPERT_REVIEWED: (
        "> **Expert-reviewed historical passages.** Sample-size and uncertainty caveats below still apply."
    ),
}


def weakest(levels: Iterable[EvidenceLevel | str]) -> EvidenceLevel | None:
    order = list(EvidenceLevel)
    present = [EvidenceLevel(level) for level in levels]
    return min(present, key=order.index) if present else None


def evidence_banner(levels: Iterable[EvidenceLevel | str]) -> str:
    level = weakest(levels)
    if level is None:
        return "> **NO RESULTS.** No evaluated outputs were available for this report."
    return BANNERS[level]


def md_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    def cell(v: Any) -> str:
        if v is None:
            return "—"
        if isinstance(v, float):
            return f"{v:.3f}"
        return str(v).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def bullet(items: Iterable[str], empty: str = "None.") -> str:
    lst = [f"- {i}" for i in items]
    return "\n".join(lst) if lst else empty


def render_template(path: Path, **values: Any) -> str:
    """Render a ``string.Template`` file; every ``${placeholder}`` must be supplied."""
    if not path.is_file():
        raise FileNotFoundError(f"report template not found: {path}")
    return Template(path.read_text(encoding="utf-8")).substitute(
        **{k: str(v) for k, v in values.items()}
    )


def fmt_est(d: dict[str, Any] | None, digits: int = 1) -> str:
    if not d or d.get("value") is None:
        return "n/a"
    v = d["value"]
    if d.get("low") is None:
        return f"{v:.{digits}f} (n={d.get('n')}, no CI)"
    return f"{v:.{digits}f} [{d['low']:.{digits}f}, {d['high']:.{digits}f}] (n={d.get('n')})"
