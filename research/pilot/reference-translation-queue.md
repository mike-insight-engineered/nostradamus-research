# Human reference-translation and review queue

Status values: `not_started` · `brief_sent` · `in_progress` · `delivered` · `reviewed` · `attached`.
A slot enters this queue only after its **transcription is verified** (`transcription-verification-queue.md`).
Translators must work from the verified diplomatic text and the facsimile, and must **not** see any AI output.

| Slot | Passage ID | Needs FR | Needs EN | Translator (FR) | Translator (EN) | Reviewer | Status | Blocker |
|---|---|---|---|---|---|---|---|---|
| FP-01 | PSG-FP-0001 | yes | yes | | | | not_started | transcription unverified |
| FV-01 | PSG-FV-0001 | yes | yes | | | | not_started | transcription unverified |
| LA-01 | PSG-LP-0001 | yes | yes | | | | not_started | transcription unverified |
| MX-01 | PSG-MX-0001 | yes | yes | | | | not_started | transcription unverified |
| other 16 slots | — | yes | yes | | | | not_started | no transcription yet |

---

## Translation brief (send with each verified passage)

**Project:** Nostradamus Research, Milestone 1: calibration of AI translation of sixteenth-century French and
Renaissance Latin. Your translation is the **reference** against which machine translations are judged.

**You receive:** the diplomatic transcription (exactly as printed), the facsimile link and locator, bibliographic
metadata, and the list of flagged uncertainties. You will **not** receive any machine translation, and please do
not consult AI tools.

**Please produce, for each passage:**
1. A **literal modern French** translation (or a modernisation, for French sources) that is faithful to the period
   sense, keeps the original's sentence structure where intelligible, and adds nothing.
2. A **literal modern English** translation on the same principles. Translate from the original, not from your
   French, if possible.
3. **Notes** for every word or construction where the period sense differs from the modern one, citing the
   dictionary or grammar you actually consulted (e.g. Huguet, DMF, Cotgrave, Lewis & Short), with headword and page.
4. **Ambiguities:** where more than one reading is defensible, give each reading. Do not choose silently.
5. **Do not** interpret the passage beyond its literal meaning: no allusions to later events and no prophecy.
6. Your name, qualification, date, and the rights you grant for the translation (proposed: CC BY 4.0. To be
   confirmed under ADR 0005).

**Return format:** plain text or the CSV row template below.

```text
slot_id, passage_id, target_language, translation, notes, ambiguities, translator, qualification, date, licence
```

**Independence declaration (required):** "I produced this translation without using machine translation or AI
tools, and without consulting machine output for this passage."
