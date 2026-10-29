# Localization ladder

The ladder narrows a difference from "the totals differ" to "this expression produces the different value". Go down one rung at a time and record each rung's result before going further: if the difference disappears when you go down, the defect was on the rung above, and you can only know that if the rung above is on record.

| Rung | Question | What to do | Record |
|---|---|---|---|
| L0 Contract | Are we comparing the same thing? | Check the Spec: measure definition, filters, period, currency, cut-off date | Any mismatch goes to the Spec as an open question, not to the findings |
| L0b Path | Do both sides use the same field, table and source path? | Trace the compared field on both sides (`playbooks/trace.md`) | The two paths, layer by layer; any difference ends the search |
| L1 Total | How much do they differ in total? | One figure per system | A, B, Δ = B − A, capture date and time |
| L2 Period | In which periods? | Total per period on each side | Table period / A / B / Δ |
| L3 Dimension | In which classification? | Total per dimension, one dimension at a time | Table per dimension; note where Δ concentrates |
| L4 Key | What exists in one system and not the other? | Test U1 (`scripts/u1_query.py`) | `solo_en_a`, `solo_en_b` |
| L5 Row | Which key is in both with a different value? | Test U1, then list the top keys by absolute difference | `dif_en_comunes` and the listed keys |
| L6 Column or expression | Which expression produces the different value? | Isolate the expression and compute it separately on both sides | The expression, both values, the difference |

## Rules

- Each rung's result goes into `evidence-log.md` with a label from `evidence-labels.md` and a capture date. Sources change between days; an undated figure cannot be compared later.
- Phase 2 (baseline) covers L1 to L3. Phase 3 (localize) continues from where the baseline points.
- Phase 7 (verify) repeats the same rungs with the same queries, so before and after are comparable.
- U1 must satisfy `dif_total = -solo_en_a + solo_en_b + dif_en_comunes`. If it does not, the query is wrong (null keys are the usual cause); fix it before reading the result.
- A total that ties out does not prove the breakdown ties out: effects can offset. Keep going down while the Spec asks for the breakdown to tie out.

## By mode

- `both`: run every rung yourself.
- `one-system`: run your side; the other side's figures are `[user data: <source>, <date>]`. Ask for them at the grain of the rung (per period, per dimension). A total alone cannot localize anything.
- `code-only`: write the query for each rung, for both sides, and put them in the reply. Record every rung as pending until someone runs them. Order hypotheses by the cost and power of their test; never by how plausible they seem.
