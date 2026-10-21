"""CLI commands (offline). Commands that would write are run with --dry-run or into tmp_path."""

import json

import pytest
from typer.testing import CliRunner

from nostradamus_research.cli import app
from tests.conftest import FIXTURES

pytestmark = pytest.mark.integration
runner = CliRunner()
FIX = str(FIXTURES / "synthetic_passages.jsonl")


def run(*args):
    return runner.invoke(app, list(args), catch_exceptions=False)


def test_help_lists_command_groups():
    r = run("--help")
    assert r.exit_code == 0
    for group in (
        "sources",
        "passages",
        "corpus",
        "translate",
        "review",
        "evaluate",
        "calibrate",
        "report",
        "demo",
    ):
        assert group in r.output


def test_info_and_config_validate():
    r = run("info")
    assert r.exit_code == 0 and "M1" in r.output
    r = run("config", "validate")
    # The paid-provider count depends on a developer's local config/providers.yaml, so only
    # validity is asserted here; test_config.py checks that the committed example disables them.
    assert r.exit_code == 0 and "Configuration valid" in r.output


def test_sources_validate_and_list():
    assert run("sources", "validate").exit_code == 0
    r = run("sources", "list")
    assert r.exit_code == 0 and "RES-GALLICA" in r.output


def test_sources_register_dry_run_and_errors():
    r = run(
        "sources", "register", "--source-id", "SRC-NEW-TEST", "--title", "A witness", "--dry-run"
    )
    assert r.exit_code == 0 and "Dry run" in r.output
    r = run(
        "sources",
        "register",
        "--source-id",
        "SRC-NEW-TEST",
        "--title",
        "A witness",
        "--status",
        "located",
        "--dry-run",
    )
    assert r.exit_code == 2 and "located" in r.output
    r = run("sources", "register", "--source-id", "RES-GALLICA", "--title", "dup", "--dry-run")
    assert r.exit_code == 2 and "duplicate" in r.output


def test_sources_audit_to_file(tmp_path):
    out = tmp_path / "audit.md"
    r = run("sources", "audit", "--output", str(out))
    assert r.exit_code == 0
    text = out.read_text(encoding="utf-8")
    assert "NO SOURCE HAS BEEN AUTHENTICATED" in text and "Outstanding concerns" in text


def test_passages_validate():
    assert run("passages", "validate", FIX, "--allow-synthetic").exit_code == 0
    r = run("passages", "validate", FIX)
    assert r.exit_code == 1 and "synthetic fixture in research corpus" in r.output
    r = run(
        "passages",
        "validate",
        str(FIXTURES.parents[1] / "tests" / "fixtures" / "invalid_passages.jsonl"),
    )
    assert r.exit_code == 1 and "invalid JSON" in r.output


def test_passages_import_refuses_synthetic(tmp_path):
    r = run("passages", "import", FIX, "--by", "Tester", "--dry-run")
    assert r.exit_code == 1 and "synthetic" in r.output


def test_corpus_stats_split_leakage_provenance():
    r = run("corpus", "stats", FIX)
    assert r.exit_code == 0 and "Pilot (20)" in r.output
    r = run("corpus", "split", FIX, "--dry-run")
    assert r.exit_code == 0 and "Achieved" in r.output and "Dry run" in r.output
    assert run("corpus", "leakage", FIX).exit_code == 0
    r = run(
        "corpus",
        "provenance",
        "--passages",
        FIX,
        "--registry",
        str(FIXTURES / "synthetic_sources.jsonl"),
        "--allow-synthetic",
    )
    assert r.exit_code == 0


def test_translate_mock_preview():
    for p in ("A", "B", "C", "D"):
        r = run("translate", "mock", "--pipeline", p, "--limit", "1")
        assert r.exit_code == 0 and "MOCK" in r.output


