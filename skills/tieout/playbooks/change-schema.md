# Playbook: change-schema

Use for any change to the structure other things depend on: adding, renaming, retyping or dropping a table or column, changing a view's output, changing a key or a partitioning, or moving data between structures. A schema change is always a **full** case (`SKILL.md`): the cost of being wrong lands on every consumer at once, and often cannot be undone.

The method is expand and contract: first add the new structure next to the old one, move consumers across with evidence at each step, and only then remove the old structure. At every step the system works and the step can be undone.

## Rules that do not bend

1. **No step without a way back.** Each step in the plan states how to undo it and what state that leaves. A step you cannot undo (a drop, a rename in place, a retype that loses precision) needs a snapshot or backup, a named approver and a grace period.
2. **Never rename, retype or drop in place.** Add the new object, migrate, switch consumers, wait, then remove the old one.
3. **Backfills are idempotent.** Running one twice gives the same result as running it once: keyed upserts or partition overwrites, never blind appends. A backfill that cannot be re-run is not finished.
4. **Dry run first.** Produce the plan and the statements, show what they would touch, and run them against a copy or a development environment before the real one. Do not run DDL in a shared or production system without the explicit permission recorded in the proposal (principle 7).
5. **Consumers are found, not assumed.** Impact analysis starts from a scan, and says what it did not scan.

## Phases

### 0. Capabilities and mode

As in `SKILL.md`. Schema work needs to know what you can run and where: development copy, production, or neither. If you cannot run anything, the output is the plan, the scan and the statements, all `not verified`.

### 1. Spec

Fill `spec.md` with: the object and the change; the consumers known so far; the environments and their order; the window during which old and new coexist; the tolerance for tying out old against new (ε_abs and ε_rel); who approves the change, who approves the final removal, and who owns each consumer.

### 2. Impact analysis (read only)

- SQL in the repository: `python scripts/schema_impact.py <folder> --table <table> --column <column> --dialect <dialect>`. It resolves aliases scope by scope and reports `certain`, `possible` and `star` references, and lists the files it could not parse.
- Power BI reports in PBIR format: the same script scans their files; `scripts/bi_fields.py` gives the fuller inventory for one report.
- Everything else (notebooks, orchestration code, stored procedures, other repositories, dashboards in other tools, ad-hoc queries): ask the user and the owners. List these as **not scanned**. A clean scan does not mean nothing depends on the object.
- If a lineage tool or connector is available, use it and label its output with its source and date. A database's own dependency views, if the user can run them, are evidence too.

Record the result in `evidence-log.md` with the date. Dependencies change; a scan is not valid after the next deployment.

### 3. Plan

Write the plan as numbered steps in a proposal, each with: the statement or action, the environment, the expected effect, **the way back**, and the check that shows it worked. A typical shape:

1. **Expand**: add the new column or table; nothing reads it yet. Way back: drop it.
2. **Backfill**: fill it from the old structure, idempotently. Way back: truncate or overwrite the new data.
3. **Dual write**: new writes go to both. Way back: stop writing to the new one.
4. **Verify**: tie out old against new with `playbooks/reconcile.md` (totals per period, key decomposition with `scripts/u1_query.py`).
5. **Switch consumers one at a time**, in the order agreed with their owners, each with its own check. Way back: point the consumer back to the old object.
6. **Parallel run**: keep both for the agreed window and tie out on every cycle.
7. **Contract**: remove the old object. Separate approval. Way back: restore from the snapshot taken just before.

Skip a step only if the proposal says why it does not apply.

### 4. Dry run

Run the plan's statements in the copy or development environment, or, without one, list the statements and the objects they touch and mark the plan `not verified`. Record what actually happened in `evidence-log.md`.

### 5. Approve

The proposal names who approved the plan, who approved each irreversible step, and who gave permission to run in each environment. Business decisions inside the change (what a NULL becomes, how a code is mapped, what the default is) are separate questions with options; apply none until answered.

### 6. Apply, one step at a time

For each step: back up or snapshot where the plan says so and state where; run it; run its check; record the result; only then start the next step. If a check fails, stop and use the step's way back; do not continue.

### 7. Verify

Tie out old against new using `playbooks/reconcile.md` and `scripts/waterfall.py`. The expected difference before the switch is zero within tolerance; if it is not, the plan is not done.

### 8. Record

Register each step: date, who approved, what changed, version affected, evidence, and the location of the snapshot. Keep the snapshot and the old object until the grace period in the Spec has passed.

## Not covered

- Choosing a migration or orchestration tool.
- Performance and storage cost of the change.
- Data contracts or governance processes in the user's organization; follow theirs and record the approvals.
