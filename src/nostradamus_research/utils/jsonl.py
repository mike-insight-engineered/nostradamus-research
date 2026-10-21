"""JSONL reading/writing with line-numbered, field-level validation errors."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError


@dataclass(frozen=True)
class RecordError:
    """A problem with one record in a JSONL file."""

    path: str
    line: int
    record_id: str | None
    message: str

    def __str__(self) -> str:
        rid = f" [{self.record_id}]" if self.record_id else ""
        return f"{self.path}:{self.line}{rid}: {self.message}"


@dataclass
class LoadResult[M: BaseModel]:
    records: list[M] = field(default_factory=list)
    errors: list[RecordError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def format_validation_error(exc: ValidationError) -> list[str]:
    """Turn a pydantic ValidationError into readable ``field.path: message`` lines."""
    lines = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"]) or "<record>"
        msg = err["msg"]
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        lines.append(f"{loc}: {msg}")
    return lines


def read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    """Read raw JSON objects with their 1-based line numbers. Blank lines are skipped."""
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            obj = json.loads(stripped)
            if not isinstance(obj, dict):
                raise ValueError(
                    f"{path}:{lineno}: expected a JSON object, got {type(obj).__name__}"
                )
            rows.append((lineno, obj))
    return rows


def load_models[M: BaseModel](
    path: Path, model: type[M], id_field: str | None = None
) -> LoadResult[M]:
    """Validate every line of ``path`` against ``model``, collecting all errors."""
    result: LoadResult[M] = LoadResult()
    if not path.exists():
        result.errors.append(RecordError(str(path), 0, None, "file does not exist"))
        return result
    with path.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                result.errors.append(RecordError(str(path), lineno, None, f"invalid JSON: {exc}"))
                continue
            rid = obj.get(id_field) if (id_field and isinstance(obj, dict)) else None
            try:
                result.records.append(model.model_validate(obj))
            except ValidationError as exc:
                for message in format_validation_error(exc):
                    result.errors.append(RecordError(str(path), lineno, rid, message))
    return result


def _to_jsonable(record: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(record, BaseModel):
        return record.model_dump(mode="json", exclude_none=False)
    return record


def write_jsonl(path: Path, records: Iterable[BaseModel | dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(_to_jsonable(record), ensure_ascii=False) + "\n")
            count += 1
    return count


def append_jsonl(path: Path, record: BaseModel | dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(_to_jsonable(record), ensure_ascii=False) + "\n")


def write_json(path: Path, obj: BaseModel | dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = obj.model_dump(mode="json") if isinstance(obj, BaseModel) else obj
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
