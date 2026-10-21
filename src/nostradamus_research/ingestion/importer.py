"""Import passage records from JSONL (or TEI) into the corpus file.

Import is conservative: it validates everything first, refuses duplicates,
refuses synthetic records in the research corpus, and writes nothing in
dry-run mode. When a record lacks ``diplomatic_sha256`` the importer locks the
transcription by computing it and appends a ``created`` review event.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..models.enums import DataOrigin
from ..models.passage import Passage
from ..provenance.registry import SourceRegistry
from ..transcription.integrity import lock_hash
from ..transcription.tei import diplomatic_text_from_tei
from ..utils.jsonl import RecordError, format_validation_error, read_jsonl, write_jsonl


@dataclass
class ImportOutcome:
    accepted: list[Passage] = field(default_factory=list)
    errors: list[RecordError] = field(default_factory=list)
    written_to: Path | None = None
    dry_run: bool = True

    @property
    def ok(self) -> bool:
        return not self.errors


def _prepare(raw: dict[str, Any], *, imported_by: str, base_dir: Path) -> dict[str, Any]:
    raw = dict(raw)
    tei_file = raw.pop("tei_file", None)
    if tei_file and "diplomatic_transcription" not in raw:
        xml = (base_dir / tei_file).read_text(encoding="utf-8")
        raw["diplomatic_transcription"] = diplomatic_text_from_tei(xml)
        raw.setdefault("transcription_format", "tei")
    if "diplomatic_sha256" not in raw and isinstance(raw.get("diplomatic_transcription"), str):
        raw["diplomatic_sha256"] = lock_hash(raw["diplomatic_transcription"])
        raw["review_history"] = [
            *raw.get("review_history", []),
            {"on": date.today().isoformat(), "by": imported_by, "action": "created",
             "notes": "imported; diplomatic transcription hash locked"},
        ]  # fmt: skip
    return raw


def import_passages(
    input_path: Path,
    corpus_path: Path,
    registry: SourceRegistry,
    *,
    imported_by: str,
    dry_run: bool = True,
    allow_synthetic: bool = False,
) -> ImportOutcome:
    outcome = ImportOutcome(dry_run=dry_run)
    existing: list[Passage] = []
    if corpus_path.exists():
        for _, obj in read_jsonl(corpus_path):
            existing.append(Passage.model_validate(obj))
    existing_ids = {p.passage_id for p in existing}
    batch_ids: set[str] = set()

    try:
        rows = read_jsonl(input_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        outcome.errors.append(RecordError(str(input_path), 0, None, f"cannot read input: {exc}"))
        return outcome

    for lineno, raw in rows:
        rid = raw.get("passage_id")
        try:
            passage = Passage.model_validate(
                _prepare(raw, imported_by=imported_by, base_dir=input_path.parent)
            )
        except ValidationError as exc:
            for msg in format_validation_error(exc):
                outcome.errors.append(RecordError(str(input_path), lineno, rid, msg))
            continue
        except (OSError, ValueError) as exc:
            outcome.errors.append(RecordError(str(input_path), lineno, rid, str(exc)))
            continue
        problems = []
        if passage.passage_id in existing_ids:
            problems.append("passage_id already exists in the corpus (use a correction workflow)")
        if passage.passage_id in batch_ids:
            problems.append("passage_id duplicated within the import file")
        if passage.source_id not in registry:
            problems.append(f"source_id {passage.source_id} is not in the source registry")
        if passage.data_origin is DataOrigin.SYNTHETIC_FIXTURE and not allow_synthetic:
            problems.append(
                "synthetic fixture passages may not be imported into the research corpus"
            )
        for msg in problems:
            outcome.errors.append(RecordError(str(input_path), lineno, rid, msg))
        if not problems:
            batch_ids.add(passage.passage_id)
            outcome.accepted.append(passage)

    if outcome.ok and not dry_run and outcome.accepted:
        write_jsonl(corpus_path, [*existing, *outcome.accepted])
        outcome.written_to = corpus_path
    return outcome
