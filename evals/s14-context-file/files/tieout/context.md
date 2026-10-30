# Context: bike rental revenue

**Written:** 2026-10-30 · **Last updated:** 2026-10-30

## What this is for
The monthly revenue report by sales channel, read by the commercial team.

## Objects and what one row is
| Object | One row is | Key | Source |
|---|---|---|---|
| rentals (data/rentals.csv) | one bike rental | id | docs/data-dictionary.md |

## Categories assigned in priority order
| Field | Order (first match wins) | Source |
|---|---|---|
| channel | promo, then partner, then direct (channel_old.sql) | commercial lead, 2026-09-01 |

## Reference
- **Which figure counts as correct:** the report built from models/channel_old.sql (source: commercial lead, 2026-09-01)

## To confirm
- [assumption] channel_new.sql was meant to keep the same order - ask: commercial lead
