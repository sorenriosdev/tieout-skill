# Evidence labels

Every figure, cause and rule you report carries exactly one label. The reader should never have to guess whether something was measured, decided or supposed.

| Label | Use it for | Must include |
|---|---|---|
| `[verified: <how>, <when>]` | Something you ran or inspected yourself | The query, script or file that shows it, and the date (and time if data may change during the day) |
| `[decided by <who>, <date>]` | A business rule or a permission given by a named person | The person's name or role as the user stated it, and the date |
| `[user data: <source>, <date>]` | A figure the user handed you that you could not reproduce | Where it came from (report, export, message) and the date it refers to or was captured |
| `[assumption]` | Anything nobody has confirmed | Nothing else, but say what would turn it into one of the labels above |

## Examples

- Total revenue in A for 2026-03 is 1,204.50 `[verified: L1 query in evidence-log entry 3, 2026-10-25]`
- Credit notes count as negative sales `[decided by finance lead, 2026-10-24]`
- B shows 1,198.00 for 2026-03 `[user data: exported dashboard screenshot, captured 2026-10-24]`
- The candidate engine truncates timestamps in UTC `[assumption]`: confirm by running H17 on both sides.

## Hypothesis status

In `findings.md`, each hypothesis from `hypotheses.md` has a status, separate from the labels above:

- `not verified`: no test was run (always the case in `code-only` mode).
- `confirmed`: the test ran and confirmed; the measured effect is recorded.
- `ruled out`: the test ran and ruled it out.
- `ambiguous`: the test ran and the result does not decide; go down one rung of the ladder.

A `confirmed` hypothesis still needs its effect measured before it enters the waterfall.
