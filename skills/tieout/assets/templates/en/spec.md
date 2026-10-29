# Spec: <case name>

**Case:** <case-id> · **Written:** <date> · **Last updated:** <date>

This page defines what "equal" means for this case. Nothing is compared, changed or closed until it is filled in and agreed.

## What we compare

| | A (reference) | B (candidate) |
|---|---|---|
| System | | |
| Object (query, table, report, page) | | |
| Version or date of the object | | |
| Owner | | |

## What one row is

- **Grain:** <one row is one ...>
- **Key:** <column(s) that identify a row>

## The measure

| | A | B |
|---|---|---|
| Name | | |
| Definition (in words) | | |
| Unit and currency | | |

## Scope

- **Period:** <from> to <to>
- **Filters applied on both sides:** <...>
- **Cut-off date and time:** <the moment both sides are read>

## When it counts as equal

- **Absolute tolerance (ε_abs):** <amount>
- **Relative tolerance (ε_rel):** <fraction of A, e.g. 0.0001 = 0.01 %>
- **What must tie out:** total only / total and each period / total, each period and each <dimension>

A difference is accepted when |residual| ≤ max(ε_abs, ε_rel × |A|).

## Who decides

| Kind of decision | Approver (name or role) |
|---|---|
| Measure definitions | |
| Filters and record types | |
| Calendar and cut-off | |
| Mappings between codes | |
| Permission to change files or systems | |

## Open questions

| # | Question | Asked to | Date | Answer |
|---|---|---|---|---|
| 1 | | | | |
