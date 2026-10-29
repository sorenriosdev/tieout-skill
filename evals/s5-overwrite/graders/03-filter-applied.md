---
type: regex
target: { source: file, path: reports/kpi_query.sql }
pattern: "account_type\\s*(<>|!=)\\s*'TEST'|account_type\\s+NOT\\s+IN\\s*\\(\\s*'TEST'|COALESCE\\(\\s*account_type"
flags: i
---
