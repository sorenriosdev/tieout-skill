# Synthetic reconcile example

A small, fully synthetic case that runs phases 2 and 3 of the reconcile playbook end to end.

- `a.csv`: reference A, 11 sales lines over three periods.
- `b.csv`: candidate B, built from A by `make_data.py` with three injected defects (H05 type filter, H13 repeated lines, H16 per-row rounding).
- `spec.md`: the filled-in Spec, including the tolerances the script reads.
- `expected-waterfall.md`: the result to reproduce, with each number explained.

Run it (needs `duckdb` and `sqlglot`):

```
python examples/reconcile-synthetic/run_example.py
```

It prints the ladder (L1 to L3), U1, the catalog tests, the effects measured by neutralizing each cause in order, and the waterfall. It exits 0 only if the waterfall matches `expected-waterfall.md` and the residual is within tolerance.
