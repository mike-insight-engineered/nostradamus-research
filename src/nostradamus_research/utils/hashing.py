"""Stable hashing used for transcription integrity and dataset versioning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_text(text: str) -> str:
    """SHA-256 of the exact UTF-8 bytes of ``text`` (no normalisation of any kind)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(obj: Any) -> str:
    """Deterministic JSON serialisation (sorted keys, no insignificant whitespace)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def stable_hash(obj: Any) -> str:
    return sha256_text(canonical_json(obj))
