SELECT order_id, legacy_code, amount
FROM orders
WHERE order_date = CURRENT_DATE;
