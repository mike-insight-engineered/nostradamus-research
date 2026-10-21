"""Command-line interface: ``nr`` (alias ``nostradamus-research``).

Examples::

    nr info
    nr config validate
    nr sources validate
    nr sources audit --output reports/source-audit.md
    nr passages validate data/fixtures/synthetic_passages.jsonl --allow-synthetic
    nr corpus stats
    nr corpus split --dry-run
    nr translate mock --pipeline D --limit 2
    nr translate run --pipeline A --provider mock --dry-run
    nr demo
    nr report milestone --output reports/milestone-1-readiness.md

No command makes a paid API call unless ``--allow-paid-api`` is passed AND the
provider is enabled in ``config/providers.yaml`` AND its key is in the environment.
"""

from __future__ import annotations

import functools
import json
import logging
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import AppConfig, ConfigError, load_config, load_providers, providers_config_path
from .utils.paths import RepositoryNotFoundError

console = Console()
err = Console(stderr=True)

app = typer.Typer(help="Nostradamus Research — Milestone 1 historical translation calibration toolkit.",
                  no_args_is_help=True, add_completion=False)  # fmt: skip
config_app = typer.Typer(help="Configuration commands.", no_args_is_help=True)
sources_app = typer.Typer(help="Historical source registry.", no_args_is_help=True)
passages_app = typer.Typer(help="Passage records.", no_args_is_help=True)
corpus_app = typer.Typer(
    help="Corpus statistics, provenance, splits and leakage.", no_args_is_help=True
)
translate_app = typer.Typer(help="Run translation pipelines.", no_args_is_help=True)
review_app = typer.Typer(help="Blinded human review packages.", no_args_is_help=True)
evaluate_app = typer.Typer(help="Automated and human evaluation.", no_args_is_help=True)
calibrate_app = typer.Typer(help="Confidence calibration.", no_args_is_help=True)
report_app = typer.Typer(help="Generate reports.", no_args_is_help=True)
schemas_app = typer.Typer(help="JSON Schemas.", no_args_is_help=True)
for sub, name in [(config_app, "config"), (sources_app, "sources"), (passages_app, "passages"),
                  (corpus_app, "corpus"), (translate_app, "translate"), (review_app, "review"),
                  (evaluate_app, "evaluate"), (calibrate_app, "calibrate"), (report_app, "report"),
                  (schemas_app, "schemas")]:  # fmt: skip
    app.add_typer(sub, name=name)


