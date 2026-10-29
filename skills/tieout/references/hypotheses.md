# Catalog of reconciliation-gap hypotheses (draft v0)

**Status:** design draft. The SQL blocks marked as tests are verified in DuckDB on synthetic data (`tests/test_hypotheses.py`): each test must confirm on data with the defect and rule out on clean data. They have not been run on BigQuery, Databricks or any other engine; the agent must translate them to the engine's dialect with sqlglot and check the result before using it.

**Origin and limits:** this comes from the field experience of a single person. It still needs to be checked against other data engineers before it can be called complete (see section 7).

**Contents:** 1 How to use · 2 Ladder (operating procedure in `ladder.md`) · 3 Symptom index · 4 Test U1 · 5 Waterfall · 6 Hypotheses: H01 snapshot · H02 same label · H03 time window · H04 unit/currency · H05 type filter · H06 consumption-layer filters · H07 NULL predicates · H08 fan-out · H09 join loss · H10 key format · H11 dimension history · H12 grain · H13 source duplicates · H14 source changes · H15 NULL arithmetic · H16 rounding · H17 time zone · H18 strings · H19 semantic-layer context · H20 contaminated reference · H21 positional UNION · H22 non-determinism · 7 Not covered yet

---

## 1. What it is and how to use it

A hypothesis is a falsifiable claim about why a system A (reference) and a system B (candidate) give different figures. Each one has: signature (what you see), cause, reading (what to look at in the code), test, test power, and the human decision it implies.

Rules of use:

1. **Nothing is declared the culprit without an executed test.** In code-only mode, the hypothesis stays "not verified" and the agent hands over the test for someone with access to run.
2. **A test confirms or rules out.** If the result is ambiguous, say it is ambiguous and go down one rung of the ladder.
3. **Order:** cheap, high-power tests first; low-power tests only if the earlier ones do not close the gap. This is a testing order, not a ranking of probability: without data, do not call any hypothesis likely or unlikely.
4. **Confirming does not close the case.** Quantify the hypothesis's effect and recompute the residual (section 5).
5. **Hypotheses are not mutually exclusive and their effects can offset each other.** A total that ties out does not prove the breakdown ties out.
6. **The catalog detects; it does not decide.** If the fix involves a business rule, the agent writes a question with options and evidence, and the case stays pending until a named approver answers.

**SQL conventions.** `a` = reference, `b` = candidate. Columns: `k` key, `line` line within the key, `period` period as text `YYYY-MM`, `dim` classification dimension, `typ` record type, `m` measure, `ts` timestamp, `d` dimension or lookup table. Every test returns one row with `confirmed` (boolean) and `evidence` (amount or count). It runs on each system separately unless stated otherwise.

---

## 2. Localization ladder

| Rung | Question | What to do |
|---|---|---|
| L0 Contract | Are we comparing the same thing? | Measure definition, filters, period, currency, cut-off date |
| L1 Total | How much do they differ in total? | One figure per system, with capture date |
| L2 Period | In which periods? | Total per period |
| L3 Dimension | In which classification? | Total per dimension, one at a time |
| L4 Key | What exists in one system and not the other? | Test U1 (section 4) |
| L5 Row | Which key is in both with a different value? | Test U1 |
| L6 Column or expression | Which expression produces the different value? | Isolate the expression and compute it separately |

Rule: do not go down a rung without recording the result of the current one. If the difference disappears when going down, the defect was in the previous rung.

---

## 3. Symptom → hypothesis index

| What you see | Hypotheses to test first |
|---|---|
| Difference with a single sign in every period | H05, H06, H07, H09, H03 |
| Constant proportional difference (near-fixed ratio) | H04 |
| Difference only in recent periods | H01, H14, H03 |
| The total ties out but the breakdown by dimension does not | Trace the dimension's field on both sides first (`playbooks/trace.md`): H02 is a different field or definition under the same name. Then H08 + H09 offsetting, H18, H21 |
| A period or rows that should be there are missing in a report | Coverage profile per layer (`playbooks/trace.md`), then H03, H09, H14 |
| B is higher than A | H08, H11, H12, H13 |
| B is lower than A | H09, H05, H07, H10 |
| Difference of cents | H16, H15 |
| Difference on the first or last day of the period | H17, H03 |
| Ties out one day and not the next (or the other way round) | H14, H01, H22 |
| The reference matches neither side | H20, H06 |
| The result changes between runs without touching anything | H22, H14 |
| The report differs from its own query | H06, H19 |

