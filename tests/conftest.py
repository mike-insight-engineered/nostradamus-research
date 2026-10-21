"""Shared test fixtures. Every test runs offline and without API keys."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from nostradamus_research.config import AppConfig, load_config
from nostradamus_research.corpus.io import load_lexical_evidence, load_passages
from nostradamus_research.models.evidence import LexicalEvidence
from nostradamus_research.models.passage import Passage
from nostradamus_research.provenance.registry import SourceRegistry
from nostradamus_research.utils.hashing import sha256_text

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "data" / "fixtures"
TEST_FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def _offline_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the repo root and guarantee no real credentials are visible to tests."""
    monkeypatch.setenv("NR_REPO_ROOT", str(REPO_ROOT))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def cfg() -> AppConfig:
    return load_config(REPO_ROOT)


@pytest.fixture(scope="session")
def fixture_passages() -> list[Passage]:
    result = load_passages(FIXTURES / "synthetic_passages.jsonl")
    assert result.ok, result.errors
    return result.records


@pytest.fixture(scope="session")
def fixture_registry() -> SourceRegistry:
    reg, errors = SourceRegistry.load(FIXTURES / "synthetic_sources.jsonl")
    assert not errors
    return reg


@pytest.fixture(scope="session")
def fixture_evidence() -> list[LexicalEvidence]:
    result = load_lexical_evidence(FIXTURES / "synthetic_lexical_evidence.jsonl")
    assert result.ok
    return result.records


@pytest.fixture
def oracle(fixture_passages: list[Passage]) -> dict[str, dict[str, str]]:
    return {
        p.diplomatic_sha256: {str(r.target_language): r.text for r in p.reference_translations}
        for p in fixture_passages
    }


def historical_passage_dict(**overrides: Any) -> dict[str, Any]:
    """A minimal *valid* historical-origin passage dict (content is a test placeholder)."""
    text = overrides.pop("diplomatic_transcription", "Texte d'essai ſans valeur hiſtorique.")
    base: dict[str, Any] = {
        "passage_id": "PSG-TEST-001",
        "source_id": "SRC-TEST-WITNESS",
        "work_id": "WORK-TEST",
        "language": "frm",
        "genre": "prose",
        "category": "french_prose",
        "diplomatic_transcription": text,
        "diplomatic_sha256": sha256_text(text),
    }
    base.update(overrides)
    return base


def synthetic_passage(i: int, work: str, category: str = "french_prose", **kw: Any) -> Passage:
    lang, genre = {
        "french_prose": ("frm", "prose"), "french_poetry": ("frm", "verse"),
        "latin_prose": ("lat", "prose"), "latin_verse": ("lat", "verse"), "mixed": ("mixed", "prose"),
    }[category]  # fmt: skip
    text = kw.pop(
        "text", f"Synthetic test sentence number {i} for work {work} with filler words {i * 7}."
    )
    data = {
        "passage_id": f"SYN-PSG-T{i:03d}", "source_id": f"SYN-WIT-{work}", "data_origin": "synthetic_fixture",
        "work_id": f"SYN-WORK-{work}", "author_id": kw.pop("author", f"A-{work}"), "language": lang,
        "genre": genre, "category": category, "diplomatic_transcription": text,
        "diplomatic_sha256": sha256_text(text),
    }  # fmt: skip
    data.update(kw)
    return Passage.model_validate(data)


@pytest.fixture
def passage_dict() -> dict[str, Any]:
    return copy.deepcopy(historical_passage_dict())
