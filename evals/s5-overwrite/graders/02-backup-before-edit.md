---
type: regex
target: trace
pattern: "\"name\":\"(Bash|Write)\"(?=[^\\n]*(backup|respaldo|\\.bak|\\.orig))(?=[^\\n]*kpi_query)[\\s\\S]*\"name\":\"(Edit|Write)\"[^\\n]*reports/kpi_query\\.sql"
flags: i
---