These guide the order of the search; they are not proof.

---

## 4. Universal test U1: decomposition by key (L4 and L5)

Splits the total difference into three parts: keys only in A, keys only in B, and value difference on common keys. Output columns: `solo_en_a` (only in A), `solo_en_b` (only in B), `dif_en_comunes` (difference on common keys), `dif_total` (total difference).

```sql test:U1
WITH j AS (
  SELECT COALESCE(sa.k, sb.k) AS k, sa.m AS ma, sb.m AS mb
  FROM (SELECT k, SUM(m) AS m FROM a GROUP BY k) sa
  FULL OUTER JOIN (SELECT k, SUM(m) AS m FROM b GROUP BY k) sb ON sa.k = sb.k
)
SELECT
  SUM(CASE WHEN mb IS NULL THEN ma ELSE 0 END) AS solo_en_a,
  SUM(CASE WHEN ma IS NULL THEN mb ELSE 0 END) AS solo_en_b,
  SUM(CASE WHEN ma IS NOT NULL AND mb IS NOT NULL THEN mb - ma ELSE 0 END) AS dif_en_comunes,
  SUM(COALESCE(mb, 0)) - SUM(COALESCE(ma, 0)) AS dif_total
FROM j
```

Identity that must hold: `dif_total = -solo_en_a + solo_en_b + dif_en_comunes`. If it does not, the test is built wrong (for example, null keys).

---

## 5. Closing: waterfall

Let $\Delta = B - A$ be the total difference. The case closes when

$$\Delta = \sum_i e_i + r, \qquad |r| \le \max\left(\varepsilon_{abs},\ \varepsilon_{rel}\,|A|\right)$$

where each $e_i$ is the **measured** effect of a confirmed hypothesis, $r$ is the residual, and the tolerances come from the Spec (phase 1 of the skill), not from the agent. If $r$ exceeds the tolerance, the case stays open even if some hypotheses are confirmed.

---

## 6. Hypotheses

### H01. Different data cut-off (snapshot)
- **Signature:** the difference concentrates in the most recent periods and changes on reload.
- **Cause:** A and B were loaded at different times; one has rows the other does not yet have.
- **Reading:** last load date of each source; when the reference model was loaded.
- **Power:** high.

```sql test:H01
SELECT (x + y > 0) AS confirmed, x + y AS evidence
FROM (SELECT (SELECT COUNT(*) FROM b WHERE ts > (SELECT MAX(ts) FROM a)) AS x,
             (SELECT COUNT(*) FROM a WHERE ts > (SELECT MAX(ts) FROM b)) AS y) t
```

- **Confirms:** some system has rows after the other's maximum. **Rules out:** neither does.
- **Decision:** technical (set a common cut-off date in the Contract). If it cannot be set, it becomes a business decision.

### H02. Same label, different definition
- **Signature:** the breakdown does not tie out although the totals sometimes do; same column or metric name on both sides.
- **Cause:** the name is the same but the rule is not (a "family" column that is a different hierarchy in one group; an "active" metric with different criteria).
- **Reading:** extract each side's definition into a comparison table (expression, filters, group it applies to).
- **Power:** high, with cross-application.

```sql template
-- Apply A's definition to B's data, and B's definition to A's data.
-- If the figure converges when using the same definition, the cause is the definition, not the data.
SELECT <definition_of_A> FROM <table_of_B> WHERE <filters_of_A>
```

- **Decision:** business. Which definition prevails is decided neither by the agent nor by the data evidence.

### H03. Different time window
- **Signature:** periods that exist in one system and not the other; differences at the edges.
- **Cause:** different date ranges, fiscal calendar or partial periods.
- **Reading:** date filters of each query; inclusive or exclusive bounds.
- **Power:** high. Repeat at day level if the periods match.

