SELECT o.order_id, m.new_code
FROM orders o JOIN code_map m ON o.legacy_code = m.old_code;
