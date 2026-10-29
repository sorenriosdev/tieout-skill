---
type: regex
target: { source: file, path: queries/store_revenue.sql }
pattern: "^(?!\\s*--).*segment_name"
flags: im
match: not_contains
---
