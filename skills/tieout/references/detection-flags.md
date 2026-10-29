# Detection flags

While working on a case you will notice things outside its scope. Four kinds are worth flagging. For each one: **record it, label it, ask one question, and do not fix it.** No impact estimates, no redesign proposals unless the user asks for them. A flag is an observation for the owner, not a task you start.

| Flag | What it looks like | Related hypotheses |
|---|---|---|
| Phantom metric | The same name (column, measure, KPI) is computed with different logic in different places | H02 |
| Structural leak | Columns, keys or dimensions that are mostly empty, orphaned or unused, yet still loaded, joined or computed | H09, H10 |
| Compute hotspot | A query or model pattern likely to be expensive at volume: full scans where a filter was intended, joins that multiply rows, heavy row-by-row calculated columns | H08 |
| Behavioral anomaly | Values that should be impossible in the domain: negative balances where none can exist, overlapping validity windows, timestamps in the future, documents with no lines | H11, H14 |

## How to record a flag

Add it to `findings.md` under a "Flags" heading:

```
- Flag: <kind>
  Where: <object, file, query, line>
  Seen: <what you observed> <label from evidence-labels.md>
  Question for <owner, if known>: <one question>
```

If you only suspect it (for example in `code-only` mode), label it `[assumption]` and give the query that would confirm it.
