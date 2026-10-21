"""Integrity checks for pilot research artifacts (candidate manifest, drafts, rights separation).

Rights-pending drafts are git-ignored, so these tests must pass both with and without them.
"""

import json
from collections import Counter

from nostradamus_research.corpus.io import load_passages
from nostradamus_research.models.enums import DataOrigin, VerificationStatus, status_rank
from nostradamus_research.provenance.registry import SourceRegistry

MANIFEST = "data/candidates/pilot_candidates.jsonl"
DRAFT_DIR = "data/transcriptions/drafts"
CLEARED = f"{DRAFT_DIR}/pilot_draft_passages.cleared.jsonl"
PENDING = f"{DRAFT_DIR}/pilot_draft_passages.pending-rights.jsonl"


def _slots(root):
    return [
        json.loads(x)
        for x in (root / MANIFEST).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def _drafts(root):
    out = {}
    for name in (CLEARED, PENDING):
        path = root / name
        if path.exists():
            result = load_passages(path)
            assert result.ok, result.errors
            out.update({p.passage_id: (name, p) for p in result.records})
    return out


def test_manifest_has_20_slots_with_pilot_composition(repo_root, cfg):
    slots = _slots(repo_root)
    assert len(slots) == 20 and len({s["slot_id"] for s in slots}) == 20
    counts = Counter(s["pilot_group"] for s in slots)
    assert counts == {str(k): v for k, v in cfg.corpus.targets.pilot.items()}


def test_manifest_references_registered_sources_and_makes_no_verification_claims(repo_root, cfg):
    reg, errors = SourceRegistry.load(cfg.path("source_registry"))
    assert not errors
    for s in _slots(repo_root):
        assert s["source_id"] in reg, s["slot_id"]
        assert s["human_verification_status"] == "not_started"
        assert s["candidate_status"] == "candidate"
        assert s["transcription_status"] in {"pending", "draft_ai_unverified"}
        assert s["reference_translation_status"].startswith("none_obtained")
        assert isinstance(s["audit_flags"], list)
        if s["proposed_replacement"]:
            assert s["proposed_replacement"]["source_id"] in reg
            assert s["proposed_replacement"]["status"].startswith("proposed")


def test_cleared_drafts_only_from_committable_sources(repo_root, cfg):
    reg, _ = SourceRegistry.load(cfg.path("source_registry"))
    for name, p in _drafts(repo_root).values():
        src = reg.get(p.source_id)
        if name == CLEARED:
            assert src.rights_permit_commit, p.passage_id
        else:
            assert not src.rights_permit_commit, p.passage_id


def test_drafts_are_unverified_and_linked(repo_root, cfg):
    drafts = _drafts(repo_root)
    assert (repo_root / CLEARED).exists()
    for s in _slots(repo_root):
        if not s["draft_passage_id"]:
            continue
        if s["draft_passage_id"] not in drafts:
            assert "pending-rights" in s["draft_location"]  # absent only if git-ignored
            continue
        name, p = drafts[s["draft_passage_id"]]
        assert s["draft_location"].startswith(name)
        assert p.data_origin is DataOrigin.HISTORICAL_SOURCE
        assert p.verification_status is VerificationStatus.CANDIDATE
        assert "UNVERIFIED" in (p.transcribed_by or "") and "AI-ASSISTED DRAFT" in (p.notes or "")
        assert not p.reference_translations
        assert all(e.action != "transcription_checked" for e in p.review_history)


def test_drafts_are_not_in_the_research_corpus(cfg):
    path = cfg.path("passages")
    if path.exists():
        ids = {p.passage_id for p in load_passages(path).records}
        assert not ids & {"PSG-MX-0001", "PSG-FP-0001", "PSG-FV-0001", "PSG-LP-0001"}


def test_no_source_above_located_without_human_evidence(cfg):
    reg, _ = SourceRegistry.load(cfg.path("source_registry"))
    for s in reg:
        if status_rank(s.verification_status) > status_rank(VerificationStatus.LOCATED):
            assert s.verification_evidence, s.source_id
        for e in s.verification_evidence:
            assert (
                "claude" not in e.verified_by.lower() and "ai" not in e.verified_by.lower().split()
            )


def test_licensing_files_present(repo_root):
    assert "GPL-3.0-or-later" in (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    assert (
        (repo_root / "LICENSES" / "CC-BY-4.0.txt")
        .read_text(encoding="utf-8")
        .startswith("Attribution 4.0 International")
    )
    assert "pending-rights" in (repo_root / ".gitignore").read_text(encoding="utf-8")
    assert "No blanket licence" in (repo_root / "DATA_LICENSE.md").read_text(encoding="utf-8")
