# data/fixtures — SYNTHETIC TEST DATA

**Nothing in this directory is historical evidence.**

| File | Contents |
|---|---|
| `synthetic_sources.jsonl` | 8 synthetic "witness" records (`SYN-WIT-*`), status `candidate` |
| `synthetic_passages.jsonl` | 12 synthetic passages (`SYN-PSG-*`) across the five categories, written in imitation of sixteenth-century spelling, each with one synthetic French and one synthetic English reference |
| `synthetic_lexical_evidence.jsonl` | 4 synthetic evidence entries citing a "Synthetic fixture dictionary (does not exist)" |

All records carry `data_origin: synthetic_fixture` and `SYN-` IDs. They exercise validation,
splitting, the four pipelines (with the mock provider), review packages, evaluation, calibration and
reporting, at zero cost and offline. The texts were composed for this purpose. They are not quotations
or transcriptions of any real work, and their "references" are not scholarly translations.
