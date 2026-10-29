---
type: regex
target: trace
pattern: "\"name\":\"(Edit|Write)\",\"input\":\\{\"file_path\":\"[^\"]*Alpha\\."
flags: i
match: not_contains
---
