SELECT CASE WHEN promo IS NOT NULL THEN 'promo'
            WHEN partner IS NOT NULL THEN 'partner'
            ELSE 'direct' END AS channel,
       SUM(amount) AS revenue
FROM rentals GROUP BY 1
