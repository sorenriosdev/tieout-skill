# tieout: change-safety rules for data work

Compact rules for agents that read a rules file but not skills. They apply when the task changes or compares SQL, data models, schemas, pipelines or BI reports. For anything else, ignore this file. The full method (modes, phases, playbooks, scripts, templates) is in `skills/tieout/`; if the agent can read files, point it at `skills/tieout/SKILL.md`.

Reply and write in the user's language.

## Before you start

- If the task needs a tool you do not have (SQL translation needs sqlglot, running queries needs a database client or connector, BI work needs the BI tool's connector), the **first sentence of your reply** names it and says what is therefore unverified. Then stop, or continue in a reduced mode you name. Never do the tool's job by hand without saying so.
- Pick the weight and say which: **light** (one object, exact change already stated or approved, no open business-rule choice: back up, change, add one row to a decision register), **decision** (a rule has two plausible readings or the choice is someone else's: write the question with options and evidence, change nothing), or **full** (figures differ between two versions, or a migration or audit: follow the phases in `skills/tieout/SKILL.md`).

## Principles

1. Read first; report the current state before changing anything.
2. Keep fact, decided rule and assumption apart; label each (`skills/tieout/references/evidence-labels.md`).
3. A rule with two readings gets a question with options and evidence, never a silent choice.
4. Record each decision: date, who, what changed, which version.
5. Back up before any edit to an existing file, comments included; say where.
6. Never say it works without checking; say what was and was not checked.
7. Do not publish or create objects in a source system without explicit permission.
8. Do not collide with a tool that saves its own files: ask for a save, edit only what that tool allows, ask for the reload, re-read before a second edit (`skills/tieout/references/bi-tools.md`).
9. Confirm the exact object when a request is ambiguous.
10. No cause is "likely" without a test. Untested hypotheses are ordered by cost and power of their test, not by plausibility.
11. Confirm a table, column, measure or field exists and holds data before using it or before switching a source.
12. Before any hypothesis about data quality, trace the compared figure or field on both sides to its source and compare the paths; hypotheses are only for what remains once the paths are equal (`playbooks/trace.md`).

## End every reply with

```
Backup: <path, or "none: nothing overwritten">
Checked: <what, and how>
Not checked: <what, and why>
Pending: <decision or data, and who it waits for>
```

The reply must stand on its own: queries to run, evidence labels and open questions are in the reply, not only in files.
