# Research methodology

## 1. Design

A calibration study: AI translation outputs for verified historical passages are compared with
independent expert references and judged by blinded expert reviewers. Four pipelines are compared on
the same passages under recorded conditions. The design measures **translation fidelity (QC2)** while
controlling **transcription fidelity (QC1)** and keeping **interpretation (QC3)** out of scope.

## 2. Corpus

- **Comparable texts.** Sixteenth-century French prose and poetry, Renaissance Latin prose and verse,
  and mixed French/Latin passages, chosen to resemble the linguistic challenges of the quatrains:
  archaic lexis, Latinisms, compressed syntax, code-switching, classical allusion. Nostradamus is
  excluded so that later work is not contaminated.
- **Witness-based.** Every passage comes from a specific registered witness (edition/exemplar) with
  checked provenance and an exact locator. See [source-authentication.md](source-authentication.md).
- **Diplomatic transcription** checked against facsimile by a second person. See
  [transcription-policy.md](transcription-policy.md).
- **Sizes.** Pilot of 20 (5/5/5/5), then 80 (30/20/15/5/10). Targets, not quotas to be filled with
  weak data.

## 3. Reference translations

At least one independent modern French and one English reference per passage, by qualified
translators or from rights-cleared published editions. References must not be produced or
post-edited by any evaluated model. Multiple legitimate references are encouraged, and ambiguity is
annotated rather than resolved by fiat.

## 4. Pipelines

A direct; B two-stage via modern French (stage 2 does not see the original); C retrieval-augmented
with provenance-tracked lexical evidence; D structured linguistic analysis. See
[translation-protocol.md](translation-protocol.md).

## 5. Evaluation

1. **Human MQM review (primary)**, blinded, by at least two reviewers per item, using the taxonomy in
   [evaluation-framework.md](evaluation-framework.md).
2. **Automated metrics (secondary)**: chrF/chrF++ against all references; optional COMET. These are
   never treated as proof of correctness.
3. **Agreement**: percent agreement, Cohen's κ and penalty correlation, reported with n.
4. **Calibration**: stated confidence against reviewed correctness. See
   [confidence-calibration.md](confidence-calibration.md).

## 6. Partitioning and contamination

Deterministic, seeded, group-isolated partitions (by work or author), 48/12/20 for the full corpus.
The test set is frozen once used and protected by tooling. Leakage checks cover duplicates,
cross-split sharing, and overlap between retrieval material and held-out references. Pretraining
contamination cannot be excluded and is reported as a limitation. See
[calibration-methodology.md](calibration-methodology.md).

## 7. Statistical stance

Small samples call for interval estimates (Wilson for proportions, percentile bootstrap for means),
descriptive comparisons rather than significance claims, and explicit refusal to claim calibration
below a configured minimum sample. A 20-passage held-out set cannot establish a precise accuracy rate.

## 8. Decision

The milestone gate compares deliverables with acceptance criteria and recommends continue,
remediate or defer. The project lead decides. See [project/milestones.md](project/milestones.md).
