#!/usr/bin/env python3
"""Translate a SQL file between dialects with sqlglot and list what to check.

  python transpile_sql.py FILE --from duckdb --to bigquery [--out FILE]

Prints the translated SQL, then a report:
  - unsupported constructs sqlglot warned about while generating
  - a parse-back check of the output in the target dialect
  - behaviors the two dialects handle differently according to sqlglot's own
    dialect model, for the constructs this query actually uses (NULL ordering,
    integer division, NULL in CONCAT, NULL in LEAST/GREATEST, array index base)
  - literals sqlglot is known to leave in the source form (see H17 in
    references/hypotheses.md)

What this does NOT do: run the query on either engine. A translation that
parses is not a translation that returns the same numbers. The equivalence test
is to run both versions on the same data and tie out the results with
playbooks/reconcile.md. The behavior list comes from sqlglot's model of each
dialect (version printed in the report), not from the engines' documentation:
confirm the ones that matter to you.

Without sqlglot the script stops. It never translates by hand.
Exit codes: 0 translated (read the report), 1 translated but sqlglot reported
unsupported constructs or the parse-back failed, 2 invalid input or missing sqlglot.
"""
import argparse
import io
import logging
import pathlib
import sys

try:
    import sqlglot
    from sqlglot import exp
    from sqlglot.dialects.dialect import Dialect
except ImportError:
    print("transpile_sql: sqlglot is not installed. Install it (pip install sqlglot) or declare a reduced mode; "
          "a hand translation must be labelled [assumption] and never presented as tool output.", file=sys.stderr)
    sys.exit(2)


def fail(msg):
    print(f"transpile_sql: {msg}", file=sys.stderr)
    sys.exit(2)


def dialect(name):
    try:
        return Dialect.get_or_raise(name)
    except ValueError as e:
        fail(str(e))


