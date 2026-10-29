# Roadmap

Built so far: the core method, five playbooks (`reconcile`, `logic-review`, `migrate-sql`, `clone-bi`, `change-schema`) and the light and decision weights in `SKILL.md`, the hypothesis catalog, seven scripts, templates in English and Spanish, synthetic examples, thirteen behavior scenarios and a compact rules file for agents without skill support. What follows is not done.

## Needs real-world validation (highest priority)

- Run `bi_fields.py` on real Power BI PBIR projects and Tableau workbooks. It was written from Microsoft's published schemas and the `.twb` structure and tested only on hand-built synthetic files.
- Run the catalog's SQL tests on BigQuery, Databricks and other engines, not only DuckDB.
- Run the translation checks of `transpile_sql.py` against real engines. Its report lists behaviors from sqlglot's own dialect model, not from the engines' documentation.
- Have at least two other data engineers review the hypothesis catalog and add what is missing.
- Run the behavior scenarios on agents other than Claude Code, on smaller models, and with more runs per scenario than three.
- Run the CI workflow on GitHub (it has never been executed) and re-run it after the Python 3.11 to 3.13 fix (it failed once on 3.10), and run the tests on a real 3.11 (only its grammar was checked).

## Known gaps

- `bi_fields.py` reads PBIR reports with TMDL or `model.bim` models and `.twb`/`.twbx` workbooks. Not supported: PBIR-Legacy (`report.json` only), `.pbix` files, other BI tools. For Tableau it checks fields against the workbook's own data source declarations, not against a live data source.
- `clone-bi` inventories and proposes; it does not edit report files. Helpers that remove a visual, repoint a field or reset saved values safely are not built.
- `u1_query.py` handles one key column. Composite keys are refused.
- `schema_impact.py` is a static scan of the files it is given. It cannot see notebooks, orchestration code that builds SQL as strings, other repositories, or anything in the databases themselves.
- No script yet compares `UNION` branches position by position beyond the lint signal (H21).
- The BI connector facts in `references/bi-tools.md` were verified on 2026-10-25 and will age. The Tableau MCP tool list and support level were not verified.

## Adapters named but not exercised

Lakebridge reconciliation and data-diff are described in `references/adapters.md` as places where they would fit. Neither is used by any script or test here.

## Ideas, not commitments

- A lighter first reply for tiny tasks (the light path still costs roughly twice a plain edit).
- Column-level lineage through sqlglot for `schema_impact.py`.
- Spanish translations of the playbooks (templates and READMEs are already bilingual).
