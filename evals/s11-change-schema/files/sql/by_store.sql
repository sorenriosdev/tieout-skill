SELECT o.store_id, SUM(o.amount) AS revenue
FROM orders o JOIN stores s ON o.store_id = s.store_id
GROUP BY o.store_id;
