#!/usr/bin/env python
"""Validate repository structure, research-integrity invariants and artifact freshness.

Checks:
  * required files and directories exist;
  * configuration, source registry, fixtures and backlog validate;
  * committed JSON Schemas match the Pydantic models;
  * the research corpus (if present) contains no synthetic records;
  * no secrets or local provider/env files are tracked by Git.

Usage:  uv run python scripts/validate_repository.py [--quiet]
Exit code 0 = all checks passed, 1 = at least one failure.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nostradamus_research.config import ConfigError, load_config, load_providers  # noqa: E402
from nostradamus_research.corpus.io import load_lexical_evidence, load_passages  # noqa: E402
from nostradamus_research.models.enums import DataOrigin  # noqa: E402
from nostradamus_research.provenance.registry import SourceRegistry  # noqa: E402
from nostradamus_research.reporting.backlog import load_backlog  # noqa: E402
from nostradamus_research.schemas import stale_schemas  # noqa: E402
from nostradamus_research.translation.prompts import PromptLibrary  # noqa: E402
from nostradamus_research.utils.redaction import contains_secret  # noqa: E402

REQUIRED = [
    "README.md", "CLAUDE.md", "LICENSE", ".gitignore", ".env.example", ".python-version", "pyproject.toml",
    "uv.lock", "Makefile",
    ".github/workflows/ci.yml", ".github/ISSUE_TEMPLATE/research_task.yml",
    ".github/ISSUE_TEMPLATE/source_verification.yml", ".github/pull_request_template.md",
    ".claude/README.md", ".claude/agents", ".claude/skills",
    "docs/project-charter.md", "docs/research-methodology.md", "docs/milestone-1-execution-plan.md",
    "docs/architecture.md", "docs/data-dictionary.md", "docs/source-authentication.md",
    "docs/transcription-policy.md", "docs/translation-protocol.md", "docs/calibration-methodology.md",
    "docs/evaluation-framework.md", "docs/human-review-guidelines.md", "docs/confidence-calibration.md",
    "docs/reproducibility.md", "docs/risk-register.md", "docs/decisions", "docs/project/backlog.md",
    "docs/project/backlog.yaml", "docs/project/milestones.md", "docs/project/progress-log.md",
    "config/project.yaml", "config/corpus.yaml", "config/translation.yaml", "config/evaluation.yaml",
    "config/providers.example.yaml",
    "data/README.md", "data/sources/source_registry.jsonl", "data/sources/source_candidates.csv",
    "data/raw/README.md", "data/transcriptions/README.md", "data/reference_translations/README.md",
    "data/processed/README.md", "data/splits/README.md", "data/annotations/README.md", "data/fixtures",
    "schemas/historical_source.schema.json", "schemas/passage.schema.json",
    "schemas/reference_translation.schema.json", "schemas/translation_result.schema.json",
    "schemas/human_review.schema.json", "schemas/evaluation_result.schema.json",
    "schemas/experiment_manifest.schema.json",
    "scripts/bootstrap.py", "scripts/validate_repository.py", "scripts/generate_schemas.py",
    "scripts/build_pilot_manifest.py", "scripts/export_review_package.py", "scripts/run_benchmark.py",
    "scripts/generate_calibration_report.py",
    "experiments/README.md", "experiments/baseline", "experiments/two_stage", "experiments/rag",
    "experiments/linguistic_analysis", "experiments/runs/README.md",
    "reports/README.md", "reports/templates/calibration-report.md", "reports/templates/source-audit.md",
    "reports/templates/human-review.md", "reports/templates/milestone-gate.md",
    "reports/templates/benchmark-report.md",
    "research/bibliography.md", "research/source-acquisition-plan.md",
    "research/historical-language-resources.md", "research/candidate-authors.md",
    "research/research-questions.md", "research/open-issues.md",
    "tests/conftest.py", "tests/unit", "tests/integration", "tests/fixtures",
]  # fmt: skip
FORBIDDEN_TRACKED = {".env", "config/providers.yaml"}
SECRET_SCAN_SUFFIXES = {
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".jsonl",
    ".toml",
    ".txt",
    ".csv",
    ".cfg",
    ".env",
}


def tracked_files() -> list[str] | None:
    """Tracked files plus untracked files that are not git-ignored (i.e. would be committed)."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=30,
        )  # fmt: skip
    except (OSError, subprocess.SubprocessError):
        return None
    return sorted({line for line in out.stdout.splitlines() if line})


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv
    failures: list[str] = []
    passes: list[str] = []

    def check(ok: bool, label: str, detail: str = "") -> None:
        (passes if ok else failures).append(f"{label}{': ' + detail if detail else ''}")

    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    check(
        not missing,
        "required paths",
        f"missing {missing}" if missing else f"{len(REQUIRED)} present",
    )

    try:
        cfg = load_config(ROOT)
        load_providers(ROOT, ROOT / "config" / "providers.example.yaml")
        check(True, "configuration")
    except ConfigError as exc:
        check(False, "configuration", str(exc))
        return report(passes, failures, quiet)

    try:
        lib = PromptLibrary.load()
        for tid, ver in cfg.translation.prompt_versions.items():
            lib.get(tid, ver)
        check(True, "prompt templates", f"{len(lib.templates)} pinned and loadable")
    except ValueError as exc:
        check(False, "prompt templates", str(exc))

    stale = stale_schemas(cfg.path("schemas_dir"))
    check(
        not stale,
        "schemas up to date",
        f"stale: {stale} (run `nr schemas generate`)" if stale else "",
    )

    reg, errs = SourceRegistry.load(cfg.path("source_registry"))
    check(
        not errs,
        "source registry",
        f"{len(reg)} records" if not errs else "; ".join(map(str, errs[:5])),
    )
    syn = [s.source_id for s in reg if s.data_origin is DataOrigin.SYNTHETIC_FIXTURE]
    check(not syn, "no synthetic sources in registry", ", ".join(syn))

    ppath = cfg.path("passages")
    if ppath.exists():
        res = load_passages(ppath)
        check(res.ok, "research passages valid", "; ".join(map(str, res.errors[:5])))
        syn_p = [p.passage_id for p in res.records if p.data_origin is DataOrigin.SYNTHETIC_FIXTURE]
        check(not syn_p, "no synthetic passages in corpus", ", ".join(syn_p))
    else:
        check(True, "research passages", "none imported yet")

    ev = load_lexical_evidence(cfg.path("lexical_evidence"))
    syn_e = [e.evidence_id for e in ev.records if e.data_origin is DataOrigin.SYNTHETIC_FIXTURE]
    check(
        ev.ok and not syn_e,
        "lexical evidence store",
        f"{len(ev.records)} entries; synthetic: {syn_e}",
    )

    fx = cfg.path("fixtures_dir")
    fr = load_passages(fx / "synthetic_passages.jsonl")
    _, ferr = SourceRegistry.load(fx / "synthetic_sources.jsonl")
    nonsyn = [p.passage_id for p in fr.records if p.data_origin is not DataOrigin.SYNTHETIC_FIXTURE]
    check(
        fr.ok and not ferr and not nonsyn,
        "synthetic fixtures valid and labelled",
        f"{len(fr.records)} passages",
    )

    try:
        bl = load_backlog(cfg.path("backlog"))
        md = (ROOT / "docs" / "project" / "backlog.md").read_text(encoding="utf-8")
        absent = [i.id for i in bl.items if i.id not in md]
        check(
            not absent,
            "backlog",
            f"{len(bl.items)} items" + (f"; missing from backlog.md: {absent}" if absent else ""),
        )
    except Exception as exc:
        check(False, "backlog", str(exc))

    files = tracked_files()
    if files is None:
        check(True, "git checks", "git unavailable; skipped")
    else:
        bad = sorted(FORBIDDEN_TRACKED & set(files))
        check(not bad, "no local secrets files tracked", ", ".join(bad))
        leaked = []
        for f in files:
            p = ROOT / f
            if (
                p.suffix in SECRET_SCAN_SUFFIXES
                and p.is_file()
                and p.stat().st_size < 2_000_000
                and contains_secret(p.read_text(encoding="utf-8", errors="ignore"))
            ):
                leaked.append(f)
        check(not leaked, "no API-key-like strings in tracked files", ", ".join(leaked))
    return report(passes, failures, quiet)


def report(passes: list[str], failures: list[str], quiet: bool) -> int:
    if not quiet:
        for p in passes:
            print(f"PASS  {p}")
    for f in failures:
        print(f"FAIL  {f}")
    print(f"\n{len(passes)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
