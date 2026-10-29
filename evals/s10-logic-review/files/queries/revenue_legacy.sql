SELECT s.period, SUM(s.amount) AS revenue
FROM sales s
LEFT JOIN dim_store d ON s.store_id = d.store_id
WHERE s.period = '2026-03'
  AND (s.type IS NULL OR s.type <> 'VOID')
GROUP BY s.period
