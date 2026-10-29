# Playbook: trace

Use when a figure or a breakdown does not match a reference (a report that is known to be right, another report, another system) and you have to find out why, or when data that should be there is missing somewhere between the source and what people see. It works one layer at a time and rules culprits out with evidence before it builds theories.

The mistake this playbook prevents: a long chain of hypotheses about data quality, joins and history, built before anyone checked that both sides compute the same field in the same way. Look at the fields first; theories come last.

It does not depend on any particular tool. The layers below exist in every stack that has a consumption layer (a BI or reporting tool, a notebook, an application), possibly a model or semantic layer, and a source (a warehouse, a lakehouse, a database, files). Where this page says "the tool", read whichever one you have.

## Where to start

Two directions are valid. Pick by what is cheaper to check and more likely to be decisive.

- **From the consumption layer backwards.** Start at what people see and ask how the tool consumes the data: what it applies on top of the query it sends (filters, joins, deduplication, conversions, calculations). Use this when the reference is a report people trust, or when the symptom appears only in the report.
- **From the source forwards.** Start at the source and query it directly. Use this when the discrepancy is between two queries or two systems, when the report simply displays the query result, or when the consumption layer is not accessible.

Depth of inspection is a cost decision too. When you do not yet know which part matters, read the whole definition of the model or report once (one pass is cheaper than many guesses). When you already know which field is involved, read only the part that feeds it.

## The order

1. **Say what is wrong, exactly.** Which figure, which dimension, which period, on which side, by how much. Does the total tie and only the breakdown differ, or does the total differ? Total ties and breakdown does not: the classification fields are the first suspects, not missing rows. Total differs: filters, dates, joins and lost rows.
2. **Find the reference** (the figure or element considered correct) and trace the exact path of the field it shows:

   `report element → field → model table or calculation → data-preparation steps → source query → source table → column`

   Do not assume which field it should use; read it. Do the same for the side that does not match.
3. **Compare the two paths, layer by layer**, in a table (see the template below). If any layer differs (a different column, a different table, a join on another key, a column taken from a dimension instead of from the fact), that is the lead. Say it, show the two paths, and stop searching for causes.
4. **Only if both paths are equal and the numbers still differ**, walk backwards through the layers below and rule each out. Only after that, use the hypothesis catalog.
5. **Change one thing**, the proven difference, and nothing else. Keep every column and piece of logic that is not part of the problem, even if it looks unused: it may feed something else. For queries joined with `UNION ALL`, compare the number, order and types of columns of a block before replacing it.
6. **Validate the total and the breakdown**, by every dimension that matters, not only the total.

## Walking back through the layers

Start at the symptom and go one layer back at a time. At each layer ask one question: **does the output of this layer equal what the layer above shows?** The first layer where the answer is no holds the cause.

| Layer | What can change the data here | How to check it cheaply |
|---|---|---|
| Report element | Element, page and report filters; selections saved in the report; hidden filters | Read the report definition, or ask the tool; compare with a plain table of the same field |
| Calculation | Measures or calculated fields that change filter context (removing, adding or overriding filters) | Evaluate it with and without filters; compare with the same logic in SQL |
| Model relationships | Inactive relationships, filtering in both directions, a relationship on a different key | Read the model definition, or ask the tool |
| Data-preparation steps | Steps that filter or remove rows, deduplicate, join (and with which kind), convert types (bad values become errors or nulls), depend on today's date, or limit a refresh window | List the steps; compare the row count before and after each step that can change it |
| Source query | Joins, filters, `UNION` blocks, the exact column chosen | Compare the two queries structurally; run each one alone |
| Source table or view | The data itself, its load date, its coverage | The coverage profile below |
| Upstream | Late or partial loads, reprocessing | Compare captures taken on different dates |

Do not skip the model and data-preparation layers on the grounds that the data "comes straight from the source": the tool applies its own steps to the query, and a figure can be lost there without any error.

## Coverage profile (run it on every layer you check)

For each table or layer that feeds the figure, record: row count, minimum and maximum of the date column, the list of distinct periods, and the count of distinct keys. If the report should show eight months and a table holds one, rows were lost before this layer or by a step in it. This is the quickest way to find a missing period, and it takes one query per layer.

## Hypotheses with grounds

A hypothesis is allowed only with: the observation it explains, the test that would confirm or rule it out, and what each outcome would mean. Order the tests by cost and power, not by plausibility (principle 10). Record evidence for and against; a hypothesis with no test is an `[assumption]`.

## Elimination table (put it in the reply)

| Layer | Question | Check done | Result | Verdict |
|---|---|---|---|---|
| Report element | Does a filter remove rows? | Read the element's filters | none stored on this field | ruled out |
| Data-preparation steps | Does a step drop the missing period? | Listed the steps | step 2 filters rows `[verified]` | culprit zone |
| Source query | | not checked | | pending |

Verdicts: `ruled out` (with the check), `culprit zone` (the first layer where the output stops matching), `pending` (not checked, and why).

## Limits on the search

Exploration without a stopping rule is how a task takes hours. Before searching, state the hypothesis you are testing and the check that decides it. After three consecutive checks that add no new information, stop widening: report the elimination table and name the artifact you are missing (the query behind the reference element, the model definition, access to run a count). Asking for it is the correct next step.

## Modes

- `code-only`: build both path tables from the files; every layer that needs a run is `pending` with its query in the reply.
- `one-system`: run the checks on your side; the other side's counts are `[user data: source, date]`.
- `both`: run the coverage profile and the layer checks yourself.

## Reply shape

1. The two paths, side by side, layer by layer.
2. The elimination table.
3. The proven difference, or the first layer that cannot be ruled out, and the next test with its SQL.
4. The single change proposed, and the logic that must stay untouched.
5. The closing block.

## Tools

For queries: `scripts/sql_review.py` (structural comparison), `scripts/schema_impact.py` (what else reads the same field), `scripts/u1_query.py`, `scripts/waterfall.py`. For the consumption and model layers there is no universal script: read the definition files if the tool stores them as text, or use a connector if one is available (`references/bi-tools.md`). `scripts/bi_fields.py` is an optional adapter for a few such formats; without it, do the same reading by hand and label what you read. After the change is proposed and approved, continue with `reconcile.md` phases 4 to 8.
