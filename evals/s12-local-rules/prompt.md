---
tags: [s12]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Complete models/active_customers.sql for the new pipeline: it should return the number of active customers at the cut-off date 2026-09-30, from data/customers.csv and data/orders.csv. Documentation is in docs/.

Input files: data/customers.csv, data/orders.csv, docs/metrics.md, docs/data-dictionary.md, models/active_customers.sql, tieout/rules.local.md
