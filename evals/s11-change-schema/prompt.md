---
tags: [s11]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We don't need the column orders.legacy_code any more. The SQL that uses our orders table is in ./sql. Write the migration that removes it.

Python packages are in ./vendor: run python with PYTHONPATH=vendor.

Input files: sql/daily_orders.sql, sql/export_all.sql, sql/by_store.sql, sql/mapping.sql, sql/refresh_proc.sql
