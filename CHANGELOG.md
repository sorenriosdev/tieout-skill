# Changelog

## 0.1.0 (early draft)

First public release.

- Method for changing data work with evidence, approval and a way back: three weights (light, decision, full), a nine-phase cycle for full cases, a closing block, evidence labels and twelve principles.
- Playbooks: reconcile, trace, logic-review, migrate-sql, clone-bi, change-schema.
- Catalog of 23 hypotheses with 21 SQL tests verified in DuckDB; scripts for waterfall, key decomposition, SQL lint and diff, dialect translation, BI report fields and schema impact.
- Optional `tieout/context.md` that the agent drafts from files the user attaches, and `tieout/rules.local.md` for approved rules. Both stay in the user's project.
- Measured on 13 synthetic scenarios in Claude Code only; see `evals/RESULTS-2026-10-30.md`.

Known limits: no run on real BI or warehouse data, no test on other agents, and the method uses more tokens than working without it.
