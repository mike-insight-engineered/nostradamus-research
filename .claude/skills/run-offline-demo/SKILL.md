---
name: run-offline-demo
description: Run and interpret the synthetic, zero-cost end-to-end demonstration (fixtures + mock provider). Use when asked to demo the framework, smoke-test the pipeline, or show what the reports look like.
---

# Run the offline demonstration

1. `uv run nr demo --output-dir experiments/runs/demo` (the default location; git-ignored).
2. Inspect `experiments/runs/demo/reports/*.md`, `evaluation_summary.json`, `calibration.json` and
   `runs/demo-*/manifest.json`.
3. When summarising, say plainly:
   - the passages are **synthetic** texts imitating period spelling, not historical sources;
   - the "translations" come from a **mock** provider that perturbs fixture references;
   - the reviews are **synthetic** (chrF rule), not human judgements;
   - therefore none of the numbers say anything about AI translation quality.
4. Use the demo to show the workflow, the file formats and the report layout. Do not use it as evidence.
