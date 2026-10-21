"""Runtime metadata for experiment manifests: time, git state, environment."""

from __future__ import annotations

import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def utc_timestamp_slug() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=10, check=True
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip()


def git_commit(root: Path) -> str | None:
    return _git(root, "rev-parse", "HEAD")


def git_dirty(root: Path) -> bool | None:
    status = _git(root, "status", "--porcelain")
    return None if status is None else bool(status)


def python_version() -> str:
    return platform.python_version()
