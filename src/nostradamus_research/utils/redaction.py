"""Protection of secrets in logs and persisted artifacts."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable

_SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)(api[_-]?key|authorization|x-api-key)(\"?\s*[:=]\s*\"?)([^\s\",]+)"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{12,}"),
]

REDACTED = "[REDACTED]"


def redact(text: str, extra_secrets: Iterable[str] = ()) -> str:
    """Remove API-key-like strings and any explicitly supplied secret values."""
    for secret in extra_secrets:
        if secret and len(secret) >= 6:
            text = text.replace(secret, REDACTED)
    for pattern in _SECRET_PATTERNS:
        if pattern.groups >= 3:
            text = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}{REDACTED}", text)
        else:
            text = pattern.sub(REDACTED, text)
    return text


def secret_env_values(names: Iterable[str]) -> list[str]:
    """Values of the named environment variables (for redaction), skipping unset ones."""
    return [v for n in names if (v := os.environ.get(n))]


def contains_secret(text: str) -> bool:
    return any(p.search(text) for p in _SECRET_PATTERNS[:2])