def test_translate_run_dry_run_and_test_split_guard():
    r = run(
        "translate",
        "run",
        "--pipeline",
        "A",
        "--provider",
        "mock",
        "--passages",
        FIX,
        "--include-unverified",
        "--dry-run",
    )
    assert r.exit_code == 0 and "estimated_provider_calls" in r.output
    r = run(
        "translate", "run", "--pipeline", "A", "--provider", "mock", "--passages", FIX, "--dry-run"
    )
    assert (
        r.exit_code == 0 and '"n_passages": 0' in r.output
    )  # fixtures are below the inclusion status


def test_translate_run_paid_provider_refused():
    r = run(
        "translate",
        "run",
        "--pipeline",
        "A",
        "--provider",
        "anthropic",
        "--passages",
        FIX,
        "--include-unverified",
    )
    assert r.exit_code == 2 and "disabled" in r.output
    r = run(
        "translate",
        "run",
        "--pipeline",
        "A",
        "--provider",
        "anthropic",
        "--passages",
        FIX,
        "--include-unverified",
        "--dry-run",
    )
    assert r.exit_code == 0 and "no calls made" in r.output


def test_schemas_check_and_milestone_report(tmp_path):
    assert run("schemas", "check").exit_code == 0
    out = tmp_path / "gate.md"
    r = run("report", "milestone", "--output", str(out))
    assert r.exit_code == 0 and "DEFER" in r.output
    assert "Acceptance criteria" in out.read_text(encoding="utf-8")


def test_end_to_end_cli_workflow(tmp_path):
    demo_dir = tmp_path / "demo"
    r = run("demo", "--output-dir", str(demo_dir))
    assert r.exit_code == 0
    runs = [str(demo_dir / "runs" / f"demo-{p}") for p in ("A_direct", "B_two_stage")]
    passages = str(demo_dir / "passages_with_splits.jsonl")
    run_args = [x for rd in runs for x in ("--run", rd)]
    # review export -> (synthetic) import -> agreement -> metrics -> calibration -> benchmark
    r = run(
        "review",
        "export",
        *run_args,
        "--package-id",
        "PKG-CLI",
        "--output",
        str(tmp_path / "pkgs"),
        "--passages",
        passages,
    )
    assert r.exit_code == 0
    key = tmp_path / "pkgs" / "PKG-CLI-KEY" / "key.json"
    linked = tmp_path / "linked.jsonl"
    r = run(
        "review",
        "import",
        str(demo_dir / "review" / "synthetic_reviews.jsonl"),
        "--key",
        str(demo_dir / "review" / "DEMO-PKG-001-KEY" / "key.json"),
        "--output",
        str(linked),
        "--allow-synthetic",
    )
    assert r.exit_code == 0 and linked.exists() and key.exists()
    assert run("review", "agreement", str(linked)).exit_code == 0
    r = run(
        "evaluate",
        "metrics",
        *run_args,
        "--reviews",
        str(linked),
        "--passages",
        passages,
        "--output",
        str(tmp_path / "eval"),
    )
    assert r.exit_code == 0 and "SYNTHETIC" in r.output
    assert (
        json.loads((tmp_path / "eval" / "summary.json").read_text(encoding="utf-8"))[
            "n_evaluations"
        ]
        == 48
    )
    r = run(
        "calibrate",
        "report",
        *run_args,
        "--reviews",
        str(linked),
        "--passages",
        passages,
        "--output",
        str(tmp_path / "cal.md"),
    )
    assert r.exit_code == 0 and "SYNTHETIC" in (tmp_path / "cal.md").read_text(encoding="utf-8")
    r = run(
        "report",
        "benchmark",
        *run_args,
        "--reviews",
        str(linked),
        "--passages",
        passages,
        "--output",
        str(tmp_path / "bench.md"),
    )
    assert r.exit_code == 0 and "Staging analysis" in (tmp_path / "bench.md").read_text(
        encoding="utf-8"
    )


def test_missing_run_dir_gives_clear_error(tmp_path):
    r = run("evaluate", "metrics", "--run", str(tmp_path / "nope"))
    assert r.exit_code == 2 and "manifest.json" in r.output
