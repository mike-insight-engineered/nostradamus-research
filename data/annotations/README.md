# data/annotations

| Path | Contents |
|---|---|
| `lexical_evidence.jsonl` | Historical lexical evidence for retrieval (pipelines C and D). **Empty.** Entries are added only by people who have consulted the cited source. Verified entries require `verified_by` / `verified_on`. |
| `review_packages/<PKG>/` | Blinded packages sent to reviewers (`nr review export`) |
| `review_packages/<PKG>-KEY/` | Unblinding keys: **git-ignored; never send to reviewers** |
| `reviews/<PKG>.jsonl` | Imported, validated reviews linked to results (`nr review import`) |

Never create, edit or simulate review judgements for real data. Synthetic reviews exist only inside
the demo output.
