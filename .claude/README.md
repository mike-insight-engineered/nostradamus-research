# Claude Code configuration for this project

Project-wide rules live in [`../CLAUDE.md`](../CLAUDE.md). This directory adds **specialised agents**
and **reusable skills**.

## Agents (`agents/`)

| Agent | Purpose | Can edit files? | Limits |
|---|---|---|---|
| `source-verifier` | Locate candidate witnesses, gather catalogue data, draft verification evidence | No (proposes registry changes as text) | May not propose any status above `located` unless a named human supplied the evidence; never asserts authenticity |
| `translation-developer` | Pipelines, prompt templates, providers | Yes (code and templates) | Mock provider only; never runs paid calls; never uses test-split data for prompt design |
| `translation-evaluator` | Run metrics, prepare review packages, summarise results | No | Never produces review judgements; never presents synthetic/mock results as findings |
| `provenance-auditor` | Audit registry, corpus, references, rights and manifests | No (read-only + validation commands) | Reports issues; does not fix data |
| `software-engineer` | Code quality, tests, CI, refactoring | Yes | Must keep integrity validators intact; tests must pass offline |

None of these agents may make unreviewed historical or scholarly claims, mark anything verified,
authorise paid API calls or other spending, or commit or push without an explicit request.

## Skills (`skills/`)

| Skill | Use |
|---|---|
| `verify-source` | Step-by-step workflow for moving a source one rung up the verification ladder |
| `run-offline-demo` | Run and interpret the synthetic end-to-end demonstration |
| `prepare-review-package` | Export a blinded package, then import and check completed reviews |
| `audit-provenance` | Full provenance/rights/leakage audit with a written report |
