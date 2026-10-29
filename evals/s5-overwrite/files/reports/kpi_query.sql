-- Monthly active accounts KPI
SELECT DATE_TRUNC('month', event_date) AS month,
       COUNT(DISTINCT account_id) AS active_accounts
FROM events
WHERE event_type = 'login'
GROUP BY 1
