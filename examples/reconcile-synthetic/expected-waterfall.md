# Expected waterfall

What `run_example.py` must reproduce. Each number can be checked by hand from `a.csv`, `b.csv` and `make_data.py`.

A is the sum of all lines in `a.csv`: 1475.7097 in sales lines and −47.75 in credit notes. B is the sum of `b.csv`: 1475.72 in rounded sales lines plus 555.46 in the two repeated lines.

H05: B keeps only `SALE`, so the three credit notes (−20.00, −15.50, −12.25) are missing. Removing them raises B relative to A by 47.75.

H13: lines D005/1 (250.33) and D008/1 (305.13) appear twice in B. Together they add 555.46.

The residual is what remains: B rounds each sales line to 2 decimals. Five lines round up by 0.0050 and three round down by 0.0049, for a net +0.0103. That is within the tolerance from `spec.md`: max(0.05, 0.0001 × 1427.9597) = 0.14279597. The residual is reported, not attributed to H16, because it is already within tolerance and the Spec only asks for the total to tie out.

| Step | Description | Amount | Evidence |
|---|---|---|---|
| A | Reference total | 1427.9597 | |
| H05 | B keeps only SALE: credit notes missing | +47.7500 | catalog test H05 |
| H13 | Lines repeated in B's source | +555.4600 | catalog test H13 on B |
| r | Residual (unexplained) | +0.0103 | |
| B | Candidate total | 2031.1800 | |

- Δ = B − A = +603.2203
- Σ effects = +603.2100
- r = Δ − Σ effects = +0.0103
- Tolerance = max(ε_abs, ε_rel·|A|) = max(0.05, 0.0001·1427.9597) = 0.14279597
- **Result: CLOSED**: |r| = 0.0103 <= 0.14279597

Both open questions in `spec.md` stay pending: whether credit notes count, and whether the repeated lines are real duplicates, are business decisions. Closing the waterfall explains the difference; it does not decide which side is right.