def handled[F: Callable[..., Any]](fn: F) -> F:
    """Convert expected failures into a clear message and exit code 2."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        from .provenance.registry import RegistryError
        from .translation.providers.base import ProviderConfigurationError
        from .translation.runner import HeldOutAccessError

        try:
            return fn(*args, **kwargs)
        except (ConfigError, RepositoryNotFoundError, RegistryError, ProviderConfigurationError,
                HeldOutAccessError, FileNotFoundError, ValueError) as exc:  # fmt: skip
            err.print(f"[bold red]Error:[/] {exc}")
            raise typer.Exit(2) from None

    return wrapper  # type: ignore[return-value]


def _cfg() -> AppConfig:
    return load_config()


def _rel(cfg: AppConfig, p: Path) -> str:
    try:
        return str(p.resolve().relative_to(cfg.root))
    except ValueError:
        return str(p)


def _print_errors(errors: list[Any], limit: int = 50) -> None:
    for e in errors[:limit]:
        err.print(f"  [red]•[/] {e}")
    if len(errors) > limit:
        err.print(f"  … and {len(errors) - limit} more")


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Debug logging (secrets redacted)."
    ),
) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )


# ----------------------------------------------------------------------------- info
@app.command()
@handled
def info() -> None:
    """Show project information and current corpus/registry state."""
    from .corpus.io import load_passages
    from .provenance.registry import SourceRegistry

    cfg = _cfg()
    p = cfg.project.project
    console.print(
        f"[bold]{p.title}[/] — {p.milestone}: {p.milestone_title}  (package {__version__})"
    )
    for k, v in p.quality_dimensions.items():
        console.print(f"  {k}: {v}")
    reg, errors = SourceRegistry.load(cfg.path("source_registry"))
    console.print(f"Repository root: {cfg.root}")
    console.print(f"Source registry: {len(reg)} records {dict(reg.status_counts())}"
                  + (f" [red]{len(errors)} errors[/]" if errors else ""))  # fmt: skip
    ppath = cfg.path("passages")
    n = len(load_passages(ppath).records) if ppath.exists() else 0
    console.print(
        f"Research passages: {n} ({_rel(cfg, ppath)}{'' if ppath.exists() else ' — not yet created'})"
    )
    console.print(f"Providers config: {_rel(cfg, providers_config_path(cfg.root))}")
    console.print(
        "[dim]Synthetic fixtures live in data/fixtures/ and are never research evidence.[/]"
    )


# ---------------------------------------------------------------------------- config
@config_app.command("validate")
@handled
def config_validate() -> None:
    """Validate config/*.yaml and the provider configuration."""
    from .translation.prompts import PromptLibrary

    cfg = _cfg()
    providers = load_providers(cfg.root)
    lib = PromptLibrary.load()
    for tid, ver in cfg.translation.prompt_versions.items():
        lib.get(tid, ver)
    unknown = set(cfg.translation.pipelines) - {
        "A_direct",
        "B_two_stage",
        "C_retrieval",
        "D_structured",
    }
    if unknown:
        raise ConfigError(f"translation.yaml: unknown pipelines {sorted(unknown)}")
    if cfg.translation.default_provider not in providers.providers:
        raise ConfigError(
            f"default_provider {cfg.translation.default_provider!r} is not configured"
        )
    paid = [n for n, p in providers.providers.items() if p.type != "mock" and p.enabled]
    console.print("[green]Configuration valid.[/]")
    console.print(f"  prompt templates pinned: {len(cfg.translation.prompt_versions)}")
    console.print(
        f"  providers: {sorted(providers.providers)}; enabled paid providers: {paid or 'none'}"
    )


# --------------------------------------------------------------------------- sources
@sources_app.command("validate")
@handled
def sources_validate(
    path: Path | None = typer.Argument(None, help="Registry JSONL (default from config)."),
) -> None:
    """Validate source records, including the evidence required by each status."""
    from .provenance.registry import SourceRegistry

    cfg = _cfg()
    target = path or cfg.path("source_registry")
    reg, errors = SourceRegistry.load(target)
    if errors:
        err.print(f"[red]{len(errors)} problem(s) in {target}:[/]")
        _print_errors(errors)
        raise typer.Exit(1)
    console.print(f"[green]{len(reg)} source records valid[/] ({dict(reg.status_counts())})")


@sources_app.command("list")
@handled
def sources_list(path: Path | None = typer.Argument(None)) -> None:
    """List registered sources."""
    from .provenance.registry import SourceRegistry

    cfg = _cfg()
    reg, _ = SourceRegistry.load(path or cfg.path("source_registry"))
    t = Table("ID", "Type", "Title", "Status", "Rights")
    for s in reg:
        t.add_row(
            s.source_id,
            str(s.record_type),
            s.title[:60],
            str(s.verification_status),
            str(s.rights_status),
        )
    console.print(t)


@sources_app.command("register")
@handled
def sources_register(
    from_json: Path | None = typer.Option(None, help="JSON file with one full source record."),
    source_id: str | None = typer.Option(None, help="e.g. SRC-RABELAIS-PANT-1532"),
    record_type: str = typer.Option(
        "witness", help="witness | digital_repository | reference_work | text_corpus"
    ),
    title: str | None = typer.Option(None),
    author: str | None = typer.Option(None),
    date_text: str | None = typer.Option(None),
    stable_url: str | None = typer.Option(None),
    date_accessed: str | None = typer.Option(None, help="YYYY-MM-DD (required for 'located')"),
    status: str = typer.Option("candidate", help="candidate | located"),
    outstanding: list[str] = typer.Option([], help="Outstanding verification task (repeatable)."),
    notes: str | None = typer.Option(None),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without writing."),
) -> None:
    """Register a new historical source (as candidate or located)."""
    from .models.source import HistoricalSource
    from .provenance.registry import SourceRegistry

    cfg = _cfg()
    if from_json:
        data = json.loads(from_json.read_text(encoding="utf-8"))
    else:
        if not (source_id and title):
            raise ValueError("--source-id and --title are required (or use --from-json)")
        data = {"source_id": source_id, "record_type": record_type, "title": title, "author": author,
                "date_text": date_text, "stable_url": stable_url, "date_accessed": date_accessed,
                "verification_status": status, "outstanding_work": list(outstanding), "notes": notes}  # fmt: skip
    from pydantic import ValidationError

    from .utils.jsonl import format_validation_error

    try:
        source = HistoricalSource.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            "invalid source record:\n  " + "\n  ".join(format_validation_error(exc))
        ) from None
    path = cfg.path("source_registry")
    reg, errors = SourceRegistry.load(path)
    if errors:
        _print_errors(errors)
        raise ValueError("fix existing registry errors before registering new sources")
    reg.register(source)
    if dry_run:
        console.print(f"[yellow]Dry run:[/] {source.source_id} is valid and would be registered.")
        return
    reg.save()
    console.print(
        f"[green]Registered[/] {source.source_id} as {source.verification_status} in {_rel(cfg, path)}"
    )


@sources_app.command("promote")
@handled
def sources_promote(
    source_id: str = typer.Argument(...),
    to: str = typer.Option(..., "--to", help="Target status (one rung up, or any demotion)."),
    by: str = typer.Option(..., "--by", help="Name of the person making the change."),
    reason: str = typer.Option(..., help="Why the status changes."),
    evidence_json: Path | None = typer.Option(
        None, help="JSON list of VerificationEvidence objects."
    ),
    updates_json: Path | None = typer.Option(
        None, help="JSON object of field updates (e.g. catalogue_identifier)."
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Change a source's verification status, enforcing evidence requirements."""
    from .models.enums import VerificationStatus
    from .models.source import VerificationEvidence
    from .provenance.registry import SourceRegistry

    cfg = _cfg()
    path = cfg.path("source_registry")
    reg, errors = SourceRegistry.load(path)
    if errors:
        _print_errors(errors)
        raise ValueError("registry has errors")
    evidence = (
        [
            VerificationEvidence.model_validate(e)
            for e in json.loads(evidence_json.read_text(encoding="utf-8"))
        ]
        if evidence_json
        else []
    )
    updates = json.loads(updates_json.read_text(encoding="utf-8")) if updates_json else None
    updated = reg.promote(
        source_id,
        VerificationStatus(to),
        changed_by=by,
        reason=reason,
        evidence=evidence,
        updates=updates,
    )
    if dry_run:
        console.print(f"[yellow]Dry run:[/] {source_id} may move to {updated.verification_status}.")
        return
    reg.save()
    console.print(f"[green]{source_id}[/] is now {updated.verification_status}")


@sources_app.command("audit")
@handled
def sources_audit(
    output: Path | None = typer.Option(None, help="Write the Markdown audit report here."),
) -> None:
    """Audit the registry (and corpus, if present) and produce the Source Audit report."""
    from .corpus.io import load_passages
    from .provenance.audit import audit_corpus
    from .provenance.registry import SourceRegistry
    from .reporting.source_audit import render_source_audit

    cfg = _cfg()
    rpath = cfg.path("source_registry")
    reg, errors = SourceRegistry.load(rpath)
    if errors:
        _print_errors(errors)
        raise typer.Exit(1)
    ppath = cfg.path("passages")
    passages = load_passages(ppath).records if ppath.exists() else []
    audit = audit_corpus(
        reg, passages, forbid_synthetic=cfg.project.integrity.forbid_synthetic_in_corpus
    )
    text = render_source_audit(
        reg,
        audit,
        cfg.path("report_templates_dir") / "source-audit.md",
        registry_path=_rel(cfg, rpath),
    )
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        console.print(f"Wrote {output}")
    else:
        console.print(text)


@sources_app.command("export-csv")
@handled
def sources_export_csv(output: Path | None = typer.Option(None)) -> None:
    """Regenerate data/sources/source_candidates.csv from the registry."""
    from .provenance.registry import SourceRegistry

    cfg = _cfg()
    reg, errors = SourceRegistry.load(cfg.path("source_registry"))
    if errors:
        _print_errors(errors)
        raise typer.Exit(1)
    target = output or cfg.path("source_candidates")
    reg.export_csv(target)
    console.print(f"Wrote {len(reg)} rows to {_rel(cfg, target)}")


# -------------------------------------------------------------------------- passages
@passages_app.command("validate")
@handled
def passages_validate(
    path: Path | None = typer.Argument(None, help="Passages JSONL (default: research corpus)."),
    allow_synthetic: bool = typer.Option(False, help="Permit SYN- fixtures (tests/demos only)."),
) -> None:
    """Validate passage records (schema, transcription hash, category, status evidence)."""
    from .corpus.io import load_passages
    from .models.enums import DataOrigin

    cfg = _cfg()
    target = path or cfg.path("passages")
    if not target.exists():
        console.print(
            f"[yellow]{_rel(cfg, target)} does not exist yet — no research passages have been imported.[/]"
        )
        return
    result = load_passages(target)
    problems = [str(e) for e in result.errors]
    if not allow_synthetic:
        problems += [f"{p.passage_id}: synthetic fixture in research corpus" for p in result.records
                     if p.data_origin is DataOrigin.SYNTHETIC_FIXTURE]  # fmt: skip
    if problems:
        err.print(f"[red]{len(problems)} problem(s) in {target}:[/]")
        _print_errors(problems)
        raise typer.Exit(1)
    console.print(f"[green]{len(result.records)} passage records valid.[/]")


@passages_app.command("import")
@handled
def passages_import(
    input_path: Path = typer.Argument(
        ..., help="JSONL of passage records (may reference tei_file)."
    ),
    by: str = typer.Option(..., "--by", help="Name of the person importing."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate only; write nothing."),
) -> None:
    """Import passage records into the research corpus (locks diplomatic hashes)."""
    from .ingestion.importer import import_passages
    from .provenance.registry import SourceRegistry

    cfg = _cfg()
    reg, _ = SourceRegistry.load(cfg.path("source_registry"))
    outcome = import_passages(
        input_path, cfg.path("passages"), reg, imported_by=by, dry_run=dry_run
    )
    if not outcome.ok:
        err.print(f"[red]Import rejected ({len(outcome.errors)} problems); nothing written.[/]")
        _print_errors(outcome.errors)
        raise typer.Exit(1)
    verb = "would import" if dry_run else "imported"
    console.print(
        f"[green]{verb} {len(outcome.accepted)} passage(s)[/]"
        + (f" into {_rel(cfg, outcome.written_to)}" if outcome.written_to else "")
    )


# ---------------------------------------------------------------------------- corpus
def _load_corpus(cfg: AppConfig, path: Path | None, allow_synthetic: bool = False) -> list[Any]:
    from .corpus.io import load_passages

    target = path or cfg.path("passages")
    if not target.exists():
        raise FileNotFoundError(f"{_rel(cfg, target)} does not exist (no passages imported yet)")
    result = load_passages(target)
    if result.errors:
        _print_errors(result.errors)
        raise ValueError(f"{target} has invalid records")
    return result.records


@corpus_app.command("stats")
@handled
def corpus_stats(path: Path | None = typer.Argument(None)) -> None:
    """Corpus statistics and progress towards pilot (20) and full (80) targets."""
    from .corpus.stats import compute_stats

    cfg = _cfg()
    target = path or cfg.path("passages")
    passages = _load_corpus(cfg, path) if target.exists() else []
    st = compute_stats(passages, cfg.corpus)
    console.print(
        f"Passages: {st.n_passages} (eligible for calibration: {st.n_eligible}); works: {st.n_works}; authors: {st.n_authors}"
    )
    console.print(
        f"By status: {dict(st.by_status)}  By split: {dict(st.by_split)}  By origin: {dict(st.by_origin)}"
    )
    for label, rows in (("Pilot (20)", st.pilot_progress), ("Full corpus (80)", st.full_progress)):
        t = Table(title=label)
        for c in ("Group", "Eligible", "Target", "Total recorded", "Met"):
            t.add_column(c)
        for r in rows:
            t.add_row(
                r.label, str(r.eligible), str(r.target), str(r.total), "yes" if r.met else "no"
            )
        console.print(t)


@corpus_app.command("provenance")
@handled
def corpus_provenance(
    passages_path: Path | None = typer.Option(None, "--passages"),
    registry_path: Path | None = typer.Option(None, "--registry"),
    allow_synthetic: bool = typer.Option(False),
) -> None:
    """Cross-check passages against the source registry and rights policy."""
    from .provenance.audit import audit_corpus
    from .provenance.registry import SourceRegistry

    cfg = _cfg()
    reg, errors = SourceRegistry.load(registry_path or cfg.path("source_registry"))
    if errors:
        _print_errors(errors)
        raise typer.Exit(1)
    target = passages_path or cfg.path("passages")
    passages = _load_corpus(cfg, passages_path) if target.exists() else []
    audit = audit_corpus(reg, passages, forbid_synthetic=not allow_synthetic)
    for i in audit.issues:
        (err if i.severity == "error" else console).print(
            f"  [{'red' if i.severity == 'error' else 'yellow'}]{i.severity}[/] {i.record_id} {i.code}: {i.message}"
        )
    console.print(
        f"{audit.n_sources} sources, {audit.n_passages} passages: {len(audit.errors)} errors, {len(audit.warnings)} warnings"
    )
    if not audit.ok:
        raise typer.Exit(1)


@corpus_app.command("split")
@handled
def corpus_split(
    path: Path | None = typer.Argument(None),
    seed: int | None = typer.Option(None, help="Override the configured seed."),
    group_by: str | None = typer.Option(None, help="work_id | author"),
    apply: bool = typer.Option(
        False, help="Also write split assignments back into the passages file."
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Generate deterministic, group-isolated development/validation/test partitions."""
    from .corpus.io import dataset_version
    from .corpus.leakage import check_leakage
    from .corpus.splitting import apply_plan, plan_splits
    from .utils.jsonl import write_json, write_jsonl

    cfg = _cfg()
    passages = _load_corpus(cfg, path)
    sc = cfg.corpus.splits
    gb_raw = group_by or sc.group_by
    if gb_raw not in ("work_id", "author"):
        raise ValueError("--group-by must be work_id or author")
    gb: Literal["work_id", "author"] = "author" if gb_raw == "author" else "work_id"
    targets = {str(k): v for k, v in sc.targets.items()}
    plan = plan_splits(passages, targets, seed=seed if seed is not None else sc.seed, group_by=gb)
    plan.dataset_sha256 = dataset_version(passages)
    leak = check_leakage(passages, assignments=plan.assignments, group_by=gb,
                         near_duplicate_threshold=cfg.corpus.leakage.near_duplicate_threshold,
                         shingle_size=cfg.corpus.leakage.shingle_size)  # fmt: skip
    console.print(f"Achieved {plan.achieved} vs targets {plan.targets}")
    for w in plan.warnings:
        console.print(f"  [yellow]warning[/] {w}")
    for f in leak.findings:
        console.print(
            f"  [{'red' if f.severity == 'error' else 'yellow'}]{f.severity}[/] {f.code} {f.ids}: {f.detail}"
        )
    if dry_run:
        console.print("[yellow]Dry run: nothing written.[/]")
        return
    out = cfg.path("splits_dir") / f"split-seed{plan.seed}-{gb}.json"
    write_json(out, plan.to_dict())
    console.print(f"Wrote {_rel(cfg, out)}")
    if apply:
        target = path or cfg.path("passages")
        write_jsonl(target, apply_plan(passages, plan))
        console.print(f"Updated split field in {_rel(cfg, target)}")


@corpus_app.command("leakage")
@handled
def corpus_leakage(
    path: Path | None = typer.Argument(None),
    split_file: Path | None = typer.Option(
        None, help="Split plan JSON (default: passages' split field)."
    ),
    evidence: Path | None = typer.Option(
        None, help="Lexical evidence JSONL (default from config)."
    ),
) -> None:
    """Check duplicates, cross-partition sharing and retrieval/test overlap."""
    from .corpus.io import load_lexical_evidence
    from .corpus.leakage import check_leakage

    cfg = _cfg()
    passages = _load_corpus(cfg, path)
    assignments = (
        json.loads(split_file.read_text(encoding="utf-8"))["assignments"] if split_file else None
    )
    ev = load_lexical_evidence(evidence or cfg.path("lexical_evidence")).records
    rep = check_leakage(passages, assignments=assignments, evidence=ev, group_by=cfg.corpus.splits.group_by,
                        near_duplicate_threshold=cfg.corpus.leakage.near_duplicate_threshold,
                        shingle_size=cfg.corpus.leakage.shingle_size)  # fmt: skip
    for f in rep.findings:
        console.print(
            f"  [{'red' if f.severity == 'error' else 'yellow'}]{f.severity}[/] {f.code} {f.ids}: {f.detail}"
        )
    console.print(
        f"{len(rep.errors)} leakage errors, {len(rep.findings) - len(rep.errors)} warnings"
    )
    console.print(
        "[dim]Pretraining contamination cannot be detected by these checks (documented limitation).[/]"
    )
    if not rep.ok:
        raise typer.Exit(1)


# ------------------------------------------------------------------------- translate
def _parse_splits(values: list[str]) -> list[Any] | None:
    from .models.enums import DatasetSplit

    return [DatasetSplit(v) for v in values] if values else None


@translate_app.command("mock")
@handled
def translate_mock(
    pipeline: str = typer.Option("A", help="A | B | C | D (or full ID)."),
    passages_path: Path | None = typer.Option(
        None, "--passages", help="Default: synthetic fixtures."
    ),
    limit: int = typer.Option(3),
) -> None:
    """Run a pipeline with the deterministic mock provider and print outputs (writes nothing)."""
    from .corpus.io import load_lexical_evidence, load_passages
    from .linguistics.retrieval import LexicalEvidenceStore
    from .translation.pipelines import parse_pipeline_id
    from .translation.providers.mock import MockProvider
    from .translation.runner import build_pipeline, settings_from_config

    cfg = _cfg()
    pid = parse_pipeline_id(pipeline)
    fx = cfg.path("fixtures_dir")
    src = passages_path or fx / "synthetic_passages.jsonl"
    loaded = load_passages(src)
    if loaded.errors:
        _print_errors(loaded.errors)
        raise typer.Exit(1)
    store = LexicalEvidenceStore(
        load_lexical_evidence(fx / "synthetic_lexical_evidence.jsonl").records
    )
    settings = replace(settings_from_config(cfg, pid.value), allow_synthetic_evidence=True)
    pl = build_pipeline(pid.value, MockProvider(), settings, store)
    console.print("[yellow]MOCK provider output — placeholder text, not translation.[/]")
    for p in loaded.records[:limit]:
        r = pl.translate(p, "mock-preview")
        console.print(f"[bold]{p.passage_id}[/] ({p.category})\n  source: {p.diplomatic_transcription!r}\n"
                      f"  fr: {r.translation_fr!r}\n  en: {r.translation_en!r}\n"
                      f"  confidence: {r.stated_confidence} ({r.confidence_source}); retrieval: {r.retrieval_status}"
                      + (f"\n  limitations: {r.limitations}" if r.limitations else ""))  # fmt: skip


@translate_app.command("run")
@handled
def translate_run(
    pipeline: str = typer.Option(..., help="A | B | C | D (or full ID)."),
    provider: str | None = typer.Option(
        None, help="Provider name from providers config (default: translation.yaml)."
    ),
    passages_path: Path | None = typer.Option(None, "--passages", help="Default: research corpus."),
    split: list[str] = typer.Option(
        [], help="Restrict to split(s): development | validation | test."
    ),
    ids: list[str] = typer.Option([], "--id", help="Restrict to passage ID(s)."),
    limit: int | None = typer.Option(None),
    model: str | None = typer.Option(None, help="Override the configured model ID."),
    include_unverified: bool = typer.Option(
        False, help="Include passages below the inclusion status."
    ),
    allow_test_split: bool = typer.Option(False, help="Permit held-out test passages (logged)."),
    test_reason: str | None = typer.Option(
        None, help="Required reason when test passages are included."
    ),
    allow_paid_api: bool = typer.Option(
        False, "--allow-paid-api", help="Confirm that paid API calls may be made."
    ),
    allow_synthetic_evidence: bool = typer.Option(False, help="Allow SYN- evidence (demos only)."),
    description: str | None = typer.Option(None),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show the plan; make no calls and write nothing."
    ),
) -> None:
    """Run a translation pipeline over the corpus and persist results with a manifest."""
    from .corpus.io import dataset_version, load_passages
    from .linguistics.retrieval import LexicalEvidenceStore
    from .models.enums import VerificationStatus
    from .translation.pipelines import parse_pipeline_id
    from .translation.providers.factory import build_provider
    from .translation.runner import (
        build_pipeline,
        run_experiment,
        select_passages,
        settings_from_config,
    )

    cfg = _cfg()
    pid = parse_pipeline_id(pipeline)
    toggle = cfg.translation.pipelines.get(pid.value)
    if toggle is not None and not toggle.enabled:
        raise ValueError(f"pipeline {pid.value} is disabled in config/translation.yaml")
    src = passages_path or cfg.path("passages")
    if not src.exists():
        raise FileNotFoundError(
            f"{_rel(cfg, src)} does not exist; import verified passages first (or use `nr demo`)"
        )
    loaded = load_passages(src)
    if loaded.errors:
        _print_errors(loaded.errors)
        raise typer.Exit(1)
    if cfg.translation.held_out_requires_explicit_flag is False:
        allow_test_split = True
    selection = select_passages(
        loaded.records, splits=_parse_splits(split), passage_ids=ids or None, limit=limit,
        minimum_status=None if include_unverified else VerificationStatus(cfg.corpus.inclusion.minimum_passage_status),
        allow_test_split=allow_test_split, test_access_reason=test_reason,
    )  # fmt: skip
    pname = provider or cfg.translation.default_provider
    providers = load_providers(cfg.root)
    if dry_run and providers.providers.get(pname) and providers.providers[pname].type != "mock":
        prov_desc = {
            "provider": pname,
            "model": model or providers.providers[pname].model,
            "paid": True,
        }
        console.print(f"[yellow]Dry run — no provider constructed, no calls made.[/] {prov_desc}")
        console.print(f"  passages: {len(selection.passages)}; excluded: {len(selection.excluded)}")
        for k, v in list(selection.excluded.items())[:20]:
            console.print(f"    {k}: {v}")
        return
    prov = build_provider(pname, providers, allow_paid=allow_paid_api, model_override=model)
    settings = settings_from_config(cfg, pid.value)
    if allow_synthetic_evidence:
        settings = replace(settings, allow_synthetic_evidence=True)
    epath = cfg.path("lexical_evidence")
    store = LexicalEvidenceStore.from_file(epath) if epath.exists() else LexicalEvidenceStore([])
    pl = build_pipeline(pid.value, prov, settings, store)
    out = run_experiment(cfg, pl, selection, dataset_path=src, dataset_sha256=dataset_version(loaded.records),
                         runs_dir=cfg.path("runs_dir"), dry_run=dry_run, description=description,
                         test_access_reason=test_reason, ledger_path=cfg.path("test_access_ledger"))  # fmt: skip
    if dry_run:
        console.print("[yellow]Dry run — no calls made, nothing written.[/]")
        console.print_json(json.dumps(out.plan, default=str))
        return
    m = out.manifest
    console.print(f"[green]Run {m.run_id}[/] {m.status}: {m.n_results} results, {m.n_failed} failed; "
                  f"cost: {m.total_cost_usd if m.total_cost_usd is not None else m.cost_note}")  # fmt: skip
    console.print(f"  results: {_rel(cfg, out.run_dir / 'results.jsonl') if out.run_dir else '-'}")
    if m.test_split_accessed:
        console.print(
            "[yellow]  Held-out test passages were translated; access recorded in the ledger.[/]"
        )


# ---------------------------------------------------------------------------- review
def _load_runs(run_dirs: list[Path]) -> tuple[list[Any], list[Any]]:
    from .models.experiment import ExperimentManifest
    from .models.translation import TranslationResult
    from .utils.jsonl import load_models

    manifests, results = [], []
    for d in run_dirs:
        mpath = d / "manifest.json"
        if not mpath.is_file():
            raise FileNotFoundError(f"{d} has no manifest.json")
        manifests.append(
            ExperimentManifest.model_validate(json.loads(mpath.read_text(encoding="utf-8")))
        )
        lr = load_models(d / "results.jsonl", TranslationResult, "result_id")
        if lr.errors:
            _print_errors(lr.errors)
            raise ValueError(f"invalid results in {d}")
        results.extend(lr.records)
    return manifests, results


def _passages_for(cfg: AppConfig, manifests: list[Any], override: Path | None) -> dict[str, Any]:
    from .corpus.io import load_passages

    paths = {override} if override else {Path(m.dataset_path) for m in manifests}
    out: dict[str, Any] = {}
    for p in paths:
        path = p if p.is_absolute() else cfg.root / p
        for rec in load_passages(path).records:
            out[rec.passage_id] = rec
    return out


@review_app.command("export")
@handled
def review_export(
    run: list[Path] = typer.Option(..., "--run", help="Run directory (repeatable)."),
    package_id: str = typer.Option(..., help="e.g. PKG-2026-001"),
    output: Path | None = typer.Option(None, help="Default: data/annotations/review_packages/"),
    passages_path: Path | None = typer.Option(None, "--passages"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Export a blinded human-review package (CSV + JSONL) with a separate unblinding key."""
    from .evaluation.review_package import build_review_package, write_review_package
    from .provenance.registry import SourceRegistry

    cfg = _cfg()
    manifests, results = _load_runs(run)
    passages = _passages_for(cfg, manifests, passages_path)
    reg, _ = SourceRegistry.load(cfg.path("source_registry"))
    pkg = build_review_package(
        results, passages, reg, package_id=package_id, seed=cfg.evaluation.review.blinding_seed
    )
    if dry_run:
        console.print(
            f"[yellow]Dry run:[/] {len(pkg.items)} items would be exported ({len(pkg.skipped)} failed results skipped)."
        )
        return
    out_dir = output or cfg.root / "data" / "annotations" / "review_packages"
    write_review_package(
        pkg, out_dir, instructions_template=cfg.path("report_templates_dir") / "human-review.md"
    )
    console.print(f"[green]Exported {len(pkg.items)} items[/] to {pkg.package_dir}")
    console.print(f"[yellow]Unblinding key:[/] {pkg.key_path} — do NOT send to reviewers.")


@review_app.command("import")
@handled
def review_import(
    reviews: Path = typer.Argument(..., help="Completed review_sheet.csv or reviews .jsonl"),
    key: Path = typer.Option(..., help="Package key.json"),
    output: Path | None = typer.Option(
        None, help="Default: data/annotations/reviews/<package>.jsonl"
    ),
    allow_synthetic: bool = typer.Option(False, help="Accept SYNTHETIC reviewers (demos only)."),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Validate completed reviews, link them to results via the key, and store them."""
    from .evaluation.review_package import import_reviews, write_linked_reviews

    cfg = _cfg()
    res = import_reviews(reviews, key, allow_synthetic=allow_synthetic)
    if not res.ok:
        err.print(f"[red]{len(res.errors)} problem(s); nothing written.[/]")
        _print_errors(res.errors)
        raise typer.Exit(1)
    console.print(f"{len(res.reviews)} valid reviews; {res.blank_rows} unreviewed rows skipped")
    if dry_run or not res.reviews:
        return
    pkg = json.loads(key.read_text(encoding="utf-8"))["package_id"]
    target = output or cfg.root / "data" / "annotations" / "reviews" / f"{pkg}.jsonl"
    write_linked_reviews(target, res.reviews)
    console.print(f"[green]Wrote[/] {_rel(cfg, target)}")


@review_app.command("agreement")
@handled
def review_agreement(
    linked: Path = typer.Argument(..., help="Linked reviews JSONL from `review import`."),
) -> None:
    """Inter-reviewer agreement (percent agreement, Cohen's kappa, penalty correlation)."""
    from .evaluation.agreement import reviewer_agreement
    from .evaluation.review_package import read_linked_reviews
    from .models.enums import TargetLanguage

    cfg = _cfg()
    revs = [lr.review for lr in read_linked_reviews(linked)]
    for lang in TargetLanguage:
        a = reviewer_agreement(revs, lang, weights=cfg.evaluation.mqm.severity_weights,
                               min_items=cfg.evaluation.agreement.min_items_for_estimate)  # fmt: skip
        console.print(f"[bold]{lang}[/]: items={a.n_items_multi_reviewed} pairs={a.n_reviewer_pairs} "
                      f"agreement={a.percent_agreement} kappa={a.mean_cohen_kappa} spearman={a.penalty_spearman}")  # fmt: skip
        for n in a.notes:
            console.print(f"  [yellow]{n}[/]")


# -------------------------------------------------------------------------- evaluate
def _linked(paths: list[Path]) -> list[Any]:
    from .evaluation.review_package import read_linked_reviews

    return [lr for p in paths for lr in read_linked_reviews(p)]


@evaluate_app.command("metrics")
@handled
def evaluate_metrics(
    run: list[Path] = typer.Option(..., "--run"),
    reviews: list[Path] = typer.Option([], "--reviews", help="Linked reviews JSONL (repeatable)."),
    passages_path: Path | None = typer.Option(None, "--passages"),
    output: Path | None = typer.Option(
        None, help="Directory for evaluation.jsonl and summary.json."
    ),
) -> None:
    """Compute chrF/chrF++ (and MQM aggregates if reviews are given) with uncertainty."""
    from .evaluation.evaluate import evaluate_results, summarise
    from .reporting.common import evidence_banner, fmt_est
    from .utils.jsonl import write_json, write_jsonl

    cfg = _cfg()
    manifests, results = _load_runs(run)
    passages = _passages_for(cfg, manifests, passages_path)
    evals = evaluate_results(results, passages, _linked(reviews), cfg.evaluation)
    summary = summarise(evals, cfg.evaluation.statistics)
    console.print(evidence_banner(e.evidence_level for e in evals))
    t = Table("Pipeline", "Lang", "n", "chrF (95% CI)", "Acceptable (95% CI)", "MQM penalty")
    for g in summary["groups"]:
        t.add_row(g["pipeline"], g["target_language"], str(g["n_outputs"]), fmt_est(g["chrf"]),
                  fmt_est(g["acceptance_rate"], 2), fmt_est(g["mqm_penalty"]))  # fmt: skip
    console.print(t)
    if output:
        write_jsonl(output / "evaluation.jsonl", evals)
        write_json(output / "summary.json", summary)
        console.print(f"Wrote {output}")


# ------------------------------------------------------------------------- calibrate
@calibrate_app.command("report")
@handled
def calibrate_report(
    run: list[Path] = typer.Option(..., "--run"),
    reviews: list[Path] = typer.Option(..., "--reviews"),
    passages_path: Path | None = typer.Option(None, "--passages"),
    output: Path | None = typer.Option(None, help="Markdown report path (default: print)."),
) -> None:
    """Calibration of stated confidence against reviewed correctness."""
    from .calibration.analysis import analyse
    from .calibration.dataset import build_items, group_reviews
    from .reporting.calibration_report import render_calibration

    cfg = _cfg()
    manifests, results = _load_runs(run)
    passages = _passages_for(cfg, manifests, passages_path)
    linked = _linked(reviews)
    items = build_items(results, group_reviews(linked), passages, cfg.evaluation.correctness)
    cl = cfg.evaluation.statistics.confidence_level
    overall = analyse(items, cfg.evaluation.calibration, cl)
    per = {str(m.pipeline): analyse([i for i in items if i.pipeline is m.pipeline], cfg.evaluation.calibration, cl)
           for m in manifests}  # fmt: skip
    text = render_calibration(overall, per, cfg.path("report_templates_dir") / "calibration-report.md",
                              inputs=[str(r) for r in [*run, *reviews]])  # fmt: skip
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        console.print(f"Wrote {output}")
    else:
        console.print(text)


# ---------------------------------------------------------------------------- report
@report_app.command("benchmark")
@handled
def report_benchmark(
    run: list[Path] = typer.Option(..., "--run"),
    reviews: list[Path] = typer.Option([], "--reviews"),
    passages_path: Path | None = typer.Option(None, "--passages"),
    output: Path | None = typer.Option(None),
) -> None:
    """Translation Benchmark report from recorded runs (and reviews, if any)."""
    from .evaluation.evaluate import evaluate_results, summarise
    from .reporting.benchmark import render_benchmark

    cfg = _cfg()
    manifests, results = _load_runs(run)
    passages = _passages_for(cfg, manifests, passages_path)
    evals = evaluate_results(results, passages, _linked(reviews), cfg.evaluation)
    text = render_benchmark(manifests, evals, summarise(evals, cfg.evaluation.statistics), passages,
                            cfg.path("report_templates_dir") / "benchmark-report.md")  # fmt: skip
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        console.print(f"Wrote {output}")
    else:
        console.print(text)


@report_app.command("milestone")
@handled
def report_milestone(
    output: Path | None = typer.Option(None, help="e.g. reports/milestone-1-readiness.md"),
) -> None:
    """Milestone gate / readiness report from current repository state."""
    from .reporting.milestone_gate import evaluate_gate, render_gate
    from .schemas import stale_schemas

    cfg = _cfg()
    gate = evaluate_gate(cfg, schemas_current=not stale_schemas(cfg.path("schemas_dir")))
    text = render_gate(gate, cfg, cfg.path("report_templates_dir") / "milestone-gate.md")
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        console.print(f"Wrote {output} - recommendation: {gate.recommendation.upper()}")
    else:
        console.print(text)


# --------------------------------------------------------------------------- schemas
@schemas_app.command("generate")
@handled
def schemas_generate() -> None:
    """Regenerate schemas/*.schema.json from the Pydantic models."""
    from .schemas import generate_schemas

    cfg = _cfg()
    for p in generate_schemas(cfg.path("schemas_dir")):
        console.print(f"wrote {_rel(cfg, p)}")


@schemas_app.command("check")
@handled
def schemas_check() -> None:
    """Fail if committed schemas differ from the models."""
    from .schemas import stale_schemas

    cfg = _cfg()
    stale = stale_schemas(cfg.path("schemas_dir"))
    if stale:
        err.print(f"[red]Stale schemas:[/] {stale} — run `nr schemas generate`")
        raise typer.Exit(1)
    console.print("[green]Schemas are up to date.[/]")


# ------------------------------------------------------------------------------ demo
@app.command()
@handled
def demo(
    output_dir: Path | None = typer.Option(
        None, help="Default: experiments/runs/demo (git-ignored)."
    ),
) -> None:
    """Run the complete OFFLINE demonstration on synthetic fixtures (mock provider, zero cost)."""
    from .demo import run_demo

    cfg = _cfg()
    out = output_dir or cfg.path("runs_dir") / "demo"
    console.print(
        "[yellow]Running SYNTHETIC offline demonstration — outputs are not research evidence.[/]"
    )
    summary = run_demo(cfg, out)
    console.print_json(json.dumps(summary, default=str))


@app.command("version")
def version_cmd() -> None:
    """Print the package version."""
    console.print(__version__)


if __name__ == "__main__":  # pragma: no cover
    app()
