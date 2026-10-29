---
type: regex
target: { source: file, path: models/active_customers.sql }
pattern: "^(?!\\s*--).*status\\s*=\\s*'A'"
flags: im
match: not_contains
---