```sql test:H03
SELECT COUNT(*) > 0 AS confirmed, COUNT(*) AS evidence
FROM (SELECT DISTINCT period FROM a) pa
FULL OUTER JOIN (SELECT DISTINCT period FROM b) pb ON pa.period = pb.period
WHERE pa.period IS NULL OR pb.period IS NULL
```

- **Decision:** technical if it is a misplaced bound; business if the calendar is a policy.

### H04. Currency, unit, taxes or scale
- **Signature:** the ratio B/A is almost constant across periods and different from 1 (for example, a tax included on one side, thousands against units, another currency at a fixed rate).
- **Cause:** a measure comes in another unit or with another tax treatment.
- **Reading:** definition of the measure, currency and exchange rate of each source.
- **Power:** medium (needs at least 3 periods; a constant ratio is a hint, not proof).

```sql test:H04
WITH sa AS (SELECT period, SUM(m) AS m FROM a GROUP BY period),
     sb AS (SELECT period, SUM(m) AS m FROM b GROUP BY period),
     r AS (SELECT CAST(sb.m AS DOUBLE) / NULLIF(CAST(sa.m AS DOUBLE), 0) AS ratio
           FROM sa JOIN sb ON sa.period = sb.period)
SELECT (COUNT(ratio) >= 3 AND MAX(ratio) - MIN(ratio) < 0.001 AND ABS(AVG(ratio) - 1) > 0.001) AS confirmed,
       AVG(ratio) AS evidence
FROM r
```

- **Decision:** business (which treatment is correct for the comparison).

### H05. Record-type filter too broad or too narrow
- **Signature:** single-sign difference; shows up when comparing the values of the type column in each system.
- **Cause:** a filter like `typ = 'SALE'` drops values the other system keeps (credit notes, voids, blanks), or the other way round.
- **Reading:** profile the column's values before filtering it: `SELECT typ, COUNT(*), SUM(m) FROM a GROUP BY typ`. Never filter by a type without first seeing which values exist.
- **Power:** high.

```sql test:H05
WITH sa AS (SELECT COALESCE(typ, '<NULL>') AS typ, SUM(m) AS m FROM a GROUP BY COALESCE(typ, '<NULL>')),
     sb AS (SELECT COALESCE(typ, '<NULL>') AS typ, SUM(m) AS m FROM b GROUP BY COALESCE(typ, '<NULL>'))
SELECT COUNT(*) > 0 AS confirmed,
       COALESCE(SUM(COALESCE(sa.m, 0) - COALESCE(sb.m, 0)), 0) AS evidence
FROM sa FULL OUTER JOIN sb ON sa.typ = sb.typ
WHERE sa.typ IS NULL OR sb.typ IS NULL
```

- **Decision:** business (which types count as a sale).

### H06. Filters in the consumption layer
- **Signature:** the report gives a different figure from its own raw query.
- **Cause:** visual, page or report filters; slicers with saved selections; filters inside measures; or values inherited from another context when cloning (title, currency, list of codes).
- **Reading:** inventory of every filter per visual and per page, including hidden ones.
- **Test (procedure, not SQL):** reproduce the visual's figure with the raw query and the same filters; the difference without filters is this hypothesis's effect.
- **Power:** high when the visual can be inspected; without access to the report it stays "not verified".
- **Decision:** technical if the filter comes from another context; business if it is intentional.

### H07. NULL in predicates
- **Signature:** B is lower; rows with the filter column NULL.
- **Cause:** `typ <> 'X'` and `NOT IN` silently drop NULLs; another engine or another way of writing it keeps them.
- **Reading:** predicates with `<>`, `!=`, `NOT IN` on nullable columns.
- **Power:** high as a measure of the mass at stake.

```sql test:H07
SELECT COUNT(*) > 0 AS confirmed, COALESCE(SUM(m), 0) AS evidence
FROM a
WHERE typ IS NULL
```

