---
tags: [s10]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Queries queries/revenue_legacy.sql and queries/revenue_new.sql should both give March revenue. The new one returns 1198300 and the old one 1240500. I can't give you database access. What differs between them and how do we find out why?

Python packages are in ./vendor: run python with PYTHONPATH=vendor.

Input files: queries/revenue_legacy.sql, queries/revenue_new.sql
