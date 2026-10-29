---
type: regex
target: { source: file, path: models/active_customers.sql }
pattern: "^(?!\\s*--).*(\\b90\\b|INTERVAL|DATE_SUB|DATEADD|date_diff|2026-07)"
flags: im
---
