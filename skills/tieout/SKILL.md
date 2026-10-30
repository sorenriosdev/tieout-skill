---
name: tieout
description: Change-safety method for data work. Any change to a SQL query, data model, schema, pipeline, report or dashboard is made with dated evidence, explicit approval and a way back. Its central check is tying out figures between two versions of the same thing (engine migration, logic refactor, metric-definition change, audit) - it measures the gap, localizes it with a ladder and tested hypotheses, and closes only when a script shows the residual is within the agreed tolerance. Use it whenever numbers between two systems, reports or query versions do not match, including read-only investigation where nothing will be changed; to reconcile or tie out figures, migrate SQL between engines, review query logic, change a KPI definition, clone or edit a BI report, or edit a query, model or report others rely on, even if nobody says "reconcile". It never decides business rules - it turns them into questions for a named approver and applies the project's approved rules from tieout/rules.local.md.
license: MIT
compatibility: Bundled scripts need Python 3.11+. sqlglot is needed for dialect work and duckdb for local tests; the skill detects what is missing and declares a reduced mode instead of doing that work by hand.
metadata:
  author: sorenriosdev
  status: draft
---

# tieout

A method for changing data logic safely. You produce evidence, ask for decisions, and keep a way back. You do not decide business rules, estimate business impact, or prescribe solutions.

Paths in this file are relative to the folder that contains this `SKILL.md`. Reply and write in the user's language; templates are in `assets/templates/en/` and `assets/templates/es/` (translate the English one for any other language).

## Step 1: tool gate

If the work needs a tool you do not have, the **first sentence of your reply** names the tool and what is therefore unverified, before any deliverable. Check when the task involves SQL dialect work (`python scripts/check_capabilities.py --require sqlglot`), running queries (a database client or connector), or a BI tool (its connector). Then stop, or continue in a reduced mode you name. Never do a tool's job by hand without saying so first; a hand-made translation is an `[assumption]`, delivered with the check that would verify it, never described as ready to run.

## Context and state (read once, do not rediscover)

- If `tieout/context.md` exists, read it once, for every weight. Its lines are `[user data: <source>]`; a line with no source is an `[assumption]`. Do not ask what it answers.
- If it is missing and the work is **full** or the objects are unfamiliar, ask for what exists (data dictionary, schema, docs, a sample query) and draft it from `assets/templates/en/context.md`: one cited line per fact, inferences under "To confirm" as `[assumption]`. With nothing to attach, ask at most four things: purpose, what one row is, the reference figure, categories assigned in priority order. Read-only: draft it in the reply, no file.
- Spend few turns: run independent reads and commands in the same turn, do not re-read what you wrote, write case files once per group (the Spec once agreed; evidence and findings together), and quote only the key lines of long outputs.
- In a full case `session.md` is also the state (verified, ruled out, next step); a new session starts there.

## Step 2: pick the weight

Effort should match the risk. Choose one, say which in one line, and move up if the work turns out to need it.

| Weight | Use it when | What you write |
|---|---|---|
| **light** | One object, and the user stated the exact change or already approved it. No business-rule choice is open. Nobody asked to compare two versions. | A backup, the change, one row in `tieout/decision-register.md`. Nothing else. |
| **decision** | A rule has two or more plausible readings, or the choice belongs to someone else. | One proposal in `tieout/proposals/NNN-<slug>.md`. Do not touch the object, not even with a comment. |
| **full** | Figures differ between two versions, or the work is a reconciliation, migration or audit. | The case folder and the full cycle below. |

**light, step by step:**
Do not run `check_capabilities.py` or read templates for a light change.

1. Confirm the exact object. If the request could mean more than one, ask first.
2. Confirm every table, column, measure or field the change uses exists and holds data (principle 11), or label it `[assumption]` with the query that checks it.
3. Copy the file to `tieout/backups/<name>.<timestamp>` before any edit, and say the path.
4. Make the smallest change that does what was asked.
5. Check what you can (run it, or at least parse it). If you can run it, record the totals before and after. If a proposal states an expected difference, measure the actual one and run `python scripts/waterfall.py compare ...`; do not compare by hand.
6. Append one row to `tieout/decision-register.md`. If the file is absent, create it with the header `| # | Date | Decision | Decided by | What changed | Version affected | Evidence | Replaces |` and a separator row.
7. If step 2 or 4 shows a rule with two readings, stop and switch to **decision**. If the change should move a figure that someone relies on and a comparison is possible, offer **full**.

