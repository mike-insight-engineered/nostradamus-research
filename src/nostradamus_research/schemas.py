"""Generate JSON Schemas from the Pydantic models and detect drift."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import SCHEMA_MODELS

SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"


def build_schema(stem: str) -> dict[str, Any]:
    model = SCHEMA_MODELS[stem]
    schema = model.model_json_schema(mode="validation")
    return {
        "$schema": SCHEMA_DRAFT,
        "$id": f"https://github.com/nostradamus-research/schemas/{stem}.schema.json",
        **schema,
    }


def render(stem: str) -> str:
    return json.dumps(build_schema(stem), indent=2, ensure_ascii=False) + "\n"


def generate_schemas(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for stem in SCHEMA_MODELS:
        path = directory / f"{stem}.schema.json"
        path.write_text(render(stem), encoding="utf-8", newline="\n")
        written.append(path)
    return written


def stale_schemas(directory: Path) -> list[str]:
    """Stems whose committed schema differs from the generated one (or is missing)."""
    stale = []
    for stem in SCHEMA_MODELS:
        path = directory / f"{stem}.schema.json"
        if not path.is_file() or path.read_text(encoding="utf-8").replace("\r\n", "\n") != render(
            stem
        ):
            stale.append(stem)
    return stale
