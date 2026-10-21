# Translation protocol (QC2)

## Common rules (all pipelines)

1. Input is the **diplomatic transcription**, with catalogued language, genre and date.
2. Output: modern French and modern English, plus alternatives and unresolved ambiguities, as JSON.
3. **No interpretation.** No explanation of meaning, prophecy, or identification with later events or
   people. Guardrails (`translation/guardrails.py`) *flag* such output. They never silently remove it.
4. No invented specificity: names, dates or places not in the text must not appear.
5. Confidence: the model may report `self_reported_confidence` in [0, 1] or null. Values outside the
   range or of the wrong type are discarded. Nothing is imputed.
6. Prompt templates are versioned files (`translation/prompt_templates/*.md`), pinned in
   `config/translation.yaml`. Each call records template ID, version and prompt hash.
7. Defaults: temperature 0.0 and max_tokens 2048 (configurable). Set temperature to `null` for
   providers or models that reject it.

## Pipeline A — Direct (baseline)

One call: historical text → modern French + English. No retrieval.

## Pipeline B — Two-stage

1. Historical text (French or Latin) → modern French.
2. Modern French → English. **The original is withheld** in stage 2.

The intermediate French is stored (`intermediate_fr`). Staging loss is estimated by a paired
comparison of B and A English outputs: chrF difference and MQM penalty difference with bootstrap
intervals, reported by `nr report benchmark`. The definitive measure is reviewer-identified errors
in English that are absent from B's French. Stated confidence is `min(stage1, stage2)`, or null if
either is null.

## Pipeline C — Retrieval-augmented

1. Tokens of the diplomatic text are matched (folded forms, including variant spellings) against
   `data/annotations/lexical_evidence.jsonl`.
2. Only entries at or above `retrieval.minimum_evidence_status` (default `transcription_verified`)
   count as evidence. Synthetic entries are excluded unless explicitly allowed (demos only).
3. Evidence is supplied with its ID, kind, status, sense, citation and locator. The model must cite
   only supplied IDs. Citing anything else raises a `cited_unsupplied_evidence` flag.
4. **If no verified evidence matches**, the prompt says so and instructs the model not to make
   evidence-dependent claims. The result records `retrieval_status: no_evidence` and a limitation.

*As of 2026-10-21 the evidence store is empty, so C behaves as A plus an abstention instruction until
checked entries are added.*

## Pipeline D — Structured linguistic analysis

Software pre-analysis (labelled heuristic): language identification with candidate code-switch spans,
clause segmentation, morphology/orthography flags, and retrieval as in C. The model then returns:
language identification; segmentation; morphology; historical syntax notes; polysemous terms with
period senses and evidence IDs; evidence used; literal modern French; literal modern English;
alternatives; unresolved ambiguities; confidence. Polysemous terms with several senses are kept as
alternatives. They are not collapsed into one reading.

## Run procedure

1. `nr translate run --pipeline X --provider P --split development --dry-run` (check passages, call count).
2. Run without `--dry-run`. Paid providers also need `--allow-paid-api`.
3. Never run on `test` except as pre-registered (see the execution plan), with `--allow-test-split
   --test-reason`.
4. Commit the run directory (manifest + results) when it is part of the research record.
