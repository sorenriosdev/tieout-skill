# Proposal 001: remove repeated lines from B

**Case:** case-004 · **Written:** 2026-10-23 · **Status:** approved

## What and why

- **Object to change:** models/b.sql (version of 2026-10-20)
- **Finding it addresses:** H13 confirmed on 2026-10-23: lines D005/1 and D008/1 appear twice in B's source
- **Kind of change:** business rule (the repeated lines were confirmed as real duplicates)

## The change

Before:

```
SELECT *
FROM read_csv('data/b_raw.csv', header = true)
```

After:

```
SELECT DISTINCT *
FROM read_csv('data/b_raw.csv', header = true)
```

## Expected result

- **Expected difference after the change:** -555.46 in B's total (the two repeated lines: 250.33 + 305.13)
- **Compared against:** base 1427.9597 (A total in the Spec), tolerance max(0.05, 0.0001 × |base|) from the Spec
- **How it will be measured:** B total after the change minus B total before the change

## Way back

- **Backup will be at:** tieout/case-004/backups/
- **To revert:** restore models/b.sql from the backup

## Approval

| | Who | Date |
|---|---|---|
| Rule approved by (business rules only) | Data owner | 2026-10-24 |
| Permission to apply given by | Data owner | 2026-10-24 |
