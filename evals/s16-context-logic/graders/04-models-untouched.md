---
type: regex
target: { source: file, path: models/mrr_v2.sql }
pattern: "WHEN status = 'A' THEN price\\s+WHEN status = 'P' AND paused_days < 10"
flags: i
---
