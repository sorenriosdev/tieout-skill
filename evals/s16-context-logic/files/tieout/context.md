# Context: gym membership revenue

**Written:** 2026-10-30 · **Last updated:** 2026-10-30

## What this is for
Monthly recurring revenue (MRR) reported to finance.

## Objects and what one row is
| Object | One row is | Key | Source |
|---|---|---|---|
| memberships (data/memberships.csv) | one membership | id | docs/data-dictionary.md |

## Terms
| Term | Means | Source |
|---|---|---|
| A | active, pays the full price | finance lead, 2026-09-01 |
| F | founder plan: pays the full price, closed to new sign-ups | finance lead, 2026-09-01 |
| P | paused: full price up to 10 paused days (inclusive), half price beyond | finance lead, 2026-09-01 |
| C | cancelled: counts until the cancellation takes effect | finance lead, 2026-09-01 |

## Reference
- **Which figure counts as correct:** mrr_v1.sql, approved by finance for the August close (source: finance lead, 2026-09-01)

## To confirm
- [assumption] mrr_v2.sql was meant to reproduce mrr_v1.sql - ask: finance lead
