<h1 align="center">
  <img src="assets/banner.svg" width="680" height="200" alt="tieout: evidence, approval and a way back for every data change">
</h1>

<p align="center"><a href="README.es.md">Leer en español</a></p>

**tieout is a method for changing data work with evidence, packaged as an agent skill.** It covers editing queries, models, schemas and reports, reviewing logic, finding where two versions disagree, and moving queries between SQL engines.

When an agent does that work, tieout makes it show its evidence, back up before it edits, and ask a named person before it decides a business rule. Its central check is the tie-out: showing that two versions of the same figure agree, or explaining exactly why they don't, with a script and not with a hunch.

It follows the [Agent Skills](https://agentskills.io) format, so agents that read it can use it (only Claude Code has been tested), and it does not depend on a particular database or BI tool.

> [!WARNING]
> Early draft, tested on synthetic data and in Claude Code only. See [Status](#status).

## What a reply looks like

Every reply that touches or analyzes an object ends with the same four lines. Example, after an approved change that excludes TEST accounts from a monthly KPI query (hence the different totals):

```
Backup:      tieout/backups/kpi_query.sql.20261030T0915
Checked:     query parses; totals before and after: 1,204.50 and 1,171.00
Not checked: that account_type exists in the warehouse table [assumption]
Pending:     Finance lead to confirm that TEST accounts never count
```

## When to use it

- "These two numbers don't match"
- "Translate this query to BigQuery"
- "I copied this report for another team; check it before I publish"
- "I'm changing how this metric is defined"

Invoke it with `/tieout:tieout` and the task. To investigate without changing anything, say so: `/tieout:tieout read-only, create or change no file: why do these two queries return different totals?`

## Install

**Claude Code**
```
claude plugin marketplace add sorenriosdev/tieout-skill
claude plugin install tieout@tieout-skill
```

**Codex**: see [docs/codex.md](docs/codex.md). **Other agents**: copy `skills/tieout/` into the agent's skills folder and ask for it by name. The scripts need Python 3.11 or later and `pip install sqlglot duckdb` for SQL work.

## How it works

Each task starts by picking a weight and saying which:

| Weight | When | What it writes |
|---|---|---|
| **light** | One object, and the change is stated or already approved | A backup, the change, one line in a decision log |
| **decision** | A rule has two readings, or the choice belongs to someone else | One proposal with the question and the options. Nothing is changed |
| **full** | Two versions disagree, or it is a reconciliation, migration or audit | Spec, baseline, find the gap, propose, approve, apply, verify, record |

A tie-out closes with Δ = B − A = Σ effects + residual. A is the reference figure and B the candidate. The effects are the differences you measured; the residual is what they leave unexplained, and it must fall inside a tolerance you agreed beforehand (how much difference counts as equal). A script checks it; the agent does not. Rules you have approved go in `tieout/rules.local.md`; the skill applies them, and treats a rule without an approver as a question.

| Playbook (`skills/tieout/playbooks/`) | For |
|---|---|
| `reconcile` | Tying out two figures that should match |
| `trace` | Finding which field or step makes a figure differ from a reference |
| `logic-review` | Comparing two versions of a query, with or without database access |
| `migrate-sql` | Moving queries between SQL engines |
| `clone-bi` | Copying or checking a report (optional adapters for Power BI and Tableau files) |
| `change-schema` | Adding, renaming, retyping or dropping a table or column |

## What it does not do

- It does not decide business rules: when a rule has two readings, it writes the question with options and evidence and waits for a named approver.
- It does not estimate financial impact or prescribe solutions.
- It does not do by hand what a tool should do: if sqlglot or a database client is missing, it says so and stops or declares a reduced mode.

## Status

Thirteen synthetic scenarios, two or three runs each: average score **0.90 with tieout and 0.56 without**, at about 1.8 times the cost. It helped most where an agent would skip a step (naming a missing tool, backing up, closing with a script, asking instead of choosing a rule) and not at all on a missing-column check. The skill and the scenarios were tuned together, so read it as a first signal: [results](evals/RESULTS-2026-10-26.md).

Not done yet:
- Any run on real Power BI, Tableau or warehouse data (those adapters are optional and were tested on hand-built files)
- SQL on engines other than DuckDB, and agents other than Claude Code
- CI is not passing yet

The catalog of checks (22 common causes of a mismatch, most with a SQL test) comes from one person's experience. Running it on your own work and reporting what it misses is the fastest way to improve it: see [docs/field-test.md](docs/field-test.md). Open items: [ROADMAP.md](ROADMAP.md).

## License

[MIT](LICENSE), © 2026 sorenriosdev.
