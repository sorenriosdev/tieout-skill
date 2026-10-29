SELECT s.period, SUM(ROUND(s.amount, 0)) AS revenue
FROM sales s
JOIN dim_store d ON s.store_id = d.store_id AND d.is_active = TRUE
WHERE s.period = '2026-03'
  AND s.type <> 'VOID'
GROUP BY s.period
