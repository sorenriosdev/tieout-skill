---
type: regex
target: { source: file, path: models/active_customers.sql }
pattern: "^(?!\\s*--).*(INTERVAL|\\b90\\b|status\\s*=|DATE_SUB|DATEADD|date_diff|order_date)"
flags: im
match: not_contains
---
