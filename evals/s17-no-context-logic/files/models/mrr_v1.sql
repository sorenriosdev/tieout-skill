SELECT SUM(CASE
    WHEN status IN ('A', 'F') THEN price
    WHEN status = 'P' AND paused_days <= 10 THEN price
    WHEN status = 'P' THEN price * 0.5
    WHEN status = 'C' AND cancel_date > DATE '2026-09-30' THEN price
    ELSE 0
  END) AS mrr
FROM memberships
