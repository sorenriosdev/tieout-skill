# Proposal <NNN>: <short title>

**Case:** <case-id> · **Written:** <date> · **Status:** proposed | approved | rejected | superseded
**Supersedes:** <proposal number, if any> · **Superseded by:** <proposal number, if any>

## What and why

- **Object to change:** <file, query, table, report, and its current version>
- **Finding it addresses:** <link to findings.md entry>
- **Kind of change:** technical equivalent | business rule | assumption

## The change

Before:

```
<current text or logic>
```

After:

```
<proposed text or logic>
```

## If this is a business rule: the question

<The question, in plain words.>

| Option | What it means | Evidence | Label |
|---|---|---|---|
| A | | | |
| B | | | |

Only the approver chooses. Nothing is applied while this is open.

## Expected result

- **Expected difference after the change:** <number> in <measure>
- **Compared against:** base <A total from the Spec>, tolerance max(ε_abs, ε_rel × |base|) from the Spec
- **How it will be measured:** <query or ladder rung>

## Way back

- **Backup will be at:** <path>
- **To revert:** <steps>

## Approval

| | Who | Date |
|---|---|---|
| Rule approved by (business rules only) | | |
| Permission to apply given by | | |

## Result (after applying)

- **Applied on:** <date> · **Backup at:** <path>
- **Actual difference:** <number> · **Expected vs actual:** MATCH | MISMATCH (waterfall.py compare output in evidence-log entry <n>)
