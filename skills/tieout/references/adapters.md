# Adapters

Optional integrations. The skill never depends on one: each is detected, used if present, and recommended (not installed) if absent. Whenever an adapter produces evidence, label it with the adapter, its version and the date.

## How detection works

`scripts/check_capabilities.py` reports Python libraries and command-line tools. It cannot see connectors (MCP servers and similar) or other agent tools; list those from the tools your environment exposes and ask the user about the rest.

## Adapters

| Adapter | What it adds | Detection | Without it |
|---|---|---|---|
| sqlglot | Parsing, dialect translation, structural review, impact scans (`transpile_sql.py`, `sql_review.py`, `u1_query.py`, `schema_impact.py`) | `check_capabilities.py` lists it | The first sentence of the reply names the missing tool; stop, or a reduced mode with hand-made work labelled `[assumption]` |
| DuckDB | Running the catalog's tests and the example locally | `check_capabilities.py` | Tests are handed over for someone with a database to run |
| Database clients (psql, bq, databricks, snowsql, sqlcmd) | Running queries on a real engine, which `both` and `one-system` modes need | `check_capabilities.py` | `code-only` mode |
| data-diff | Row-level comparison between two databases | `check_capabilities.py` lists the library and the CLI | `u1_query.py` at key level, run on each side |
| Power BI Authoring MCP server | Reading and changing semantic models, running DAX, working with TMDL | Ask the user; look at your tool list | Files only (`references/bi-tools.md`) |
| Tableau MCP server | Reading Tableau Cloud or Server content | Ask the user; look at your tool list | `bi_fields.py twb` on the workbook file |
| Lakebridge reconciliation | A Databricks-side reconciliation of migrated data | Ask the user | `playbooks/reconcile.md` with the user's queries |

Only the first four are exercised by this repository's tests. The connector and Lakebridge rows describe where they fit; their capabilities should be taken from the vendors' current documentation when you use them. `references/bi-tools.md` records what was verified for the BI connectors, and when.

## Adding an adapter

An adapter needs: how to detect it, what it covers, what the skill does without it, and the label its output carries. Add it to the table; keep the core independent of it.
