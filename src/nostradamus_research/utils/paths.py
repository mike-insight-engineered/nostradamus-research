"""Repository root discovery.

Research artifacts (configuration, data, schemas, report templates) live in the
repository rather than inside the installed package, so commands must locate
the repository root. ``NR_REPO_ROOT`` overrides discovery (useful in tests).
"""

from __future__ import annotations

import os
from pathlib import Path


class RepositoryNotFoundError(FileNotFoundError):
    """Raised when the research repository root cannot be located."""


def is_repo_root(path: Path) -> bool:
    return (path / "pyproject.toml").is_file() and (path / "config" / "project.yaml").is_file()


def find_repo_root(start: Path | None = None) -> Path:
    """Return the repository root, searching upward from ``start`` (default: cwd)."""
    override = os.environ.get("NR_REPO_ROOT")
    if override:
        root = Path(override).resolve()
        if not is_repo_root(root):
            raise RepositoryNotFoundError(
                f"NR_REPO_ROOT={override!r} does not contain pyproject.toml and config/project.yaml"
            )
        return root
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if is_repo_root(candidate):
            return candidate
    raise RepositoryNotFoundError(
        "Could not find the nostradamus-research repository root "
        "(looked for pyproject.toml and config/project.yaml). "
        "Run the command from inside the repository or set NR_REPO_ROOT."
    )


def resolve(root: Path, path: str | Path) -> Path:
    """Resolve ``path`` relative to ``root`` unless it is already absolute."""
    p = Path(path)
    return p if p.is_absolute() else root / p
