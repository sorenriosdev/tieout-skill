SELECT region, SUM(revenue) AS revenue
FROM accounts
GROUP BY region
