# Open issues

## Research / data

| ID | Issue | Blocks |
|---|---|---|
| OI-01 | No witness located or authenticated; all 26 registry records are candidates entered from general knowledge | CAL-05–08 |
| OI-02 | Licensing terms unconfirmed for BVH, Gallica, Frantext, Perseus, Huguet, DMF | CAL-02, CAL-09, retrieval |
| OI-03 | No qualified translators/reviewers recruited; budget not set | CAL-09, CAL-10 |
| OI-04 | Lexical evidence store is empty; pipeline C/D retrieval currently abstains | RQ4 |
| OI-05 | No provider or model chosen; paid use not authorised; pricing not recorded | CAL-12 |
| OI-06 | Historical-grammar bibliography and Occitan resources need a specialist | Bibliography, M2 |
| OI-07 | Protocols (CAL-01, 03, 04) and ADRs 0001–0004 await project-lead review | CAL-01–04 → Complete |
| OI-08 | Decide whether the project licence is GPL-3.0-only or GPL-3.0-or-later (LICENSE text is GPL v3; `pyproject.toml` references the file only) | Packaging metadata |

## Software / technical

| ID | Issue | Notes |
|---|---|---|
| TI-01 | Anthropic and OpenAI adapters have **not been exercised against live APIs** (by design: no paid calls). They are covered only by guard and configuration tests | Run a single low-cost smoke test once authorised; mark it `external` |
| TI-02 | OpenAI adapter uses `max_completion_tokens`; some older models expect `max_tokens`. Some newer models reject `temperature` (set it to `null` in config) | Verify against the chosen model |
| TI-03 | COMET extra is declared but untested in this environment (heavy PyTorch install; pins NumPy < 2) | Optional; never in CI |
| TI-04 | Language-ID and morphology heuristics are simple function-word and suffix rules | Labelled heuristic; pipeline D treats them as hints |
| TI-05 | Group chrF is the mean of sentence-level chrF (multi-reference), not corpus-level chrF | Documented; adequate for small n |
| TI-06 | Blinding can leak through output structure (e.g. presence of alternatives) | D's analysis and B's intermediate are hidden; documented |
| TI-07 | Agreement uses pairwise Cohen's κ; no Krippendorff's α and no adjudication workflow yet | Add if more than two reviewers per item |
| TI-08 | Windows consoles with legacy code pages may mis-render some Unicode in CLI output; files are always UTF-8 | Use Windows Terminal or `PYTHONUTF8=1` |
| TI-09 | `review_sheet.csv` is UTF-8 with BOM for Excel; reviewers must keep that encoding when saving | Documented in package README |
