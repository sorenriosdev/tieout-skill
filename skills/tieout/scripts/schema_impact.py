#!/usr/bin/env python3
"""Find what references a table or column before you change or drop it.

  python schema_impact.py PATH --table orders [--column amount] [--dialect duckdb] [--fail-if-referenced]

Scans PATH (a file or a folder, recursively):
  - *.sql files, parsed with sqlglot and resolved scope by scope, so an alias
    like `o.amount` counts only if `o` is the table you asked about
  - Power BI PBIR files (visual.json, page.json, report.json, bookmarks) for
    fields on that table, using the same reader as bi_fields.py
Reports, per reference, how certain it is:
  certain    the column is qualified with the table, or the table is the only
             source in that SELECT
  possible   the column is unqualified and the SELECT reads several tables, one
             of them the target: it may or may not be the target's column
  star       SELECT * or table.* reads the table: new or removed columns change
             the output
  table      (no --column) the table is read, written or created here
Also lists every file that could not be parsed: those are NOT covered by this
scan, and a clean result excludes them.

This is a static scan of the files you point it at. It cannot see queries in
databases, notebooks, BI tools you did not scan, dbt macros that generate SQL,
dynamic SQL in strings, or other teams' code. "No references" means none were
found in what was scanned.

Exit codes: 0 scan completed, 1 references found and --fail-if-referenced was
given, 2 invalid input or sqlglot missing.
"""
import argparse
import json
import pathlib
import sys

try:
    import sqlglot
    from sqlglot import exp
    from sqlglot.optimizer.scope import traverse_scope
except ImportError:
    print("schema_impact: sqlglot is not installed. Install it (pip install sqlglot) or declare a reduced mode; "
          "do not claim that nothing references the object without a scan.", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bi_fields import Collector  # noqa: E402


def fail(msg):
    print(f"schema_impact: {msg}", file=sys.stderr)
    sys.exit(2)


def line_of(node):
    lines = [i.meta["line"] for i in node.find_all(exp.Identifier) if "line" in i.meta]
    return min(lines) if lines else 0


def table_matches(table, wanted):
    parts = [p.lower() for p in wanted.split(".")]
    have = [p.lower() for p in (table.catalog, table.db, table.name) if p]
    return have[-len(parts):] == parts


def scan_sql(path, table, column, dialect, refs, unparsed):
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        trees = [t for t in sqlglot.parse(text, read=dialect) if t is not None]
    except sqlglot.errors.ParseError as e:
        unparsed.append((str(path), str(e).splitlines()[0][:120]))
        return
    for tree in trees:
        if isinstance(tree, exp.Command) or tree.find(exp.Command) is not None:
            unparsed.append((str(path), "contains a statement sqlglot could only read as an opaque command "
                                        "(procedure or unsupported syntax); references inside it are not detected"))
            continue
        if column is None:
            for t in tree.find_all(exp.Table):
                if table_matches(t, table):
                    refs.append((str(path), line_of(t) or line_of(tree), "table", tree.sql()[:90].replace("\n", " ")))
            continue
        try:
            scopes = traverse_scope(tree)
        except Exception as e:  # noqa: BLE001 - sqlglot raises various errors on unsupported statements
            unparsed.append((str(path), f"scope analysis failed: {type(e).__name__}"))
            continue
        for scope in scopes:
            targets = {alias for alias, src in scope.sources.items()
                       if isinstance(src, exp.Table) and table_matches(src, table)}
            if not targets:
                continue
            for c in scope.columns:
                if c.name.lower() != column.lower():
                    continue
                if c.table:
                    if c.table in targets:
                        refs.append((str(path), line_of(c), "certain", c.sql()))
                elif len(scope.sources) == 1:
                    refs.append((str(path), line_of(c), "certain", c.sql()))
                else:
                    refs.append((str(path), line_of(c), "possible", c.sql()))
            for star in scope.stars if hasattr(scope, "stars") else []:
                q = star.this if isinstance(star, exp.Column) else None
                if q is None or (getattr(star, "table", "") in targets):
                    refs.append((str(path), line_of(scope.expression), "star", scope.expression.sql()[:90].replace("\n", " ")))
                    break
            else:
                if any(isinstance(e, exp.Star) for e in scope.expression.expressions):
                    refs.append((str(path), line_of(scope.expression), "star", scope.expression.sql()[:90].replace("\n", " ")))


def scan_pbir(path, table, column, refs, unparsed):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        unparsed.append((str(path), f"invalid JSON: {e}"))
        return
    col = Collector()
    col.walk(data, str(path))
    for where, kind, entity, prop in col.refs:
        if entity.lower() == table.lower() and (column is None or prop.lower() == column.lower()):
            refs.append((str(path), 0, "certain", f"{kind} {entity}[{prop}]"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--table", required=True, help="table name, optionally qualified (schema.table)")
    ap.add_argument("--column", help="column name; omit to find every use of the table")
    ap.add_argument("--dialect", default="duckdb")
    ap.add_argument("--fail-if-referenced", action="store_true")
    args = ap.parse_args()
    try:
        sqlglot.Dialect.get_or_raise(args.dialect)
    except ValueError as e:
        fail(str(e))
    root = pathlib.Path(args.path)
    if not root.exists():
        fail(f"not found: {root}")

    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    sql_files = [f for f in files if f.suffix.lower() == ".sql"]
    pbir_files = [f for f in files if f.suffix.lower() == ".json" and ".pbi" not in f.parts and
                  (f.name in ("visual.json", "page.json", "report.json") or f.name.endswith(".bookmark.json"))]
    refs, unparsed = [], []
    for f in sql_files:
        scan_sql(f, args.table, args.column, args.dialect, refs, unparsed)
    for f in pbir_files:
        scan_pbir(f, args.table, args.column, refs, unparsed)

    target = f"{args.table}.{args.column}" if args.column else args.table
    print(f"# Impact scan: {target}\n")
    print(f"Scanned {len(sql_files)} SQL file(s) and {len(pbir_files)} report file(s) under `{root}` "
          f"(dialect {args.dialect}, sqlglot {sqlglot.__version__}).\n")
    if refs:
        print("| File | Line | Certainty | Reference |")
        print("|---|---|---|---|")
        for f, line, kind, text in sorted(set(refs)):
            print(f"| {f} | {line or ''} | {kind} | `{text}` |")
    else:
        print("No references found in what was scanned.")
    print(f"\n{len(set(refs))} reference(s): "
          + ", ".join(f"{k} {sum(1 for r in set(refs) if r[2] == k)}" for k in ("certain", "possible", "star", "table")
                      if any(r[2] == k for r in refs)) if refs else "")
    if unparsed:
        print("\n## Not covered by this scan\n")
        print("These files could not be analyzed; they may reference the object.\n")
        for f, why in unparsed:
            print(f"- {f}: {why}")
    print("\nA static scan sees only the files given to it. Queries in databases, notebooks, other repositories and "
          "tools you did not scan are not covered.")
    sys.exit(1 if (refs and args.fail_if_referenced) else 0)


if __name__ == "__main__":
    main()