- **Confirms:** there is mass with the filter column NULL (the exact effect depends on how each query writes the predicate). **Rules out:** no NULL rows.
- **Decision:** business (do blanks count or not?).

### H08. Join fan-out
- **Signature:** B is higher; the difference appears after a join.
- **Cause:** the joined table is not unique on the join key (1:N), and the measure is repeated for every match.
- **Reading:** every join in the query: is the key unique on the joined side? Locate with `SELECT k, COUNT(*) FROM d GROUP BY k HAVING COUNT(*) > 1`.
- **Power:** high.

```sql test:H08
SELECT (despues <> antes) AS confirmed, despues - antes AS evidence
FROM (SELECT (SELECT SUM(m) FROM a) AS antes,
             (SELECT SUM(a.m) FROM a LEFT JOIN d ON a.k = d.k) AS despues) t
```

- **Decision:** mixed. Removing the fan-out is technical; choosing which of the duplicated rows is valid is business.

### H09. Join loss (INNER or unmatched key)
- **Signature:** B is lower; the total may tie out if another effect offsets it, but classifications are missing ("no channel", "no route").
- **Cause:** an `INNER JOIN` drops unmatched rows, or the key exists but denotes another level (the lookup stores stores and the fact table carries chains).
- **Reading:** type of each join and key coverage in the joined table.
- **Power:** high.

```sql test:H09
SELECT COUNT(*) > 0 AS confirmed, COALESCE(SUM(a.m), 0) AS evidence
FROM a LEFT JOIN d ON a.k = d.k
WHERE d.k IS NULL
```

- **Confirms:** there is mass with no match in the joined table (it is lost only if the join is INNER; check the query). **Rules out:** all mass has a match.
- **Watch out:** H08 and H09 can offset each other and leave a total that ties out.
- **Decision:** mixed. How to treat orphans ("show blank and report it" or assign a default value) is business.

### H10. Key with a different format or type
- **Signature:** B is lower or classifications are blank; the codes "look alike" but do not match.
- **Cause:** text with leading zeros against a number, spaces, upper case.
- **Reading:** types of the columns on each side of the join.
- **Power:** high.

```sql test:H10
SELECT COUNT(*) > 0 AS confirmed, COUNT(*) AS evidence
FROM a
WHERE NOT EXISTS (SELECT 1 FROM d WHERE CAST(d.k AS VARCHAR) = a.k)
  AND EXISTS (SELECT 1 FROM d WHERE d.k = TRY_CAST(a.k AS BIGINT))
```

- **Confirms:** there are keys that do not match as-is but do after normalizing. **Rules out:** none.
- **Decision:** technical, with one check: that normalizing does not merge entities that are actually different.

### H11. Dimension with history (validity)
- **Signature:** B is higher, or classification values that do not belong to the date.
- **Cause:** the lookup stores versions by validity and the join does not filter by date.
- **Reading:** validity columns (from, to, active) in the joined table.
- **Power:** high.

```sql test:H11
SELECT COUNT(*) > 0 AS confirmed, COUNT(*) AS evidence
FROM (SELECT k FROM d GROUP BY k HAVING COUNT(DISTINCT valid_from) > 1) x
```

- **Decision:** business (which version applies to which date).

### H12. Different aggregation grain
- **Signature:** the number of rows per key differs between systems; B higher if a header measure is repeated on every line.
- **Cause:** one system has documents and the other has lines, or levels are mixed.
- **Reading:** declared grain of each source and each query.
- **Power:** medium.

```sql test:H12
WITH sa AS (SELECT k, COUNT(*) AS n FROM a GROUP BY k),
     sb AS (SELECT k, COUNT(*) AS n FROM b GROUP BY k)
SELECT COUNT(*) > 0 AS confirmed, COUNT(*) AS evidence
FROM sa JOIN sb ON sa.k = sb.k
WHERE sa.n <> sb.n
```

- **Decision:** mixed.

