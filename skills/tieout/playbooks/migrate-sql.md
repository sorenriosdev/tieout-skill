# Playbook: migrate-sql

Use to move queries from one SQL engine to another (for example DuckDB, BigQuery, Databricks, PostgreSQL, Snowflake, SQL Server). The migration is done when each query returns the same numbers on the target as on the source, within the tolerance in the Spec, with every difference explained or decided. A query that merely parses on the target is not migrated.

## Tool gate

This playbook depends on sqlglot. Run `python scripts/check_capabilities.py --require sqlglot`. If it exits 1, the first sentence of your reply names the missing tool. Then stop, or continue in a reduced mode the user accepts: a hand translation, labelled `[assumption]`, delivered with the equivalence test and never described as ready to run.

## Phases

### 0. Capabilities and mode

As in `SKILL.md`. In addition, find out whether you can run queries on the source, the target, both, or neither. Equivalence cannot be shown without running both.

### 1. Spec

Fill `spec.md`: source and target engine, the list of queries, the data window and cut-off to compare on, the measures that must match, tolerances ε_abs and ε_rel, and who approves differences that are not purely technical (rounding policy, NULL handling, time zone, ordering of ties).

### 2. Baseline

Run each source query on the source engine over the agreed window and record totals per period and by the main dimensions in `evidence-log.md` (ladder rungs L1 to L3, `references/ladder.md`). Without access to the source, those figures come from the user: `[user data: source, date]`.

### 3. Translate

One query at a time, never overwriting a file:

`python scripts/transpile_sql.py <file> --from <source> --to <target> --out <new file>`

Read the report it prints after the SQL:

- **Unsupported constructs**: sqlglot could not translate them faithfully. Each is a manual task for the user's review.
- **Parse-back**: only shows the output is syntactically valid.
- **Behaviors that differ**: NULL ordering, integer division, NULL in concatenation, LEAST/GREATEST, array index base, time zones, row selection, numeric casts. They are taken from sqlglot's model of the dialects, not from the engines' documentation. Each one that applies to the query is a hypothesis to test in the next step.
- **Interval literals**: check them by hand in the target engine.

The translation is a draft. In this repository's own check, a DuckDB to BigQuery translation of an expression that formats a timestamp parsed back successfully but used a date-formatting function on what looks like a timestamp and kept a quoted interval literal. Neither was run on BigQuery. Parsing proves syntax only.

### 4. Equivalence test

Run the translated query on the target over the same window and tie out with `reconcile.md`:

- totals per period and per dimension against the baseline;
- the key decomposition (`scripts/u1_query.py`, dialect of the target) for rows present on one side only;
- the catalog tests for each behavior listed in step 3 that applies.

Without access to the target, hand over the translated query and these test queries, and report the migration as `not verified`.

### 5. Propose, approve, apply

A translation proven equivalent within tolerance is a technical equivalent: it needs the user's permission to write, not a business approver. Any difference you could not eliminate that changes which rows or values count (a rounding rule, how NULL is treated, which row wins a tie) is a business rule: write the question with options and wait for the named approver. Back up any file you replace. Do not deploy to the target engine without permission.

### 6. Record

One row per query in `decision-register.md`: query and version, dialect pair, sqlglot version, tolerance, result of the equivalence test, remaining decisions and who made them.

## Not covered

- Data movement, schema creation and permissions on the target.
- Performance tuning and cost.
- Procedural code (stored procedures, scripting blocks): sqlglot targets queries; check the output carefully or treat these as manual.
