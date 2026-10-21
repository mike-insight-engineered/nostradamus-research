"""JSONL-backed historical source registry.

The registry is append-friendly and reviewed through Git. Status changes go
through :meth:`SourceRegistry.promote`, which enforces the one-rung-at-a-time
transition rule and the cumulative evidence requirements in
:mod:`nostradamus_research.models.status_policy`.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from ..models.enums import VerificationStatus
from ..models.source import HistoricalSource, StatusChange, VerificationEvidence
from ..models.status_policy import allowed_transition
from ..utils.jsonl import LoadResult, RecordError, format_validation_error, load_models, write_jsonl


class RegistryError(ValueError):
    pass


class SourceRegistry:
    def __init__(self, sources: list[HistoricalSource] | None = None, path: Path | None = None):
        self.path = path
        self._sources: dict[str, HistoricalSource] = {}
        for s in sources or []:
            self._add(s)

    # -- loading / saving ---------------------------------------------------------
    @classmethod
    def load(cls, path: Path) -> tuple[SourceRegistry, list[RecordError]]:
        if not path.exists():
            return cls(path=path), []
        result: LoadResult[HistoricalSource] = load_models(path, HistoricalSource, "source_id")
        registry = cls(path=path)
        errors = list(result.errors)
        for s in result.records:
            try:
                registry._add(s)
            except RegistryError as exc:
                errors.append(RecordError(str(path), 0, s.source_id, str(exc)))
        return registry, errors

    def save(self, path: Path | None = None) -> Path:
        target = path or self.path
        if target is None:
            raise RegistryError("no registry path given")
        ordered: list[HistoricalSource] = sorted(self._sources.values(), key=lambda s: s.source_id)
        write_jsonl(target, ordered)
        return target

    def export_csv(self, path: Path) -> None:
        """Write a reviewer-friendly candidates CSV (one row per source)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        cols = [
            "source_id", "record_type", "title", "author", "date_text", "printer_publisher",
            "place_of_publication", "holding_institution", "stable_url", "rights_status",
            "verification_status", "outstanding_work",
        ]  # fmt: skip
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=cols)
            writer.writeheader()
            for s in sorted(self._sources.values(), key=lambda s: s.source_id):
                row = s.model_dump(mode="json")
                out = {c: row.get(c) for c in cols}
                out["outstanding_work"] = " | ".join(s.outstanding_work)
                writer.writerow(out)

    # -- access ------------------------------------------------------------------------
    def _add(self, source: HistoricalSource) -> None:
        if source.source_id in self._sources:
            raise RegistryError(f"duplicate source_id {source.source_id}")
        self._sources[source.source_id] = source

    def __contains__(self, source_id: object) -> bool:
        return source_id in self._sources

    def __len__(self) -> int:
        return len(self._sources)

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(sorted(self._sources.values(), key=lambda s: s.source_id))

    def get(self, source_id: str) -> HistoricalSource:
        try:
            return self._sources[source_id]
        except KeyError:
            raise RegistryError(f"unknown source_id {source_id}") from None

    def status_counts(self) -> Counter[str]:
        return Counter(str(s.verification_status) for s in self._sources.values())

    # -- mutation ----------------------------------------------------------------------
    def register(self, source: HistoricalSource) -> HistoricalSource:
        """Add a new source. New registrations must start at ``candidate`` or ``located``."""
        if source.verification_status not in (
            VerificationStatus.CANDIDATE,
            VerificationStatus.LOCATED,
        ):
            raise RegistryError(
                "new sources are registered as 'candidate' or 'located'; higher statuses must be "
                "reached through `promote` with documented evidence"
            )
        self._add(source)
        return source

    def promote(
        self,
        source_id: str,
        new_status: VerificationStatus,
        *,
        changed_by: str,
        reason: str,
        evidence: list[VerificationEvidence] | None = None,
        on: date | None = None,
        updates: dict[str, object] | None = None,
    ) -> HistoricalSource:
        """Move a source to ``new_status``, validating transition and evidence."""
        current = self.get(source_id)
        if not allowed_transition(current.verification_status, new_status):
            raise RegistryError(
                f"cannot move {source_id} from '{current.verification_status}' to '{new_status}': "
                "promotion is one rung at a time"
            )
        data = current.model_dump()
        data.update(updates or {})
        data["verification_evidence"] = [
            *current.verification_evidence,
            *(evidence or []),
        ]
        try:
            change = StatusChange(
                from_status=current.verification_status,
                to_status=new_status,
                changed_by=changed_by,
                changed_on=on or date.today(),
                reason=reason,
            )
            data["status_history"] = [*current.status_history, change]
            data["verification_status"] = new_status
            updated = HistoricalSource.model_validate(data)
        except ValidationError as exc:
            raise RegistryError("; ".join(format_validation_error(exc))) from exc
        self._sources[source_id] = updated
        return updated
