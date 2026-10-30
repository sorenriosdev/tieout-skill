---
type: regex
target: { source: file, path: models/channel_new.sql }
pattern: "WHEN partner IS NOT NULL THEN 'partner'\\s+WHEN promo IS NOT NULL THEN 'promo'"
flags: i
---
