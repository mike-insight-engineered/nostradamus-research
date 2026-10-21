#!/usr/bin/env python
"""Build human transcription-verification materials (QC1) from the pilot manifest.

Outputs:
  research/pilot/transcription-review/<slot>.md   one summary sheet per slot
  research/pilot/review-packets/<slot>/           full packet for each slot that has a draft
      README.md (instructions + metadata + draft + uncertainties), transcription_lines.txt,
      corrections.csv, signoff.md

Material containing a transcription derived from a facsimile whose reuse terms are not
cleared (source rights_status not committable) is written with ".pending-rights" in its
path. Such paths are git-ignored (DATA_LICENSE.md §3). Packets never contain machine
translations.

Usage:
    uv run python scripts/build_transcription_review_packets.py [--dry-run]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nostradamus_research.corpus.io import load_passages  # noqa: E402
from nostradamus_research.models.passage import Passage  # noqa: E402
from nostradamus_research.models.source import HistoricalSource  # noqa: E402
from nostradamus_research.provenance.registry import SourceRegistry  # noqa: E402

MANIFEST = ROOT / "data" / "candidates" / "pilot_candidates.jsonl"
DRAFT_DIR = ROOT / "data" / "transcriptions" / "drafts"
SHEETS = ROOT / "research" / "pilot" / "transcription-review"
PACKETS = ROOT / "research" / "pilot" / "review-packets"
RESOURCES = ["RES-HUGUET", "RES-DMF-ATILF", "RES-COTGRAVE-1611", "RES-ESTIENNE-1549", "RES-NICOT-1606",
             "RES-GODEFROY", "RES-DU-CANGE", "RES-PERSEUS"]  # fmt: skip
PROTOCOL = "docs/transcription-verification-protocol.md"


def load_drafts() -> dict[str, Passage]:
    drafts: dict[str, Passage] = {}
    for path in sorted(DRAFT_DIR.glob("*.jsonl")):
        result = load_passages(path)
        if result.errors:
            raise SystemExit("draft errors:\n  " + "\n  ".join(map(str, result.errors)))
        drafts.update({p.passage_id: p for p in result.records})
    return drafts


def witness_block(src: HistoricalSource) -> list[str]:
    return [
        f"- Registry ID: `{src.source_id}` (status `{src.verification_status}`)",
        f"- Author / title: {src.author or '—'} — *{src.title}*",
        f"- Imprint: {src.place_of_publication or '—'} : {src.printer_publisher or '—'}, {src.date_text or '—'}",
        f"- Edition / collation: {src.edition or '—'}",
        f"- Holding institution / copy: {src.holding_institution or '—'}",
        f"- Catalogue: {src.catalogue_identifier or '—'}",
        f"- Facsimile used for the draft (derivative): {src.stable_url or '—'}",
        f"- Original digitisation (use this to verify): {src.persistent_identifier or '—'}",
        f"- Image/quality notes: {src.uncertainty_notes or '—'}",
        f"- Rights (`{src.rights_status}`): see `research/pilot/rights-provenance-matrix.md`",
    ]


def sheet(slot: dict, src: HistoricalSource, draft: Passage | None, reg: SourceRegistry) -> str:
    lines = [
        f"# Transcription verification sheet — {slot['slot_id']} ({slot['pilot_group']})",
        "",
        "> QC1 check against the facsimile. **No machine translation is included.** Do not use AI tools.",
        f"> Protocol: `{PROTOCOL}`.",
        "",
        "## Witness",
        "",
        *witness_block(src),
        "",
        "## Passage",
        "",
        f"- Locator: {slot['locator']}",
        f"- Passage: {slot['passage']}",
        f"- Audit flags: {', '.join(slot.get('audit_flags', [])) or 'none'}",
        f"- Blockers: {'; '.join(slot['blockers']) or 'none recorded'}",
        "",
    ]
    if draft is None:
        lines += [
            "## Transcription",
            "",
            "*No draft.* Transcribe directly from the original digitisation.",
            "",
        ]
    else:
        lines += [
            "## Draft",
            "",
            f"`{draft.passage_id}` — {draft.transcribed_by}",
            "",
            "```text",
            draft.diplomatic_transcription,
            "```",
            "",
            f"Full packet: `research/pilot/review-packets/{packet_dir_name(slot, src)}/`",
            "",
        ]
    lines += [
        "## Resources",
        "",
        *[f"- `{r}` — {reg.get(r).title}" for r in RESOURCES if r in reg],
        "",
    ]
    return "\n".join(lines)


def packet_dir_name(slot: dict, src: HistoricalSource) -> str:
    return slot["slot_id"] if src.rights_permit_commit else f"pending-rights/{slot['slot_id']}"


def packet_files(
    slot: dict, src: HistoricalSource, draft: Passage, reg: SourceRegistry
) -> dict[str, str]:
    numbered = "\n".join(
        f"{i:>3}  {line}" for i, line in enumerate(draft.diplomatic_transcription.split("\n"), 1)
    )
    readme = "\n".join(
        [
            f"# Review packet — {slot['slot_id']} / {draft.passage_id}",
            "",
            "**For:** a qualified transcriber and an independent checker (two different people).",
            "**Task:** verify, character by character, a DRAFT diplomatic transcription against the facsimile.",
            "",
            "> The draft was produced by an AI system reading a facsimile image. It is **UNVERIFIED**. Do not treat",
            "> it as correct; it may contain misreadings. This packet contains **no translation of any kind**. Do not",
            "> consult AI tools, and do not use the Wikisource text, except as a last-resort hint recorded as such.",
            "",
            "## 1. Source",
            "",
            *witness_block(src),
            "",
            "## 2. Where to look",
            "",
            f"- Locator: {draft.locator}",
            f"- Image read for the draft (derivative, with SHA-256): {draft.facsimile_reference}",
            "- **Verify against the original digitisation** (persistent identifier above), at full resolution.",
            "",
            "## 3. Draft transcription (line-numbered copy in `transcription_lines.txt`)",
            "",
            "```text",
            draft.diplomatic_transcription,
            "```",
            "",
            f"SHA-256 of the draft text: `{draft.diplomatic_sha256}`",
            "",
            "## 4. Conventions used in the draft",
            "",
            draft.typography_notes or "—",
            "",
            "## 5. Flagged uncertainties (resolve each one, or leave it explicitly unresolved)",
            "",
            draft.spelling_notes or "—",
            "",
            "## 6. Other notes",
            "",
            draft.notes or "—",
            "",
            "## 7. Dictionary and reference works (cite only what you actually consult)",
            "",
            *[f"- `{r}` — {reg.get(r).title}" for r in RESOURCES if r in reg],
            "",
            "## 8. Instructions",
            "",
            f"1. Read `{PROTOCOL}` in full.",
            "2. **Transcriber:** confirm the copy and shelfmark in the library's own viewer; record the exact leaf or",
            "   page and the stable image URL; correct the draft line by line in `corrections.csv`.",
            "3. **Checker (a different person):** repeat the comparison independently. Do not rely on the transcriber's",
            "   corrections, then reconcile.",
            "4. Keep abbreviations, ſ, u/v, i/j, ⁊ or &, tildes, punctuation, spacing and lineation exactly as printed.",
            "   Do not modernise or correct.",
            "5. Record copy-specific marks (manuscript notes, stamps) in the notes, never in the text.",
            "6. Both sign `signoff.md`. Return the packet to the project lead. The status changes to",
            "   `transcription_verified` only after the project lead records your check in the passage history.",
            "",
        ]
    )
    corrections = "line,draft_reads,facsimile_reads,category(letter|abbreviation|punctuation|spacing|lineation|other),note,found_by\n"
    signoff = "\n".join(
        [
            f"# Sign-off — {slot['slot_id']} / {draft.passage_id}",
            "",
            "People only; an AI system can never sign.",
            "",
            "| Role | Name | Qualification | Date | Copy/shelfmark confirmed | Result (accepted / corrected / rejected) | Differences found |",
            "|---|---|---|---|---|---|---|",
            "| Transcriber | | | | | | |",
            "| Independent checker | | | | | | |",
            "",
            "## Audit trail",
            "",
            "| Date | By | Action | Notes |",
            "|---|---|---|---|",
            *[f"| {e.on} | {e.by} | {e.action} | {e.notes or ''} |" for e in draft.review_history],
            "| | | | |",
            "",
        ]
    )
    return {
        "README.md": readme,
        "transcription_lines.txt": numbered + "\n",
        "corrections.csv": corrections,
        "signoff.md": signoff,
        "metadata.json": json.dumps(
            {
                "slot": slot,
                "source": src.model_dump(mode="json"),
                "draft": draft.model_dump(mode="json", exclude={"reference_translations"}),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    }


def main(argv: list[str]) -> int:
    slots = [
        json.loads(line)
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    reg, errors = SourceRegistry.load(ROOT / "data" / "sources" / "source_registry.jsonl")
    if errors:
        print("registry errors:", *errors, sep="\n  ")
        return 1
    drafts = load_drafts()
    planned: dict[Path, str] = {}
    for slot in slots:
        src = reg.get(slot["source_id"])
        draft = drafts.get(slot["draft_passage_id"]) if slot.get("draft_passage_id") else None
        pending = draft is not None and not src.rights_permit_commit
        planned[SHEETS / f"{slot['slot_id']}{'.pending-rights' if pending else ''}.md"] = sheet(
            slot, src, draft, reg
        )
        if draft is not None:
            pdir = PACKETS / packet_dir_name(slot, src)
            for name, text in packet_files(slot, src, draft, reg).items():
                planned[pdir / name] = text
        elif slot.get("draft_passage_id"):
            print(
                f"note: draft {slot['draft_passage_id']} for {slot['slot_id']} not present (rights-pending file absent?)"
            )
    if "--dry-run" in argv:
        print(f"would write {len(planned)} files")
        return 0
    for old in SHEETS.glob("*.md"):
        old.unlink()
    for path, text in planned.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {len(planned)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
