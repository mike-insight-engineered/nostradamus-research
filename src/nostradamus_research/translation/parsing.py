"""Robust extraction of the JSON object from a model response."""

from __future__ import annotations

import json
import re
from typing import Any

from ..models.translation import AlternativeReading

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class ResponseParseError(ValueError):
    pass


def extract_json(text: str) -> dict[str, Any]:
    """Return the first top-level JSON object in ``text`` (code fences tolerated)."""
    candidates = [m.group(1) for m in _FENCE.finditer(text)] + [text]
    for cand in candidates:
        start = cand.find("{")
        while start != -1:
            depth, in_str, esc = 0, False, False
            for i in range(start, len(cand)):
                ch = cand[i]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                    continue
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            obj = json.loads(cand[start : i + 1])
                        except json.JSONDecodeError:
                            break
                        if isinstance(obj, dict):
                            return obj
                        break
            start = cand.find("{", start + 1)
    raise ResponseParseError("no JSON object found in model response")


def as_confidence(value: Any) -> float | None:
    """Accept a model-stated confidence only if it is a number in [0, 1]."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float) and 0.0 <= float(value) <= 1.0:
        return float(value)
    return None


def as_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [v for v in value if isinstance(v, str) and v.strip()]


def as_alternatives(value: Any) -> list[AlternativeReading]:
    out: list[AlternativeReading] = []
    if not isinstance(value, list):
        return out
    for item in value:
        if isinstance(item, dict) and isinstance(item.get("span"), str):
            readings = as_str_list(item.get("readings"))
            if readings:
                note = item.get("note")
                out.append(AlternativeReading(span=item["span"], readings=readings,
                                              note=note if isinstance(note, str) else None))  # fmt: skip
    return out
