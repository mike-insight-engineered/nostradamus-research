import json
import re

import jsonschema
import pytest
import yaml
from pydantic import ValidationError

from nostradamus_research.models import SCHEMA_MODELS
from nostradamus_research.models.enums import EvidenceLevel
from nostradamus_research.reporting.backlog import Backlog, load_backlog
from nostradamus_research.reporting.common import evidence_banner, md_table, render_template
from nostradamus_research.reporting.milestone_gate import evaluate_gate, render_gate
from nostradamus_research.schemas import build_schema, stale_schemas
from tests.conftest import FIXTURES


def test_banners_pick_weakest_evidence():
    assert "SYNTHETIC" in evidence_banner(
        [EvidenceLevel.EXPERT_REVIEWED, EvidenceLevel.SYNTHETIC_FIXTURE]
    )
    assert "AUTOMATED METRICS ONLY" in evidence_banner(["automated_only", "expert_reviewed"])
    assert "Expert-reviewed" in evidence_banner(["expert_reviewed"])
    assert "NO RESULTS" in evidence_banner([])


def test_md_table_escapes():
    t = md_table(["a", "b"], [("x|y", None), (1.23456, "z\nw")])
    assert "x\\|y" in t and "—" in t and "1.235" in t and "z w" in t


def test_all_templates_render_when_values_supplied(cfg):
    tdir = cfg.path("report_templates_dir")
    for name in (
        "source-audit.md",
        "benchmark-report.md",
        "calibration-report.md",
        "milestone-gate.md",
    ):
        text = (tdir / name).read_text(encoding="utf-8")
        keys = set(re.findall(r"\$\{(\w+)\}", text))
        assert keys, name
        out = render_template(tdir / name, **{k: f"<{k}>" for k in keys})
        assert "${" not in out
        with pytest.raises(KeyError):
            render_template(tdir / name)


def test_gate_on_current_repository_defers(cfg):
    gate = evaluate_gate(cfg, schemas_current=True)
    by_id = {c.cid: c for c in gate.criteria}
    assert (
        by_id["S1"].status == "passed"
        and by_id["S2"].status == "passed"
        and by_id["S3"].status == "passed"
    )
    assert by_id["R2"].status == "failed"  # no verified passages exist
    assert all(c.status != "passed" for c in gate.criteria if c.area == "research")
    assert gate.recommendation == "defer"
    text = render_gate(gate, cfg, cfg.path("report_templates_dir") / "milestone-gate.md")
    assert "DEFER" in text and "CAL-05" in text


def test_backlog_is_valid_and_honest(cfg):
    bl = load_backlog(cfg.path("backlog"))
    assert [i.id for i in bl.items] == [f"CAL-{n:02d}" for n in range(1, 15)]
    # No data-acquisition or review task may be Complete while the corpus is empty.
    for item_id in (
        "CAL-05",
        "CAL-06",
        "CAL-07",
        "CAL-08",
        "CAL-09",
        "CAL-10",
        "CAL-11",
        "CAL-12",
        "CAL-13",
        "CAL-14",
    ):
        assert str(bl.get(item_id).status) != "Complete"
    md = (cfg.root / "docs" / "project" / "backlog.md").read_text(encoding="utf-8")
    for item in bl.items:
        assert item.id in md and str(item.status) in md


def test_backlog_validation_rules(cfg):
    data = yaml.safe_load(cfg.path("backlog").read_text(encoding="utf-8"))
    data["items"][4]["status"] = "Complete"  # CAL-05 without evidence/workstream completion
    with pytest.raises(ValidationError, match="Complete"):
        Backlog.model_validate(data)


def test_committed_schemas_are_current(cfg):
    assert stale_schemas(cfg.path("schemas_dir")) == []
    assert set(SCHEMA_MODELS) >= {
        "historical_source",
        "passage",
        "reference_translation",
        "translation_result",
        "human_review",
        "evaluation_result",
        "experiment_manifest",
    }


def test_fixture_records_validate_against_json_schemas(cfg):
    for stem, fname in (
        ("passage", "synthetic_passages.jsonl"),
        ("historical_source", "synthetic_sources.jsonl"),
        ("lexical_evidence", "synthetic_lexical_evidence.jsonl"),
    ):
        schema = build_schema(stem)
        for line in (FIXTURES / fname).read_text(encoding="utf-8").splitlines():
            jsonschema.validate(json.loads(line), schema)
    registry_schema = build_schema("historical_source")
    for line in cfg.path("source_registry").read_text(encoding="utf-8").splitlines():
        jsonschema.validate(json.loads(line), registry_schema)


def test_json_schema_rejects_bad_record():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"passage_id": "bad"}, build_schema("passage"))
