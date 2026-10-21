"""Blinded human-review packages: export for reviewers, import completed reviews.

Blinding: review items carry an opaque ``review_item_id`` and are shuffled with
a seeded RNG. Pipeline, provider, model, run and result identifiers are written
only to a separate key file in a ``<package>-KEY`` directory that must not be
shared with reviewers. Structured analysis (pipeline D) and the intermediate
French text are not shown, as they would reveal the pipeline.
"""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from string import Template
from typing import Any

from pydantic import ValidationError

from ..models.enums import ReviewerProvenance
from ..models.passage import Passage
from ..models.review import HumanReview
from ..models.translation import TranslationResult
from ..provenance.registry import SourceRegistry
from ..utils.jsonl import RecordError, format_validation_error, read_jsonl, write_json, write_jsonl

ITEM_COLUMNS = [
    "review_item_id", "passage_id", "language", "genre", "date_text", "source_text", "locator",
    "facsimile_reference", "provenance_summary", "translation_fr", "translation_en",
    "offered_alternatives", "declared_ambiguities",
]  # fmt: skip
REVIEW_COLUMNS = [
    "reviewer_id", "reviewer_provenance", "reviewed_on", "judgement_fr", "judgement_en",
    "errors_json", "alternative_readings", "ambiguity_flag", "unresolvable", "reviewer_confidence",
    "supporting_references", "comments", "time_spent_minutes",
]  # fmt: skip
LIST_SEP = " || "


@dataclass
class ReviewPackage:
    package_id: str
    items: list[dict[str, Any]]
    key: dict[str, dict[str, str]]
    package_dir: Path | None = None
    key_path: Path | None = None
    skipped: list[str] = field(default_factory=list)


def _provenance_summary(p: Passage, registry: SourceRegistry | None) -> str:
    if registry is None or p.source_id not in registry:
        return f"source {p.source_id} (not found in registry)"
    s = registry.get(p.source_id)
    bits = [s.title, s.author, s.date_text, s.printer_publisher, s.place_of_publication,
            s.holding_institution, s.catalogue_identifier]  # fmt: skip
    desc = "; ".join(b for b in bits if b)
    return f"{s.source_id}: {desc} | status={s.verification_status} | rights={s.rights_status} | origin={s.data_origin}"


def build_review_package(
    results: list[TranslationResult],
    passages: dict[str, Passage],
    registry: SourceRegistry | None,
    *,
    package_id: str,
    seed: int,
) -> ReviewPackage:
    rng = random.Random(seed)
    usable = [r for r in results if r.succeeded and r.passage_id in passages]
    skipped = [r.result_id for r in results if r not in usable]
    rng.shuffle(usable)
    items, key = [], {}
    used: set[str] = set()
    for r in usable:
        while True:
            item_id = f"RI-{rng.getrandbits(40):010x}"
            if item_id not in used:
                used.add(item_id)
                break
        p = passages[r.passage_id]
        alts = [f"{a.span}: {' / '.join(a.readings)}" for a in r.alternatives]
        items.append({
            "review_item_id": item_id,
            "package_id": package_id,
            "passage_id": p.passage_id,
            "language": str(p.language),
            "genre": str(p.genre),
            "date_text": p.date_text or "",
            "source_text": p.diplomatic_transcription,
            "locator": p.locator or "",
            "facsimile_reference": p.facsimile_reference or "",
            "provenance_summary": _provenance_summary(p, registry),
            "data_origin": str(p.data_origin),
            "translation_fr": r.translation_fr or "",
            "translation_en": r.translation_en or "",
            "offered_alternatives": LIST_SEP.join(alts),
            "declared_ambiguities": LIST_SEP.join(r.unresolved_ambiguities),
        })  # fmt: skip
        key[item_id] = {"result_id": r.result_id, "run_id": r.run_id, "passage_id": r.passage_id,
                        "pipeline": str(r.pipeline), "provider": r.provider, "model": r.model}  # fmt: skip
    return ReviewPackage(package_id, items, key, skipped=skipped)


def write_review_package(
    package: ReviewPackage, out_dir: Path, *, instructions_template: Path | None = None
) -> ReviewPackage:
    pdir = out_dir / package.package_id
    kdir = out_dir / f"{package.package_id}-KEY"
    write_jsonl(pdir / "items.jsonl", package.items)
    with (pdir / "review_sheet.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=ITEM_COLUMNS + REVIEW_COLUMNS, extrasaction="ignore"
        )
        writer.writeheader()
        for item in package.items:
            writer.writerow({**item, **dict.fromkeys(REVIEW_COLUMNS, "")})
    if instructions_template is not None and instructions_template.is_file():
        text = Template(instructions_template.read_text(encoding="utf-8")).safe_substitute(
            package_id=package.package_id, n_items=len(package.items),
            data_origins=", ".join(sorted({i["data_origin"] for i in package.items})) or "none",
        )  # fmt: skip
        (pdir / "README.md").write_text(text, encoding="utf-8")
    write_json(kdir / "key.json", {
        "WARNING": "Unblinding key. Do NOT share with reviewers.",
        "package_id": package.package_id, "items": package.key,
    })  # fmt: skip
    package.package_dir, package.key_path = pdir, kdir / "key.json"
    return package


