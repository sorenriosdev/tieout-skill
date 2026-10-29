# Playbook: logic-review

Use to review a change to query logic, to read two versions of a query and say what differs, or to explain why a rewritten query might return different numbers when you have the code but not the data. It produces facts about the code, questions for the people who own the rules, and a test plan. It does not say whether a query is "right".

## Before you start

- Confirm the exact objects: which query, which two versions, which dialect (principle 9). If a change history exists, take both versions from it (`git show <rev>:<path>`, `git diff`) rather than asking the user to paste them.
- Declare the mode (`SKILL.md`, phase 0). Without data access this playbook is the whole job; with data access, continue into `reconcile.md` for the measured effects.
- The structural comparison uses `scripts/sql_review.py`, which needs sqlglot. If it is missing, the first sentence of your reply says so; you may still read the queries yourself, and everything you report is then labelled as read by you, not produced by the tool.

## Steps

1. **Read** both versions in full. Note the dialect and anything that looks engine-specific.
2. **Compare structurally**: `python scripts/sql_review.py diff <before> <after> --dialect <dialect>`. It lists differences in joins and join type, join conditions, filter conjuncts, aggregates, grouping, output columns and DISTINCT or LIMIT. Table aliases are ignored.
3. **Lint each version**: `python scripts/sql_review.py lint <file> --dialect <dialect>`. Each signal is tied to a hypothesis in `references/hypotheses.md`. Signals are things worth testing, not defects: say so.
4. **Describe each difference in plain words**: what rows can enter or leave, what happens to rows with NULL, whether the grain changes, whether values are rounded or cast differently. State it as a fact about the code ("the new query drops rows where `type` is NULL"), and the effect on the numbers only as unmeasured ("could change the total; not measured").
5. **Classify each difference** as technical equivalent, business rule or assumption (`SKILL.md`). A filter, a join type or a rounding policy that changes which rows or values count is usually a business rule: write the question with the options and the evidence, and no recommendation.
6. **Write the test plan**: for each difference, the catalog hypothesis and its test (`references/hypotheses.md`), in order of cost and power of the test, never of plausibility (principle 10). Put the SQL of each test in the reply, translated to the user's dialect with `scripts/u1_query.py` where it is the key decomposition.
7. **If you can run queries**: run the tests, measure each effect by neutralizing the causes one at a time, and close with `waterfall.py` as in `reconcile.md` phase 3.

## Reply shape

1. Differences found, as facts (a short table is fine).
2. Questions for the owners of each business rule.
3. Test plan: numbered, each with its SQL in a code block and the result that would confirm or rule it out.
4. The closing block.

## Not covered

- Judging performance, style or maintainability.
- Rewriting the query. If the user asks for a rewrite, treat it as a change: propose, approve, back up, apply.
- Semantic-layer measures and report filters (hypotheses H06 and H19): they need the report or model, not SQL. Use `clone-bi.md` and the connector notes in `references/bi-tools.md`.
