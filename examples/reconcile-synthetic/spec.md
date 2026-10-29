# Spec: synthetic sales tie-out

**Case:** example-001 · **Written:** 2026-10-25 · **Last updated:** 2026-10-25

This page defines what "equal" means for this case. Nothing is compared, changed or closed until it is filled in and agreed. All data in this example is synthetic.

## What we compare

| | A (reference) | B (candidate) |
|---|---|---|
| System | Legacy engine (here: `a.csv`) | New engine (here: `b.csv`) |
| Object (query, table, report, page) | Sales lines | Sales lines |
| Version or date of the object | 2026-10-25 extract | 2026-10-25 extract |
| Owner | Example data team | Example data team |

## What one row is

- **Grain:** one row is one document line
- **Key:** `k` (document) and `line`; the U1 test runs at document level (`k`)

## The measure

| | A | B |
|---|---|---|
| Name | `m` | `m` |
| Definition (in words) | Net amount of the line, credit notes negative | Net amount of the line, credit notes negative |
| Unit and currency | Currency units, 4 decimals | Currency units, 2 decimals |

## Scope

- **Period:** 2026-01 to 2026-03
- **Filters applied on both sides:** none
- **Cut-off date and time:** 2026-10-25 00:00

## When it counts as equal

- **Absolute tolerance (ε_abs):** 0.05
- **Relative tolerance (ε_rel):** 0.0001
- **What must tie out:** total only

A difference is accepted when |residual| ≤ max(ε_abs, ε_rel × |A|).

## Who decides

| Kind of decision | Approver (name or role) |
|---|---|
| Measure definitions | Finance lead (example) |
| Filters and record types | Finance lead (example) |
| Calendar and cut-off | Data owner (example) |
| Mappings between codes | Data owner (example) |
| Permission to change files or systems | Data owner (example) |

## Open questions

| # | Question | Asked to | Date | Answer |
|---|---|---|---|---|
| 1 | Should credit notes count in B, as they do in A? (H05) | Finance lead | 2026-10-25 | pending |
| 2 | Are the repeated lines in B's source real duplicates? (H13) | Data owner | 2026-10-25 | pending |