### H13. Duplicates at the source or different deduplication
- **Signature:** B (or A) is higher; identical rows repeated in one of the base tables, before any join.
- **Cause:** the source repeats lines, or one system deduplicates and the other does not.
- **Reading:** declared natural keys; presence of `DISTINCT` or deduplication in any query.
- **Power:** high. Difference from H08: here the duplicate is already in the base table.

```sql test:H13
SELECT COALESCE(SUM(n - 1), 0) > 0 AS confirmed, COALESCE(SUM((n - 1) * m), 0) AS evidence
FROM (SELECT k, line, m, COUNT(*) AS n FROM a GROUP BY k, line, m HAVING COUNT(*) > 1) x
```

- **Watch out:** two identical rows can be legitimate. The test measures exposure; it does not prove the error.
- **Decision:** business (is it a real duplicate?).

### H14. The source changes over time
- **Signature:** the same system gives a different figure for the same closed period in two captures; duplicates that appear and disappear.
- **Cause:** reprocessing, late corrections, incomplete loads.
- **Reading:** load and correction history, if any.
- **Power:** high, but requires having saved captures. That is why the skill records every measurement with a date.

```sql test:H14
SELECT (t_new <> t_old) AS confirmed, t_new - t_old AS evidence
FROM (SELECT (SELECT SUM(m) FROM snap_new) AS t_new,
             (SELECT SUM(m) FROM snap_old) AS t_old) t
```

- **Decision:** process and business (agree on a cut-off date and on who corrects). The agent reports; it does not fix the source.

### H15. NULL in measures and expressions
- **Signature:** small or per-row differences; B lower.
- **Cause:** `m1 + m2` is NULL if either is, and the whole row is lost from the sum; averages and ratios change depending on how NULL and division by zero are handled.
- **Reading:** arithmetic expressions without `COALESCE`, unprotected divisions.
- **Power:** high.

```sql test:H15
SELECT (d <> 0) AS confirmed, d AS evidence
FROM (SELECT SUM(COALESCE(m1, 0) + COALESCE(m2, 0)) - COALESCE(SUM(m1 + m2), 0) AS d FROM a) x
```

- **Decision:** mixed (is NULL zero, or is the data missing?).

