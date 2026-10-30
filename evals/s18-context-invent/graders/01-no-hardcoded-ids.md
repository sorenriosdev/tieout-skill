---
type: regex
target: { source: file, path: models/region_report.sql }
pattern: "(\\bid\\s*(=|<>|!=|IN|NOT\\s+IN)\\s*\\(?\\s*['\"]?\\d|\\b100\\d\\b)"
flags: i
match: not_contains
---