def behavior_notes(tree, src, dst):
    """Differences sqlglot models between the dialects, for constructs present in this query."""
    notes = []
    s, d = dialect(src), dialect(dst)
    sname, dname = src, dst

    has_order = any(isinstance(o, exp.Ordered) for o in tree.find_all(exp.Ordered))
    if has_order and getattr(s, "NULL_ORDERING", None) != getattr(d, "NULL_ORDERING", None):
        notes.append(("ORDER BY",
                      f"Default NULL ordering differs: {sname} is modeled as `{s.NULL_ORDERING}`, {dname} as `{d.NULL_ORDERING}`. "
                      "Rows with NULL sort keys can move. sqlglot may add NULLS FIRST/LAST to the output to keep the source "
                      "behavior: check that it did, and that this is what you want."))
    if any(isinstance(n, exp.Div) for n in tree.find_all(exp.Div)) and \
            getattr(s, "TYPED_DIVISION", None) != getattr(d, "TYPED_DIVISION", None):
        notes.append(("division with `/`",
                      f"Typed division differs: {sname} TYPED_DIVISION={s.TYPED_DIVISION}, {dname} TYPED_DIVISION={d.TYPED_DIVISION}. "
                      "With integer operands one engine may return an integer, the other a decimal."))
    if any(isinstance(n, exp.Div) for n in tree.find_all(exp.Div)) and \
            getattr(s, "SAFE_DIVISION", None) != getattr(d, "SAFE_DIVISION", None):
        notes.append(("division by zero",
                      f"SAFE_DIVISION differs: {sname}={s.SAFE_DIVISION}, {dname}={d.SAFE_DIVISION}. "
                      "One engine may return NULL where the other raises an error."))
    if any(isinstance(n, (exp.Concat, exp.DPipe)) for n in tree.walk()) and \
            getattr(s, "CONCAT_COALESCE", None) != getattr(d, "CONCAT_COALESCE", None):
        notes.append(("string concatenation",
                      f"NULL handling in concatenation differs: {sname} CONCAT_COALESCE={s.CONCAT_COALESCE}, "
                      f"{dname} CONCAT_COALESCE={d.CONCAT_COALESCE}. A NULL input may give NULL in one engine and a string in the other."))
    if any(isinstance(n, (exp.Least, exp.Greatest)) for n in tree.walk()) and \
            getattr(s, "LEAST_GREATEST_IGNORES_NULLS", None) != getattr(d, "LEAST_GREATEST_IGNORES_NULLS", None):
        notes.append(("LEAST / GREATEST",
                      f"NULL handling differs: {sname} ignores NULLs={s.LEAST_GREATEST_IGNORES_NULLS}, "
                      f"{dname} ignores NULLs={d.LEAST_GREATEST_IGNORES_NULLS}."))
    if any(isinstance(n, exp.Bracket) for n in tree.walk()) and getattr(s, "INDEX_OFFSET", None) != getattr(d, "INDEX_OFFSET", None):
        notes.append(("array or bracket index",
                      f"Index base differs: {sname}={s.INDEX_OFFSET}, {dname}={d.INDEX_OFFSET}. sqlglot adjusts literal indexes; check computed ones."))
    if any(isinstance(n, (exp.DateTrunc, exp.TimestampTrunc, exp.AtTimeZone, exp.Extract, exp.CurrentDate, exp.CurrentTimestamp))
           for n in tree.walk()):
        notes.append(("date and time functions",
                      "Truncation, EXTRACT and CURRENT_* depend on the session time zone and on the column type (DATE, "
                      "TIMESTAMP with or without zone) in each engine. Test the period boundaries (hypothesis H17)."))
    if any(isinstance(n, exp.RowNumber) for n in tree.walk()) or any(isinstance(n, exp.Limit) for n in tree.walk()):
        notes.append(("row selection",
                      "ROW_NUMBER and LIMIT choose rows by ORDER BY. If the ordering admits ties, the chosen row can differ "
                      "between engines (hypothesis H22)."))
    if any(isinstance(n, exp.Cast) and n.args.get("to") is not None and n.args["to"].this in
           (exp.DataType.Type.FLOAT, exp.DataType.Type.DOUBLE, exp.DataType.Type.DECIMAL) for n in tree.walk()):
        notes.append(("numeric casts", "Decimal and floating-point types round and overflow differently between engines (hypothesis H16)."))
    return notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--from", dest="src", required=True, help="source dialect (sqlglot name)")
    ap.add_argument("--to", dest="dst", required=True, help="target dialect (sqlglot name)")
    ap.add_argument("--out", help="also write the translated SQL to this new file (never overwrites)")
    args = ap.parse_args()
    dialect(args.src), dialect(args.dst)

    path = pathlib.Path(args.file)
    if not path.is_file():
        fail(f"not a file: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        trees = [t for t in sqlglot.parse(text, read=args.src) if t is not None]
    except sqlglot.errors.ParseError as e:
        fail(f"cannot parse {path} as {args.src}: {e}")
    if not trees:
        fail(f"{path} has no SQL statement")

    # Capture sqlglot's warnings about unsupported constructs instead of losing them.
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("sqlglot")
    logger.addHandler(handler)
    old_level = logger.level
    logger.setLevel(logging.WARNING)
    try:
        statements = [t.sql(dialect=args.dst, pretty=True, unsupported_level=sqlglot.ErrorLevel.WARN) for t in trees]
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
    unsupported = [l.strip() for l in stream.getvalue().splitlines() if l.strip()]
    output = ";\n\n".join(statements) + ";"

    opaque = [t for t in trees if isinstance(t, exp.Command) or t.find(exp.Command) is not None]
    if opaque:
        unsupported.append(f"{len(opaque)} statement(s) were read only as opaque commands (procedural code or syntax "
                           "sqlglot does not model): they are copied, not translated; translate them by hand")
    problems = bool(unsupported)
    parse_back = "ok"
    try:
        sqlglot.parse(output, read=args.dst)
    except sqlglot.errors.ParseError as e:
        parse_back = f"FAILED: {e}"
        problems = True

    if args.out:
        out_path = pathlib.Path(args.out)
        if out_path.exists():
            fail(f"{out_path} already exists; refusing to overwrite (back it up or choose another name)")
        out_path.write_text(output + "\n", encoding="utf-8")

    print(f"-- Translated by transpile_sql.py from {args.src} to {args.dst}, sqlglot {sqlglot.__version__}.")
    print("-- Syntax only: not executed on either engine. Tie out results with playbooks/reconcile.md.")
    print(output)
    print("\n/* ---------------- REPORT ----------------")
    print(f"Parse-back in {args.dst}: {parse_back}")
    print("Unsupported constructs reported by sqlglot: " + ("none" if not unsupported else ""))
    for u in unsupported:
        print(f"  - {u}")
    notes = [n for t in trees for n in behavior_notes(t, args.src, args.dst)]
    seen = set()
    print("Behaviors that differ between the dialects, for constructs used here (sqlglot's model; confirm in the engine docs):")
    if not notes:
        print("  none detected")
    for construct, text in notes:
        if (construct, text) not in seen:
            seen.add((construct, text))
            print(f"  - {construct}: {text}")
    literals = [n.sql() for t in trees for n in t.find_all(exp.Interval) if isinstance(n.this, exp.Literal) and n.this.is_string]
    if literals:
        print("Interval literals written with quoted values; verify them by hand in the target engine (catalog note under H17):")
        for l in sorted(set(literals)):
            print(f"  - {l}")
    print("---------------------------------------- */")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
