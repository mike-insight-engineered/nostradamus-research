# data/processed

`passages.jsonl` is the canonical research corpus: one validated `Passage` per line (see
`schemas/passage.schema.json`). It is created by `nr passages import`, never by hand-editing hashes.

It does not exist yet: no verified passages have been acquired (CAL-05 to CAL-08). Commands that
need it report this clearly. Synthetic fixtures (`data/fixtures/`) must never be placed here.