# --- import -------------------------------------------------------------------------


@dataclass
class LinkedReview:
    review: HumanReview
    result_id: str
    run_id: str
    passage_id: str
    pipeline: str


@dataclass
class ImportedReviews:
    reviews: list[LinkedReview] = field(default_factory=list)
    errors: list[RecordError] = field(default_factory=list)
    blank_rows: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def _split_list(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(LIST_SEP.strip()) if v.strip()]


def _bool(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "y", "x")


def _row_to_review(row: dict[str, Any], package_id: str) -> dict[str, Any]:
    """Convert a CSV row (all strings) into HumanReview input."""

    def opt(k: str) -> str | None:
        v = row.get(k)
        return v.strip() if isinstance(v, str) and v.strip() else None

    errors_raw = opt("errors_json")
    try:
        errors = json.loads(errors_raw) if errors_raw else []
    except json.JSONDecodeError as exc:
        raise ValueError(f"errors_json is not valid JSON: {exc}") from exc
    return {
        "review_id": f"{package_id}:{opt('review_item_id')}:{opt('reviewer_id')}",
        "review_item_id": opt("review_item_id"),
        "package_id": package_id,
        "reviewer_id": opt("reviewer_id"),
        "reviewer_provenance": opt("reviewer_provenance"),
        "reviewed_on": opt("reviewed_on"),
        "judgement_fr": opt("judgement_fr"),
        "judgement_en": opt("judgement_en"),
        "errors": errors,
        "alternative_readings": _split_list(opt("alternative_readings")),
        "ambiguity_flag": _bool(opt("ambiguity_flag")),
        "unresolvable": _bool(opt("unresolvable")),
        "reviewer_confidence": int(v) if (v := opt("reviewer_confidence")) else None,
        "supporting_references": _split_list(opt("supporting_references")),
        "comments": opt("comments"),
        "time_spent_minutes": float(v) if (v := opt("time_spent_minutes")) else None,
    }


def import_reviews(
    path: Path,
    key_path: Path,
    *,
    allow_synthetic: bool = False,
) -> ImportedReviews:
    key_doc = json.loads(key_path.read_text(encoding="utf-8"))
    package_id: str = key_doc["package_id"]
    key: dict[str, dict[str, str]] = key_doc["items"]
    out = ImportedReviews()
    raw_rows: list[tuple[int, dict[str, Any], bool]] = []
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for i, row in enumerate(csv.DictReader(handle), start=2):
                raw_rows.append((i, row, True))
    else:
        raw_rows = [(i, r, False) for i, r in read_jsonl(path)]

    seen: set[tuple[str, str]] = set()
    for lineno, row, is_csv in raw_rows:
        item_id = row.get("review_item_id")
        if is_csv and not (row.get("reviewer_id") or "").strip():
            out.blank_rows += 1  # not yet reviewed
            continue
        try:
            data = _row_to_review(row, package_id) if is_csv else {"package_id": package_id, **row}
            if not is_csv:
                data.setdefault("review_id", f"{package_id}:{item_id}:{row.get('reviewer_id')}")
            review = HumanReview.model_validate(data)
        except ValidationError as exc:
            for msg in format_validation_error(exc):
                out.errors.append(RecordError(str(path), lineno, item_id, msg))
            continue
        except ValueError as exc:
            out.errors.append(RecordError(str(path), lineno, item_id, str(exc)))
            continue
        problems = []
        if review.review_item_id not in key:
            problems.append(
                f"review_item_id {review.review_item_id} is not in package {package_id}"
            )
        if review.package_id != package_id:
            problems.append(f"package_id {review.package_id} does not match key {package_id}")
        pair = (review.review_item_id, review.reviewer_id)
        if pair in seen:
            problems.append("duplicate review by the same reviewer for this item")
        if (
            review.reviewer_provenance is ReviewerProvenance.SYNTHETIC_FIXTURE
            and not allow_synthetic
        ):
            problems.append(
                "synthetic reviews are only accepted for demonstrations (--allow-synthetic)"
            )
        if review.reviewed_on > date.today():
            problems.append("reviewed_on is in the future")
        if problems:
            for msg in problems:
                out.errors.append(RecordError(str(path), lineno, item_id, msg))
            continue
        seen.add(pair)
        k = key[review.review_item_id]
        out.reviews.append(
            LinkedReview(review, k["result_id"], k["run_id"], k["passage_id"], k["pipeline"])
        )
    return out


def write_linked_reviews(path: Path, reviews: list[LinkedReview]) -> None:
    write_jsonl(path, [{"result_id": lr.result_id, "run_id": lr.run_id, "passage_id": lr.passage_id,
                        "pipeline": lr.pipeline, "review": lr.review.model_dump(mode="json")}
                       for lr in reviews])  # fmt: skip


def read_linked_reviews(path: Path) -> list[LinkedReview]:
    out = []
    for _, row in read_jsonl(path):
        out.append(LinkedReview(HumanReview.model_validate(row["review"]), row["result_id"],
                                row["run_id"], row["passage_id"], row["pipeline"]))  # fmt: skip
    return out