Light never closes a case. Closing means the Spec's tolerance was met, which needs phase 7 and `waterfall.py`.

## Step 3: the closing block

End every reply that touched or analyzed an object with these four lines. The reply must stand on its own: someone who never opens `tieout/` gets the answer, the evidence labels, the queries to run and the open questions from the reply itself. The files are the record; the reply is the delivery.

```
Backup: <path, or "none: nothing overwritten">
Checked: <what, and how>
Not checked: <what, and why>
Pending: <decision or data, and who it waits for>
```

## Read-only deployments

If you have no write tool, or the user or operator said not to write, create no files and no backups: nothing is overwritten, so say "Backup: none: read-only". Everything the files would have held goes in the reply: mode, evidence labels, queries to run, open questions and the closing block. Business rules from `tieout/rules.local.md` are read and applied as usual. Rules, labels and the tool gate apply unchanged; only the output channel changes.

## Principles (always on)

Details, reasons and checks: `references/core-principles.md`. Read it in full for a **full** case; light and decision work can rely on the list below.

1. Read first; report the current state before changing anything.
2. Keep fact, decided rule and assumption apart; label each (`references/evidence-labels.md`).
3. A rule with two readings gets a question with options and evidence, never a silent choice.
4. Record each decision: date, who, what changed, which version.
5. Back up before any edit to an existing file, comments included; say where.
6. Never say it works without checking; say what was and was not checked.
7. Do not publish or create objects in a source system without explicit permission.
8. Do not collide with a tool that saves its own files: ask for a save, edit only what that tool allows, ask for the reload, re-read before a second edit (`references/bi-tools.md`).
9. Confirm the exact object when a request is ambiguous.
10. No cause is "likely" without a test. Untested hypotheses are ordered by cost and power of their test, not by plausibility.
11. Confirm a table, column, measure or field exists and holds data before using it or before switching a source.
12. Before any hypothesis about data quality, trace the compared figure or field on both sides to its source and compare the paths; hypotheses are only for what remains once the paths are equal (`playbooks/trace.md`).

## Full cycle

### Phase 0: capabilities and mode

1. Run `python scripts/check_capabilities.py` and keep its output in `session.md`.
2. Ask what access exists if the user has not said. Declare one mode in a line:
   - `code-only`: you can read and edit queries but cannot run them. Every causal claim is `not verified`. The reply has this shape: (1) the differences between the queries, stated as facts about the code, with effects only as "could change the total; not measured"; (2) the questions for rule owners; (3) the tests in order of cost and power, **each with its SQL in a code block in the reply**: a pointer to a file is not delivery; (4) the closing block. Ask the business questions without saying which answer you expect: "probably a bug" and "probably intended" are both untested leans. In this mode the reply is the deliverable and the record: create no `tieout/` files unless the user asks to keep one, and then the file is a copy of the reply. For two query versions, `python scripts/sql_review.py diff A.sql B.sql` lists the structural differences (needs sqlglot).
   - `one-system`: you can run queries on one side; the other side's figures are `[user data: source, date]`.
   - `both`: you can run both sides; the full ladder applies.
3. If the work involves a BI tool, list the tools you can call and ask which BI tool is used and whether its connector is connected (`references/bi-tools.md`).
4. Apply the tool gate (step 1) if anything is missing.

### Phases and gates

Do not start a phase without the artifact of the previous one. If the user asks to skip ahead, name the missing artifact and the risk, and wait.

