"""Report D — Milestone Gate: deliverables, acceptance criteria, recommendation.

Each criterion is ``passed``, ``failed`` (evaluated and not yet met) or
``not_evaluated`` (cannot be assessed from repository state, e.g. because a
prerequisite is missing). Software readiness and research readiness are
reported separately; the go/no-go recommendation can only be ``continue`` when
research criteria pass on non-synthetic, expert-reviewed data.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ..config import AppConfig
from ..corpus.io import load_passages
from ..corpus.leakage import check_leakage
from ..corpus.stats import compute_stats, is_eligible
from ..models.enums import (
    COMMITTABLE_RIGHTS,
    DataOrigin,
    EvidenceLevel,
    PipelineId,
    RecordType,
    TargetLanguage,
    VerificationStatus,
    status_rank,
)
from ..models.experiment import ExperimentManifest
from ..provenance.audit import audit_corpus
from ..provenance.registry import SourceRegistry
from ..translation.prompts import PromptLibrary
from ..utils.runtime import git_commit, utc_now
from .backlog import Backlog, load_backlog
from .common import bullet, md_table, render_template

Status = Literal["passed", "failed", "not_evaluated"]


@dataclass
class Criterion:
    cid: str
    area: Literal["software", "research"]
    description: str
    status: Status
    detail: str


@dataclass
class GateResult:
    criteria: list[Criterion] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    recommendation: Literal["continue", "remediate", "defer"] = "remediate"
    rationale: str = ""
    backlog: Backlog | None = None

    def add(
        self,
        cid: str,
        area: Literal["software", "research"],
        desc: str,
        status: Status,
        detail: str,
    ) -> None:
        self.criteria.append(Criterion(cid, area, desc, status, detail))


def _load_manifests(runs_dir: Path) -> list[ExperimentManifest]:
    out = []
    for path in sorted(runs_dir.glob("*/manifest.json")):
        try:
            out.append(
                ExperimentManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))
            )
        except (ValueError, OSError):
            continue
    return out


def evaluate_gate(cfg: AppConfig, *, schemas_current: bool | None = None) -> GateResult:
    gate = GateResult()

    # ---------------- software criteria ----------------
    gate.add(
        "S1", "software", "Configuration files load and validate", "passed", "config/*.yaml valid"
    )
    registry, reg_errors = SourceRegistry.load(cfg.path("source_registry"))
    gate.add("S2", "software", "Source registry validates against the schema",
             "passed" if not reg_errors else "failed",
             f"{len(registry)} records, {len(reg_errors)} errors")  # fmt: skip
    try:
        lib = PromptLibrary.load()
        for tid, ver in cfg.translation.prompt_versions.items():
            lib.get(tid, ver)
        gate.add("S3", "software", "Pipelines A–D and pinned prompt templates load", "passed",
                 f"{len(PipelineId)} pipelines; {len(lib.templates)} templates")  # fmt: skip
    except Exception as exc:
        gate.add(
            "S3", "software", "Pipelines A–D and pinned prompt templates load", "failed", str(exc)
        )
    if schemas_current is None:
        gate.add("S4", "software", "JSON Schemas match the Pydantic models", "not_evaluated",
                 "run scripts/validate_repository.py")  # fmt: skip
    else:
        gate.add("S4", "software", "JSON Schemas match the Pydantic models",
                 "passed" if schemas_current else "failed", "compared generated vs committed")  # fmt: skip
    gate.add("S5", "software", "Automated test suite passes", "not_evaluated",
             "evaluated by CI / `make test`, not by this report")  # fmt: skip

    # ---------------- research criteria ----------------
    ppath = cfg.path("passages")
    passages = load_passages(ppath).records if ppath.exists() else []
    real = [p for p in passages if p.data_origin is DataOrigin.HISTORICAL_SOURCE]
    stats = compute_stats(real, cfg.corpus)

    witnesses = [s for s in registry if s.record_type is RecordType.WITNESS]
    checked = [
        s
        for s in witnesses
        if status_rank(s.verification_status) >= status_rank(VerificationStatus.PROVENANCE_CHECKED)
    ]
    gate.add("R1", "research", "Witnesses with checked provenance are registered",
             "passed" if checked else "failed",
             f"{len(checked)} of {len(witnesses)} witness records at provenance_checked or above")  # fmt: skip

    pilot_detail = "; ".join(f"{t.label}: {t.eligible}/{t.target}" for t in stats.pilot_progress)
    pilot_ok = all(t.met for t in stats.pilot_progress)
    gate.add("R2", "research", "20-passage pilot meets category quotas with verified transcriptions",
             "passed" if pilot_ok else "failed", f"eligible passages — {pilot_detail}")  # fmt: skip

    eligible = [p for p in real if is_eligible(p, cfg.corpus)]
    rights_ok = [
        p for p in eligible
        if all(r.rights_status in COMMITTABLE_RIGHTS and r.independent_of_evaluated_models
               for r in p.references_for(TargetLanguage.MODERN_FRENCH) + p.references_for(TargetLanguage.ENGLISH))
    ]  # fmt: skip
    gate.add("R3", "research", "Independent FR and EN references with cleared rights",
             "not_evaluated" if not eligible else ("passed" if len(rights_ok) == len(eligible) else "failed"),
             f"{len(rights_ok)} of {len(eligible)} eligible passages")  # fmt: skip

    audit = audit_corpus(
        registry, real, forbid_synthetic=cfg.project.integrity.forbid_synthetic_in_corpus
    )
    gate.add("R4", "research", "Provenance audit has no errors",
             "not_evaluated" if not real else ("passed" if audit.ok else "failed"),
             f"{len(audit.errors)} errors, {len(audit.warnings)} warnings over {len(real)} passages")  # fmt: skip

    assigned = [p for p in real if str(p.split) != "unassigned"]
    if assigned:
        leak = check_leakage(real, near_duplicate_threshold=cfg.corpus.leakage.near_duplicate_threshold,
                             shingle_size=cfg.corpus.leakage.shingle_size, group_by=cfg.corpus.splits.group_by)  # fmt: skip
        gate.add("R5", "research", "Partitions are leakage-free", "passed" if leak.ok else "failed",
                 f"{len(leak.errors)} leakage errors")  # fmt: skip
    else:
        gate.add(
            "R5",
            "research",
            "Partitions are leakage-free",
            "not_evaluated",
            "no passages assigned to splits",
        )

    manifests = [
        m
        for m in _load_manifests(cfg.path("runs_dir"))
        if m.evidence_level is not EvidenceLevel.SYNTHETIC_FIXTURE and not m.is_mock
    ]
    covered = {m.pipeline for m in manifests if m.status in ("completed", "partial")}
    gate.add("R6", "research", "All four pipelines benchmarked on real passages with a real provider",
             "passed" if covered == set(PipelineId) else ("failed" if real else "not_evaluated"),
             f"pipelines with non-synthetic, non-mock runs: {sorted(map(str, covered)) or 'none'}")  # fmt: skip

    reviews_dir = cfg.root / "data" / "annotations" / "reviews"
    n_reviews = (
        sum(
            1
            for f in reviews_dir.glob("*.jsonl")
            for line in f.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if reviews_dir.exists()
        else 0
    )
    gate.add("R7", "research", "Blinded expert review of pilot outputs completed",
             "not_evaluated" if not covered else ("passed" if n_reviews else "failed"),
             f"{n_reviews} imported review records in data/annotations/reviews/")  # fmt: skip
    gate.add(
        "R8",
        "research",
        "Calibration analysis on expert labels with sufficient sample",
        "not_evaluated",
        "requires R6 and R7",
    )

    # ---------------- backlog consistency ----------------
    try:
        backlog = load_backlog(cfg.path("backlog"))
        gate.backlog = backlog
        quota = {
            "CAL-05": "french_prose",
            "CAL-06": "french_poetry",
            "CAL-07": "latin",
            "CAL-08": "mixed_or_difficult",
        }
        by_group = {t.label: t for t in stats.pilot_progress}
        for item_id, group in quota.items():
            item = backlog.get(item_id)
            if str(item.status) == "Complete" and not by_group[group].met:
                gate.blockers.append(
                    f"{item_id} is marked Complete but only {by_group[group].eligible} eligible {group} passages exist"
                )
        gate.add("S6", "software", "Backlog file validates and is consistent with corpus state",
                 "passed" if not gate.blockers else "failed", f"{len(backlog.items)} items")  # fmt: skip
    except Exception as exc:
        gate.add(
            "S6",
            "software",
            "Backlog file validates and is consistent with corpus state",
            "failed",
            str(exc),
        )

    # ---------------- blockers & recommendation ----------------
    status_by = Counter((c.area, c.status) for c in gate.criteria)
    for c in gate.criteria:
        if c.area == "research" and c.status != "passed":
            gate.blockers.append(f"{c.cid}: {c.description} — {c.detail}")
    sw_failed = status_by[("software", "failed")]
    rs_passed = status_by[("research", "passed")]
    n_research = sum(1 for c in gate.criteria if c.area == "research")
    if sw_failed:
        gate.recommendation = "remediate"
        gate.rationale = "Software criteria failed; fix the framework before any research use."
    elif rs_passed == n_research:
        gate.recommendation = "continue"
        gate.rationale = "All research acceptance criteria passed on non-synthetic data."
    elif not real:
        gate.recommendation = "defer"
        gate.rationale = (
            "The software foundation is ready for review, but no verified historical passages, "
            "independent reference translations or expert reviews exist yet. The go/no-go decision "
            "on AI translation reliability is deferred until CAL-05 to CAL-10 are complete."
        )
    else:
        gate.recommendation = "remediate"
        gate.rationale = (
            "Research criteria are incomplete; complete the outstanding data and review work."
        )
    return gate


def render_gate(gate: GateResult, cfg: AppConfig, template: Path) -> str:
    rows = [
        (c.cid, c.area, c.description, c.status.upper().replace("_", " "), c.detail)
        for c in gate.criteria
    ]
    backlog_rows = []
    if gate.backlog:
        backlog_rows = [
            (i.id, i.title, i.status, i.software_status, i.research_status)
            for i in gate.backlog.items
        ]
    deliverables = [
        "Repository structure, configuration, CI and documentation",
        "Source registry with provenance/licensing tracking and status policy",
        "Canonical passage model and generated JSON Schemas",
        "Translation pipelines A–D with versioned prompts and provider adapters (mock, Anthropic, OpenAI)",
        "Evaluation framework (MQM taxonomy, chrF, blinded review, agreement)",
        "Confidence calibration module and reports",
        "20 verified pilot passages with independent references (research — see R2/R3)",
        "Blinded expert review and calibration of the pilot (research — see R7/R8)",
    ]
    return render_template(
        template,
        banner=(
            "> **This gate report reflects repository state only.** It contains no translation-quality "
            "results. Synthetic fixtures and mock runs are excluded from every research criterion."
        ),
        generated_at=utc_now().isoformat(),
        git_commit=git_commit(cfg.root) or "unknown",
        milestone=f"{cfg.project.project.milestone} — {cfg.project.project.milestone_title}",
        deliverables=bullet(deliverables),
        criteria_table=md_table(["ID", "Area", "Criterion", "Status", "Detail"], rows),
        backlog_table=md_table(["ID", "Title", "Overall", "Software", "Research"], backlog_rows)
        if backlog_rows
        else "Backlog unavailable.",
        blockers=bullet(gate.blockers),
        recommendation=gate.recommendation.upper(),
        rationale=gate.rationale,
    )
