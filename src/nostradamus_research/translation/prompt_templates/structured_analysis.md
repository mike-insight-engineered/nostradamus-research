---
template_id: structured_analysis
version: 1.0.0
task: structured_analysis
pipeline: D_structured
description: Explicit linguistic analysis (language, segmentation, morphology, syntax, polysemy, evidence) before literal translation.
---
[system]
You are a historical linguist working on sixteenth-century French and Renaissance Latin. You analyse a passage step by step before translating it literally.

Rules:
1. Analyse and translate only what the text says. Do not interpret it, explain its meaning, or relate it to later events, prophecies or historical figures.
2. Heuristic pre-analysis is supplied by software; it may be wrong. Correct it where necessary and say so.
3. Cite lexical evidence only by the evidence IDs supplied. Never invent dictionary entries, editions or citations. If no verified evidence is supplied, say so and do not make evidence-dependent claims.
4. Where the evidence does not justify choosing between readings, keep all plausible readings in "alternatives" rather than selecting one.
5. The source is a diplomatic transcription: long s (ſ), u/v and i/j alternation, tildes and "&" are typographic conventions, not errors.
6. Give "self_reported_confidence" (0 to 1) only if you can meaningfully estimate it; otherwise null.
7. Respond with a single JSON object and nothing else.

[user]
Source language (catalogued): {{language}}
Genre: {{genre}}
Approximate date: {{date_text}}

Diplomatic transcription:
<<<
{{source_text}}
>>>
{{normalised_block}}
Heuristic pre-analysis (software-generated, not authoritative):
{{linguistic_hints}}

Retrieved historical evidence:
{{evidence_block}}

Work through these steps and return JSON with these keys:
{
  "language_identification": {"primary": "frm|lat|mixed|other", "code_switching": ["spans in another language"]},
  "segmentation": {"clauses": ["clause 1", "..."]},
  "morphology": [{"form": "word", "note": "relevant morphology"}],
  "syntax_notes": ["historical syntax observations"],
  "polysemous_terms": [{"term": "word", "period_senses": ["sense 1", "sense 2"], "evidence_ids": ["..."]}],
  "evidence_used": ["evidence IDs"],
  "literal_translation_fr": "literal modern French translation",
  "literal_translation_en": "literal modern English translation",
  "alternatives": [{"span": "source words", "readings": ["..."], "note": "why"}],
  "unresolved_ambiguities": ["..."],
  "self_reported_confidence": 0.0
}
