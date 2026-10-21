import json
import subprocess
import sys

import pytest

from nostradamus_research.demo import run_demo

pytestmark = pytest.mark.integration


def test_offline_demo_end_to_end(cfg, tmp_path):
    s = run_demo(cfg, tmp_path)
    assert s["n_passages"] == 12 and s["n_results"] == 48 and s["n_failed"] == 0
    assert s["leakage_errors"] == 0 and s["audit_errors"] == 0
    assert s["n_reviews"] == 2 * s["n_review_items"]
    assert sum(s["splits"].values()) == 12
    for rep in ("source-audit.md", "benchmark-report.md", "calibration-report.md"):
        text = (tmp_path / "reports" / rep).read_text(encoding="utf-8")
        assert "SYNTHETIC" in text, rep
    for pid in ("A_direct", "B_two_stage", "C_retrieval", "D_structured"):
        manifest = json.loads(
            (tmp_path / "runs" / f"demo-{pid}" / "manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["evidence_level"] == "synthetic_fixture" and manifest["is_mock"]
    ledger = (
        (tmp_path / "test_access_ledger.jsonl").read_text(encoding="utf-8").strip().splitlines()
    )
    assert len(ledger) == 4
    cal = json.loads((tmp_path / "calibration.json").read_text(encoding="utf-8"))
    assert cal["overall"]["sufficient_sample"] is False


def test_demo_is_deterministic(cfg, tmp_path):
    a = run_demo(cfg, tmp_path / "a")
    b = run_demo(cfg, tmp_path / "b")
    assert a["ece"] == b["ece"] and a["splits"] == b["splits"]
    ra = (tmp_path / "a" / "evaluation_summary.json").read_text(encoding="utf-8")
    rb = (tmp_path / "b" / "evaluation_summary.json").read_text(encoding="utf-8")
    assert json.loads(ra)["groups"] == json.loads(rb)["groups"]


def test_validate_repository_script(repo_root):
    proc = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "validate_repository.py"), "--quiet"],
        capture_output=True,
        text=True,
        cwd=repo_root,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_build_pilot_manifest_reports_shortfall(repo_root):
    proc = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "build_pilot_manifest.py"),
            "--passages",
            str(repo_root / "data" / "fixtures" / "synthetic_passages.jsonl"),
            "--allow-synthetic",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert '"complete": false' in proc.stdout  # fixtures are not verified, so nothing is eligible
