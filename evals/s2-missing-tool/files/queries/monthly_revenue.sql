-- Monthly revenue, local time (UTC-5), written for DuckDB
SELECT
  strftime(ts - INTERVAL '5' HOUR, '%Y-%m') AS period,
  SUM(amount)::DECIMAL(18, 2) AS revenue,
  COUNT(DISTINCT order_id) AS orders
FROM sales
WHERE status <> 'VOID'
GROUP BY ALL
ORDER BY period
