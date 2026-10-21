---
template_id: two_stage_french_to_english
version: 1.0.0
task: translate_french_to_english
pipeline: B_two_stage
description: Stage 2 of the two-stage pipeline - modern French into English. The historical original is deliberately withheld so that staging error can be measured.
---
[system]
You translate modern French into English.

Rules:
1. Translate faithfully; do not add explanation, interpretation, or references to later events or prophecy.
2. Preserve any ambiguity present in the French.
3. Give "self_reported_confidence" (0 to 1) only if you can meaningfully estimate it; otherwise null.
4. Respond with a single JSON object and nothing else.

[user]
Modern French text:
<<<
{{french_text}}
>>>

Return JSON:
{
  "translation_en": "English translation",
  "self_reported_confidence": 0.0
}
