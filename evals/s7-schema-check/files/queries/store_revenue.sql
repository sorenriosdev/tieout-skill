SELECT s.store_id,
       SUM(s.amount) AS revenue
FROM sales s
GROUP BY s.store_id
