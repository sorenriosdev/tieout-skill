#!/usr/bin/env python3
"""Close or compare a tie-out with exact decimal arithmetic.

close: explain Δ = B − A as the sum of measured effects plus a residual r, and
check |r| <= max(eps_abs, eps_rel * |A|).

  python waterfall.py close --a 1000 --b 1050 --effects effects.csv \
      --eps-abs 0.01 --eps-rel 0.0001

  effects.csv has a header and one row per confirmed hypothesis:
    id,description,effect,evidence
    H13,Duplicated lines in B,30.00,evidence-log entry 7

  An effects file with only the header is valid: then r = Δ.

compare: after a change, check the actual difference against the expected one
written in the proposal before applying it.

  python waterfall.py compare --expected -12.50 --actual -12.48 \
      --base 1000 --eps-abs 0.01 --eps-rel 0.0001

  The tolerance is max(eps_abs, eps_rel * |base|); use the reference total A
  from the Spec as base.

Numbers use '.' as the decimal separator and no thousands separator
("1204.50", not "1,204.50"): a comma means different things in different
locales, so it is rejected rather than guessed.

Tolerances must come from the Spec. They are required arguments on purpose.

Exit codes: 0 closed / match, 1 open / mismatch, 2 invalid input.
"""
import argparse
import csv
import datetime
import re
import sys
from decimal import Decimal

NUMBER = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def fail(msg):
    print(f"waterfall: {msg}", file=sys.stderr)
    sys.exit(2)


def num(text, what):
    text = str(text).strip()
    if not NUMBER.match(text):
        fail(f"{what}: '{text}' is not a plain number (use '.' for decimals, no thousands separator)")
    return Decimal(text)


def tolerance(eps_abs, eps_rel, base):
    if eps_abs < 0 or eps_rel < 0:
        fail("tolerances cannot be negative")
    return max(eps_abs, eps_rel * abs(base))


def fmt(d):
    return f"{d:+f}" if d else "0"


def stamp():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def read_effects(path):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            header = reader.fieldnames or []
    except OSError as e:
        fail(f"cannot read effects file: {e}")
    if [h.strip() for h in header] != ["id", "description", "effect", "evidence"]:
        fail("effects file header must be exactly: id,description,effect,evidence")
    seen, effects = set(), []
    for n, row in enumerate(rows, 2):
        hid = (row.get("id") or "").strip()
        if not hid:
            fail(f"effects file line {n}: empty id")
        if hid in seen:
            fail(f"effects file line {n}: duplicate id {hid}")
        seen.add(hid)
        effects.append((hid, (row.get("description") or "").strip(),
                        num(row.get("effect"), f"effects file line {n}"),
                        (row.get("evidence") or "").strip()))
    return effects


def close(args):
    a, b = num(args.a, "--a"), num(args.b, "--b")
    eps_abs, eps_rel = num(args.eps_abs, "--eps-abs"), num(args.eps_rel, "--eps-rel")
    effects = read_effects(args.effects)
    delta = b - a
    explained = sum((e for _, _, e, _ in effects), Decimal(0))
    r = delta - explained
    tol = tolerance(eps_abs, eps_rel, a)
    closed = abs(r) <= tol

    out = [f"## Waterfall [verified: waterfall.py close, {stamp()}]", "",
           "| Step | Description | Amount | Evidence |", "|---|---|---|---|",
           f"| A | Reference total | {a} | |"]
    out += [f"| {hid} | {desc} | {fmt(e)} | {ev} |" for hid, desc, e, ev in effects]
    out += [f"| r | Residual (unexplained) | {fmt(r)} | |",
            f"| B | Candidate total | {b} | |", "",
            f"- Δ = B − A = {fmt(delta)}",
            f"- Σ effects = {fmt(explained)}",
            f"- r = Δ − Σ effects = {fmt(r)}",
            f"- Tolerance = max(ε_abs, ε_rel·|A|) = max({eps_abs}, {eps_rel}·{abs(a)}) = {tol}",
            f"- **Result: {'CLOSED' if closed else 'OPEN'}**: |r| = {abs(r)} {'<=' if closed else '>'} {tol}"]
    print("\n".join(out))
    return 0 if closed else 1


def compare(args):
    expected, actual = num(args.expected, "--expected"), num(args.actual, "--actual")
    base = num(args.base, "--base")
    eps_abs, eps_rel = num(args.eps_abs, "--eps-abs"), num(args.eps_rel, "--eps-rel")
    gap = actual - expected
    tol = tolerance(eps_abs, eps_rel, base)
    match = abs(gap) <= tol
    out = [f"## Expected vs actual [verified: waterfall.py compare, {stamp()}]", "",
           f"- Expected difference (from the proposal): {fmt(expected)}",
           f"- Actual difference (measured after the change): {fmt(actual)}",
           f"- Gap = actual − expected = {fmt(gap)}",
           f"- Tolerance = max(ε_abs, ε_rel·|base|) = max({eps_abs}, {eps_rel}·{abs(base)}) = {tol}",
           f"- **Result: {'MATCH: the case may close' if match else 'MISMATCH: do not close'}**: "
           f"|gap| = {abs(gap)} {'<=' if match else '>'} {tol}"]
    print("\n".join(out))
    return 0 if match else 1


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to a legacy code page
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("close", help="waterfall and residual check")
    c.add_argument("--a", required=True, help="reference total A")
    c.add_argument("--b", required=True, help="candidate total B")
    c.add_argument("--effects", required=True, help="CSV: id,description,effect,evidence")
    p = sub.add_parser("compare", help="expected vs actual difference after a change")
    p.add_argument("--expected", required=True)
    p.add_argument("--actual", required=True)
    p.add_argument("--base", required=True, help="reference total used for the relative tolerance")
    for s in (c, p):
        s.add_argument("--eps-abs", required=True, help="absolute tolerance from the Spec")
        s.add_argument("--eps-rel", required=True, help="relative tolerance from the Spec")
    args = ap.parse_args()
    sys.exit(close(args) if args.cmd == "close" else compare(args))


if __name__ == "__main__":
    main()
