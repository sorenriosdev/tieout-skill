SELECT CASE WHEN partner IS NOT NULL THEN 'partner'
            WHEN promo IS NOT NULL THEN 'promo'
            ELSE 'direct' END AS channel,
       SUM(amount) AS revenue
FROM rentals GROUP BY 1