### H16. Types and rounding
- **Signature:** differences of cents that grow with volume.
- **Cause:** rounding per row against rounding the total, decimal against float, truncation against rounding.
- **Reading:** where `ROUND` or a numeric cast happens on each side.
- **Power:** high as a measure of exposure (set the decimals to each case's policy).

```sql test:H16
SELECT (r_each <> r_total) AS confirmed, r_total - r_each AS evidence
FROM (SELECT SUM(ROUND(m, 2)) AS r_each, ROUND(SUM(m), 2) AS r_total FROM a) x
```

- **Decision:** mixed (rounding policy is usually an accounting matter).

### H17. Time zone and date truncation
- **Signature:** differences on the first or last day of the period.
- **Cause:** one side assigns the period in UTC and the other in local time; each engine truncates by session time zone or by UTC depending on the type and the function (check the engine's documentation).
- **Reading:** type of the date column and truncation function on each side.
- **Power:** medium. It measures exposure (how much mass changes period when the boundary moves), not which side uses which zone.

```sql test:H17
SELECT COUNT(*) > 0 AS confirmed, COALESCE(SUM(m), 0) AS evidence
FROM a
WHERE EXTRACT(MONTH FROM ts) <> EXTRACT(MONTH FROM ts - INTERVAL '5' HOUR)
```

- **Parameter:** the 5-hour offset is an example; use the real zone's offset.
- **Dialect warning:** sqlglot leaves the literal `INTERVAL '5' HOUR` as-is when transpiling to BigQuery, which expects `INTERVAL 5 HOUR`. Check this literal by hand on each engine before running. It is the only case found so far; the transpilation check is syntactic only and there may be others.
- **Decision:** business (which zone defines the close).

### H18. Strings: spaces, case, collation
- **Signature:** the same category appears split across several rows; the groups do not match between systems.
- **Cause:** `'Lima'`, `'lima '` and `'LIMA'` group differently depending on collation or prior cleaning.
- **Reading:** text cleaning on each side.
- **Power:** high.

```sql test:H18
SELECT COUNT(*) > 0 AS confirmed, COUNT(*) AS evidence
FROM (SELECT UPPER(TRIM(dim)) AS n FROM a GROUP BY UPPER(TRIM(dim)) HAVING COUNT(DISTINCT dim) > 1) x
```

- **Decision:** technical.

### H19. Measure with filter context (semantic layer)
- **Signature:** the model's measure does not match the same logic computed in SQL.
- **Cause:** functions that alter context (`ALL`, `ALLEXCEPT`), inactive relationships, bidirectional cross-filtering, row-by-row calculated columns.
- **Reading:** the measure's code and the model's relationships.
- **Test (procedure, not SQL):** evaluate the measure with and without filters (for example with the model's query tool) and compare it with its SQL equivalent.
- **Power:** high with access to the model; otherwise "not verified".
- **Decision:** mixed.

### H20. The reference is contaminated
- **Signature:** the reference R matches neither A nor B, or matches one side and not the other.
- **Cause:** R was loaded earlier (old values), has its own filter, or a period comes as zero because of a filter rather than the data.
- **Reading:** when and with which filters R was loaded.
- **Power:** high. Do not assume the reference is the truth.

```sql test:H20
WITH sa AS (SELECT period, SUM(m) AS m FROM a GROUP BY period),
     sb AS (SELECT period, SUM(m) AS m FROM b GROUP BY period),
     sr AS (SELECT period, SUM(m) AS m FROM r GROUP BY period)
SELECT COUNT(*) > 0 AS confirmed, COUNT(*) AS evidence
FROM sa JOIN sb ON sa.period = sb.period JOIN sr ON sa.period = sr.period
WHERE ABS(sa.m - sb.m) < 0.005 AND ABS(sr.m - sa.m) >= 0.005
```

- **Parameter:** `0.005` is an example; use the Spec's tolerance.
- **Decision:** technical (reload or fix R) or R's owner's.

### H21. Positional UNION
- **Signature:** values in one column that belong to another; unexpected categories in a dimension.
- **Cause:** `UNION ALL` pairs columns by position, not by name; if two columns have compatible types the engine does not warn.
- **Reading:** compare each branch's `SELECT`, position by position (a script does this better than the agent reading).
- **Power:** low in SQL (disjoint-domain heuristic); high with the script.

```sql test:H21
SELECT (COUNT(*) = 0) AS confirmed, COUNT(*) AS evidence
FROM (SELECT DISTINCT c FROM u1) x JOIN (SELECT DISTINCT c FROM u2) y ON x.c = y.c
```

- **Confirms:** the domains of a column that should be shared are disjoint between branches. **Rules out:** they overlap. Apply only to categorical columns that share a domain.
- **Decision:** technical.

### H22. Non-deterministic selection
- **Signature:** the result changes between runs or between engines without the data changing.
- **Cause:** `ROW_NUMBER` or deduplication with an ordering that admits ties; `LIMIT` without a total order.
- **Reading:** window functions, `DISTINCT ON`, `QUALIFY`, `LIMIT` and their `ORDER BY`.
- **Power:** high.

```sql test:H22
SELECT COUNT(*) > 0 AS confirmed, COUNT(*) AS evidence
FROM (SELECT k, ts FROM a GROUP BY k, ts HAVING COUNT(*) > 1) x
```

- **Parameter:** `k` is the partition and `ts` the ordering column used in the real query.
- **Decision:** technical (add a deterministic tie-breaker), unless choosing which row is valid is a business rule.

---

## 7. What this catalog does not cover yet

- Data quality without a comparison (profiling, nulls, orphans): that is another playbook.
- Performance and cost.
- The visuals layer and report files (referenced fields, hidden pages, publishing binding): covered with scripts, not SQL tests.
- Third-party validation: the 22 hypotheses come from one person's experience. Before publishing it as a "catalog", check them with at least two other engineers and add the missing ones.
- Semantic equivalence across dialects (`STRUCT`, `ARRAY`, date functions, NULL handling): relies on sqlglot and a separate document.
