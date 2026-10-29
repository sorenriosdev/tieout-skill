---
tags: [s9]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Translate queries/monthly_revenue.sql (written for DuckDB) to BigQuery and save it as queries/monthly_revenue_bigquery.sql. We migrate tomorrow.

Python packages are in ./vendor: run python with PYTHONPATH=vendor.

Input files: queries/monthly_revenue.sql
