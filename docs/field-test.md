# Trying tieout on real work

*[Leer en español](field-test.es.md)*

This guide is for trying the skill on your own data work and measuring whether it helps, without exposing anything. It assumes Claude Code; for other agents see the note at the end.

## Before you start

1. **Install from the `next` branch**, not `main`: `claude plugin marketplace add sorenriosdev/tieout-skill#next`, then `claude plugin install tieout@tieout-skill`. If the repository is private, the machine needs git credentials that work non-interactively (for GitHub, `gh auth login` and `gh auth setup-git`).
2. **Work on copies.** Point the agent at a clone of the project or a development environment. The skill asks for permission before writing, but do not rely on that alone while you evaluate it.
3. **Read-only first.** Start with the tasks below in the order given; the first three change nothing.
4. **Treat outputs as internal.** The inventories and findings name your real tables, fields and values. Do not paste them into public issues. Before publishing anything you wrote while testing, check it against your own list of terms that must not leave the company.

## Five tasks, in order

| # | Task | Why this one | Changes anything? |
|---|---|---|---|
| 1 | Give it two versions of one real query (no database access) and ask why the numbers differ | Tests `code-only` analysis: does it list the real differences, give runnable tests in the reply, and avoid naming a cause? | No |
| 2 | Run `python skills/tieout/scripts/bi_fields.py pbir <your>.Report` yourself on a real PBIP (or `twb` on a workbook) | Tests the inventory against a real report, which this repository has not seen | No |
| 3 | Ask it to tie out two real figures you already know the answer to | Tests `reconcile` against a case where you can grade the result | No (it works on copies you give it) |
| 4 | A small approved change to a copy of one query | Tests the light path: backup, change, register row, honest "Not checked" | Yes, on the copy |
| 5 | Translate one query between your two engines | Tests `migrate-sql`: does it flag what differs and ask for the equivalence test? | Writes a new file only |

## What to record for each task

Write one row per task, once with the skill and once without (same prompt, fresh session):

| Measure | How |
|---|---|
| Correct findings | Number of real differences or defects it reported that you confirm |
| False findings | Number it reported that are not real |
| Missed | Real ones you know about that it did not report |
| Decisions it left to you that were yours | Count the good questions |
| Decisions it took that were not its to take | Any silent choice of a rule |
| Unverified claims | Statements without a label, or "works" without a check |
| Cost and time | `/cost` in the session; wall-clock minutes |
| Would you ship it? | Yes / with edits / no |

The scenarios in `evals/` show the expected behavior on synthetic data. They measured roughly twice the cost of working without the skill on small tasks, with better process (backups, labels, deferred decisions), not better detection of the underlying defects. Check whether that holds on your work.

## What would count as a failure

- It changes a file without a backup, or publishes anything.
- It picks a business rule for you.
- It presents a hand-made translation as ready.
- It names a cause as likely without a test.
- The inventory script reports a field as missing that exists, or misses one that does not: send the (anonymized) structure so the parser can be fixed.
- It takes ten steps for a one-line change.

## Other agents

The skill is a standard `SKILL.md` folder (`skills/tieout/`) and should load in agents that read Agent Skills. For agents that only read a rules file, `adapters/AGENTS.md` carries the rules without the method. Neither has been tested outside Claude Code.
