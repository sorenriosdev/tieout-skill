---
tags: [s14]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

The monthly report built from models/channel_old.sql and the one built from models/channel_new.sql give a different revenue per channel. Find out why. Data is in data/rentals.csv. Do not change the models.

Input files: data/rentals.csv, models/channel_old.sql, models/channel_new.sql, docs/data-dictionary.md, tieout/context.md
