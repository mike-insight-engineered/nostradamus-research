import csv
import json

import pytest

from nostradamus_research.evaluation.review_package import (
    REVIEW_COLUMNS,
    build_review_package,
    import_reviews,
    write_review_package,
)
from nostradamus_research.evaluation.synthetic import simulate_reviews
from nostradamus_research.models.enums import PipelineId
from nostradamus_research.translation.providers import MockProvider
from nostradamus_research.translation.runner import build_pipeline, settings_from_config
from nostradamus_research.utils.jsonl import write_jsonl


@pytest.fixture
def package(cfg, tmp_path, fixture_passages, fixture_registry, oracle):
    results = []
    for pid in (PipelineId.A_DIRECT, PipelineId.B_TWO_STAGE):
        pl = build_pipeline(
            pid.value, MockProvider(oracle=oracle), settings_from_config(cfg, pid.value), None
        )
        results += [pl.translate(p, f"run-{pid.value}") for p in fixture_passages[:4]]
    by_id = {p.passage_id: p for p in fixture_passages}
    pkg = build_review_package(results, by_id, fixture_registry, package_id="PKG-T", seed=5)
    write_review_package(
        pkg, tmp_path, instructions_template=cfg.path("report_templates_dir") / "human-review.md"
    )
    return pkg, by_id


def test_package_is_blinded(package):
    pkg, _ = package
    assert len(pkg.items) == 8
    blob = (pkg.package_dir / "items.jsonl").read_text(encoding="utf-8") + (
        pkg.package_dir / "review_sheet.csv"
    ).read_text(encoding="utf-8-sig")
    for leak in ("A_direct", "B_two_stage", "mock-deterministic", "run-", "result_id", "pipeline"):
        assert leak not in blob, leak
    assert pkg.key_path.parent != pkg.package_dir  # key kept outside the reviewer folder
    key = json.loads(pkg.key_path.read_text(encoding="utf-8"))
    assert set(key["items"]) == {i["review_item_id"] for i in pkg.items}
    assert "WARNING" in key
    readme = (pkg.package_dir / "README.md").read_text(encoding="utf-8")
    assert "PKG-T" in readme and "synthetic_fixture" in readme


def test_package_shows_source_and_provenance(package):
    pkg, by_id = package
    item = pkg.items[0]
    assert item["source_text"] == by_id[item["passage_id"]].diplomatic_transcription
    assert "status=" in item["provenance_summary"] and "rights=" in item["provenance_summary"]


def test_shuffle_is_seeded(cfg, fixture_passages, fixture_registry):
    pl = build_pipeline("A_direct", MockProvider(), settings_from_config(cfg, "A_direct"), None)
    results = [pl.translate(p, "r") for p in fixture_passages]
    by_id = {p.passage_id: p for p in fixture_passages}
    a = build_review_package(results, by_id, fixture_registry, package_id="P", seed=1)
    b = build_review_package(results, by_id, fixture_registry, package_id="P", seed=1)
    assert [i["review_item_id"] for i in a.items] == [i["review_item_id"] for i in b.items]


def _fill_csv(pkg, rows):
    path = pkg.package_dir / "review_sheet.csv"
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields, data = reader.fieldnames, list(reader)
    for row, update in zip(data, rows, strict=False):
        row.update(update)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(data)
    return path


def test_csv_import_roundtrip(package):
    pkg, _ = package
    good = {
        "reviewer_id": "Dr Reviewer",
        "reviewer_provenance": "expert",
        "reviewed_on": "2026-01-01",
        "judgement_fr": "acceptable",
        "judgement_en": "unacceptable",
        "errors_json": json.dumps(
            [
                {
                    "category": "lost_ambiguity",
                    "severity": "major",
                    "target_language": "en",
                    "note": "ambiguity resolved silently",
                }
            ]
        ),
        "alternative_readings": "reading one || reading two",
        "ambiguity_flag": "yes",
        "reviewer_confidence": "4",
        "supporting_references": "Consulted work A",
    }
    path = _fill_csv(pkg, [good])
    res = import_reviews(path, pkg.key_path)
    assert res.ok and len(res.reviews) == 1 and res.blank_rows == 7
    lr = res.reviews[0]
    assert lr.review.alternative_readings == ["reading one", "reading two"]
    assert lr.review.errors[0].category.value == "lost_ambiguity"
    assert lr.pipeline in ("A_direct", "B_two_stage") and lr.result_id.startswith("run-")


def test_import_rejects_bad_rows(package):
    pkg, _ = package
    bad = [
        {
            "reviewer_id": "Dr R",
            "reviewer_provenance": "expert",
            "reviewed_on": "2026-01-01",
            "judgement_en": "acceptable",
            "errors_json": "[not json",
        },
        {
            "reviewer_id": "Dr R",
            "reviewer_provenance": "expert",
            "reviewed_on": "2026-01-01",
            "judgement_en": "great",
        },
        {
            "reviewer_id": "SYNTHETIC-X",
            "reviewer_provenance": "synthetic_fixture",
            "reviewed_on": "2026-01-01",
            "judgement_en": "acceptable",
        },
    ]
    res = import_reviews(_fill_csv(pkg, bad), pkg.key_path)
    msgs = " ".join(e.message for e in res.errors)
    assert "errors_json" in msgs and "judgement_en" in msgs and "synthetic" in msgs
    assert not res.reviews


def test_jsonl_import_unknown_item_and_duplicates(package, tmp_path):
    pkg, by_id = package
    rows = simulate_reviews(pkg.items[:2], by_id, package_id=pkg.package_id)
    rows.append(dict(rows[0]))  # duplicate
    rows.append({**rows[1], "review_item_id": "RI-unknown", "review_id": "x"})
    path = tmp_path / "r.jsonl"
    write_jsonl(path, rows)
    res = import_reviews(path, pkg.key_path, allow_synthetic=True)
    msgs = " ".join(e.message for e in res.errors)
    assert "duplicate" in msgs and "not in package" in msgs
    assert len(res.reviews) == 4  # 2 items x 2 synthetic reviewers


def test_simulated_reviews_are_always_labelled(package):
    pkg, by_id = package
    rows = simulate_reviews(pkg.items, by_id, package_id=pkg.package_id)
    assert all(
        r["reviewer_id"].startswith("SYNTHETIC") and r["reviewer_provenance"] == "synthetic_fixture"
        for r in rows
    )
    assert all("SYNTHETIC" in r["comments"] for r in rows)
    with pytest.raises(ValueError):
        simulate_reviews(pkg.items, by_id, package_id="P", reviewer_ids=("Real Person",))


def test_review_columns_are_blank_in_export(package):
    pkg, _ = package
    with (pkg.package_dir / "review_sheet.csv").open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            assert all(row[c] == "" for c in REVIEW_COLUMNS)