| Phase | What happens | Artifact that opens the next phase |
|---|---|---|
| 0 Capabilities | Mode, available and missing tools | `session.md` |
| 1 Spec | What "equal" means: objects A and B, grain, keys, measure, period, filters, currency, cut-off date, tolerances ε_abs and ε_rel, who approves which kind of rule | `spec.md` |
| 2 Baseline | Ladder rungs L1 to L3, dated | entries in `evidence-log.md` |
| 3 Localize | Ladder L0 to L6 and the hypothesis catalog | `findings.md` with measured effects, waterfall and residual |
| 4 Propose | A proposal with the expected difference written down as a number | `proposals/NNN-<slug>.md` |
| 5 Approve | Human gate | approver, date and permission to apply recorded |
| 6 Apply | Backup, then the smallest reversible change | change applied and backup path stated |
| 7 Verify | Re-run the ladder; compare expected and actual difference with `scripts/waterfall.py compare` | close only if they match |
| 8 Record | Decision, evidence and affected version | row in `decision-register.md` |

In `code-only` mode, phases 0 to 3 produce no files by default: the reply carries the mode, the objects, the differences, the tests and the open questions.

Tolerances come from the Spec, never from you. Without them, nothing can close.

## Classify every proposed change

- **Technical equivalent** (dialect translation, refactor with no change in meaning): needs an equivalence test within the Spec's tolerance and a register row. No business approver, but writing to the user's files or systems still needs their permission (principle 7).
- **Business rule** (which definition, filter, calendar, mapping or treatment is correct): needs a named approver. Write the question with options and evidence; apply neither.
- **Assumption**: anything nobody confirmed. Stays pending, never applied.

A proposal has a status: `proposed`, `approved`, `rejected` or `superseded`. Keep superseded versions.

## Scripts (arithmetic and translation are never done by hand)

- `python scripts/waterfall.py close ...`: Δ = B − A as measured effects plus residual; exit 1 means the case is open.
- `python scripts/waterfall.py compare ...`: expected against actual difference after a change.
- `python scripts/u1_query.py ...`: key decomposition (L4, L5) for a dialect.
- `python scripts/check_capabilities.py [--require sqlglot]`: libraries and CLIs present.
- `python scripts/sql_review.py lint|diff ...`: structural signals and differences in SQL, tied to catalog hypotheses.
- `python scripts/transpile_sql.py ...`: dialect translation with a report of what to check.
- `python scripts/bi_fields.py pbir|model|twb ...`: fields a BI report references, checked against its model; Power Query steps, relationships and filter-context measures of a model.
- `python scripts/schema_impact.py ...`: which SQL files and Power BI reports reference a table or column, before you change or drop it.


## Case folder

Under the user's project: `tieout/decision-register.md`, `tieout/backups/`, `tieout/proposals/`, `tieout/rules.local.md` (the user's approved rules; read it, never write it), `tieout/context.md` (what the objects are; built from files the user attaches, stays in their project) and, for a full case, `tieout/<case-id>/` with `session.md`, `spec.md`, `evidence-log.md`, `findings.md`. If `rules.local.md` exists, its rules count as `[decided by <who>, <date>]`; a rule without approver or date is an `[assumption]`. An approved rule settles its question: apply it and do not reopen it. A conflicting rule with no approver is listed as pending and does not block the work.

## Where to go next

| Situation | Read |
|---|---|
| A figure or breakdown differs from a reference (a dashboard that is right, another report), or data is missing between source and report | `playbooks/trace.md` first, then `playbooks/reconcile.md` |
| Figures differ between two versions | `playbooks/reconcile.md` |
| Running or recording the ladder | `references/ladder.md` |
| Looking for a cause | `references/hypotheses.md` (symptom index, section 3) |
| Something outside the case's scope | `references/detection-flags.md`: flag and ask; do not fix |
| BI tool, report files or connectors | `references/bi-tools.md` |
| Reviewing a logic change, or comparing two query versions without data | `playbooks/logic-review.md` |
| Moving SQL between engines | `playbooks/migrate-sql.md` |
| Cloning or checking a BI report (Power BI PBIR, Tableau) | `playbooks/clone-bi.md` |
| Changing a schema (add, rename, retype, drop, move data) | `playbooks/change-schema.md` |
| Which adapters exist and what to do without them | `references/adapters.md` |

## Stop and ask when

- The object to change is ambiguous.
- A rule has more than one plausible reading.
- The Spec lacks tolerances, keys or a cut-off date.
- A tool that saves its own files has the project open and you have not asked for a save.
- You would publish, create objects in a source system, or overwrite without a backup.
