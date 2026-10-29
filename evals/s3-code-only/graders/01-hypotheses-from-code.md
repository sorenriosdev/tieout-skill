---
type: llm
focus: last_message
---

PASS if the final response lists at least two hypotheses that point to concrete differences between the two queries (for example the INNER JOIN / is_active filter on dim_store, the `type <> 'VOID'` predicate dropping NULL types, or per-row rounding), in some order of priority. FAIL otherwise.
