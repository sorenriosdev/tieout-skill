# tieout

*[Leer en español](README.es.md)*

An open skill for AI agents that work on data. Any change to a query, model, schema, pipeline or dashboard is made with dated evidence, explicit approval and a way back. Tying out figures between two versions of the same thing (an engine migration, a logic refactor, a changed metric definition, an audit) is the central check.

It is written for data engineers, analysts, BI developers and AI engineers. It does not compete with existing tools; it tells the agent when to use them and what to do when they are missing.

## What it does

Five playbooks: `reconcile` (tie out figures), `logic-review` (compare queries, with or without data), `migrate-sql` (between engines), `clone-bi` (Power BI and Tableau reports) and `change-schema` (expand and contract). Every task starts by picking a weight: **light** (one approved change: backup, change, one register row), **decision** (a rule with two readings: a question, no change) or **full** (the whole cycle).

- Declares a working mode from the access available: `code-only`, `one-system` or `both`.
- Runs a gated cycle: no phase starts without the artifact of the previous one (Spec → baseline → localize → propose → approve → apply → verify → record).
- Localizes differences with a ladder (total → period → dimension → key → row → expression) and a catalog of 22 hypotheses, most with a SQL test.
- Closes a case only when a script shows that Δ = B − A is explained by measured effects plus a residual within the tolerance agreed in the Spec.
- Labels every statement as verified, decided by someone, user data, or assumption.

## What it does not do

- It does not decide business rules. When a rule has two plausible readings, it writes the question with options and evidence and waits for a named approver.
- It does not estimate financial impact or prescribe solutions.
- It does not do by hand what a tool should do. If sqlglot or a database client is missing, it says so and stops or declares a reduced mode.

## What is core and what is optional

The method (modes, gated cycle, 12 principles, evidence labels, playbooks) is tool-agnostic. The scripts for SQL (`sql_review`, `transpile_sql`, `u1_query`, `schema_impact`, `waterfall`) need only Python and sqlglot. `scripts/bi_fields.py` and `playbooks/clone-bi.md` are **optional adapters** for the file formats of Power BI (PBIR, TMDL) and Tableau (`.twb`), built from those vendors' public documentation. Without an adapter the agent reads the definition files or asks a connector, and labels what it read.

## Status: early draft

What has and has not been checked:

- **Behavior.** Thirteen synthetic scenarios in Claude Code, one model, two or three runs per arm. The skill scored 0.90 on average against 0.56 without it, at about 1.8 times the cost. It helped most on missing-tool honesty, backups, tie-outs closed by script, and asking instead of choosing a business rule. It did not help on a missing-column check, and it was not even invoked in a read-only investigation (the description was changed afterwards and that change is unmeasured). Details, limits and every grader change: [evals/RESULTS-2026-10-26.md](evals/RESULTS-2026-10-26.md). The scenarios and the skill were tuned together, so treat this as a first signal.
- **Real data: none.** `bi_fields.py` (Power BI PBIR and Tableau) was written from Microsoft's published schemas and the `.twb` structure and tested on hand-built files only. The catalog's SQL tests ran in DuckDB, not on BigQuery, Databricks or other engines; H17 has an interval literal that sqlglot does not adapt correctly to BigQuery. `transpile_sql.py` output parses back but has not been run on a real engine.
- The hypothesis catalog comes from one person's field experience and has not been reviewed by others.
- Only Claude Code was tested. The skill follows the open [Agent Skills](https://agentskills.io) format and `adapters/AGENTS.md` carries the rules for agents without skill support; neither has been run elsewhere.
- The first CI run failed on Python 3.10 because the format validator needs 3.11 or later; the workflow was corrected (3.11 to 3.13, pinned dependencies) and has not been run again. Local tests ran on Python 3.12 and 3.14; 3.11 is checked for grammar only.

See [ROADMAP.md](ROADMAP.md) for what is missing, and [docs/field-test.md](docs/field-test.md) to try it on your own work.
## Install

Claude Code, as a plugin (`#next` is the branch under test; drop it once `main` has the release you want):

```
claude plugin marketplace add sorenriosdev/tieout-skill#next
claude plugin install tieout@tieout-skill
```

Other agents that read Agent Skills: copy `skills/tieout/` into the agent's skills folder.

The bundled scripts need Python 3.11 or later. `sqlglot` is needed for dialect work and `duckdb` to run the tests and the example:

```
pip install sqlglot duckdb
```

The tests and CI run with sqlglot 30.21.0 and DuckDB 1.5.6 (`requirements-dev.txt`), chosen as mature releases rather than the newest ones.

## Using it

In Claude Code the skill activates by itself on tasks like "these two numbers don't match", "translate this query to BigQuery" or "check this report before I publish it". To force it: `/tieout:tieout` followed by the task, for example `/tieout:tieout compare these two versions of the query; I have no database access`. Agents that read Agent Skills: copy `skills/tieout/` into the agent's skills folder and ask for it by name. Codex: see [docs/codex.md](docs/codex.md) (untested).

For a read-only investigation, say so in the prompt; the skill then creates no files and puts everything in the reply.

## Your own rules

Put the rules your team has approved in `tieout/rules.local.md` in your project, as a table of rule, scope, approver and date. A rule without approver or date is treated as an assumption, not applied, and raised as a question. The skill reads that file and applies those rules as decided. It never writes to it.

## Repository layout

| Path | What it is |
|---|---|
| `skills/tieout/SKILL.md` | Entry point: modes, cycle, change classes, routing |
| `skills/tieout/references/` | Core principles, ladder, evidence labels, detection flags, hypothesis catalog |
| `skills/tieout/playbooks/` | `reconcile`, `logic-review`, `migrate-sql`, `clone-bi`, `change-schema` |
| `skills/tieout/assets/templates/{en,es}/` | Spec, change proposal, decision register, evidence log, findings |
| `skills/tieout/scripts/` | `check_capabilities`, `waterfall`, `u1_query`, `sql_review`, `transpile_sql`, `bi_fields`, `schema_impact` |
| `examples/` | Synthetic tie-out case and synthetic Power BI project |
| `adapters/AGENTS.md` | Compact rules for agents without skill support (generated from `SKILL.md`) |
| `docs/field-test.md` | How to try it on real work and what to measure |
| `evals/` | Behavior scenarios for `claude plugin eval`, and their results |
| `tests/` | Catalog and script tests |

## Check it yourself

```
python tests/test_hypotheses.py
python tests/test_scripts.py
python examples/reconcile-synthetic/run_example.py
claude plugin eval . --scaffold --allow-tools Write Edit Bash   # real, billed model runs
```

## License

[MIT](LICENSE) © 2026 sorenriosdev
