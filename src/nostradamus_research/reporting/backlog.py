"""Machine-readable research backlog (docs/project/backlog.yaml).

Software and research completion are tracked separately; an item is only
``Complete`` overall when every applicable workstream is complete.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..models.enums import BacklogStatus

NotApplicable = Literal["n/a"]


class BacklogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^CAL-\d{2}$")
    title: str
    workstream: Literal["software", "research", "both"]
    status: BacklogStatus
    software_status: BacklogStatus | NotApplicable
    research_status: BacklogStatus | NotApplicable
    depends_on: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def _check(self) -> BacklogItem:
        sw_needed = self.workstream in ("software", "both")
        rs_needed = self.workstream in ("research", "both")
        if sw_needed == (self.software_status == "n/a"):
            raise ValueError(
                f"{self.id}: software_status must be n/a iff workstream lacks software"
            )
        if rs_needed == (self.research_status == "n/a"):
            raise ValueError(
                f"{self.id}: research_status must be n/a iff workstream lacks research"
            )
        parts = [s for s in (self.software_status, self.research_status) if s != "n/a"]
        if self.status is BacklogStatus.COMPLETE and any(
            s != BacklogStatus.COMPLETE for s in parts
        ):
            raise ValueError(f"{self.id}: cannot be Complete while a workstream is incomplete")
        if self.status is BacklogStatus.COMPLETE and not self.evidence:
            raise ValueError(f"{self.id}: Complete items must cite evidence")
        if self.status is BacklogStatus.BLOCKED and not self.blockers:
            raise ValueError(f"{self.id}: Blocked items must list blockers")
        return self


class Backlog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    milestone: str
    updated: str
    items: list[BacklogItem]

    @model_validator(mode="after")
    def _check(self) -> Backlog:
        ids = [i.id for i in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate backlog IDs")
        unknown = {d for i in self.items for d in i.depends_on} - set(ids)
        if unknown:
            raise ValueError(f"unknown dependencies: {sorted(unknown)}")
        by_id = {i.id: i for i in self.items}
        for i in self.items:
            if i.status is BacklogStatus.COMPLETE:
                open_deps = [
                    d for d in i.depends_on if by_id[d].status is not BacklogStatus.COMPLETE
                ]
                if open_deps:
                    raise ValueError(f"{i.id} is Complete but depends on incomplete {open_deps}")
        return self

    def get(self, item_id: str) -> BacklogItem:
        return next(i for i in self.items if i.id == item_id)


def load_backlog(path: Path) -> Backlog:
    return Backlog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
