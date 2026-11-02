#!/usr/bin/env python3
"""Static review of SQL with sqlglot: signals to test, never verdicts.

  python sql_review.py lint FILE [--dialect duckdb]
  python sql_review.py diff A.sql B.sql [--dialect duckdb] [--dialect-b bigquery]

lint  Lists constructs that commonly cause a mismatch between two versions of a
      query, each tied to a hypothesis in references/hypotheses.md. A finding
      says "this is worth testing", not "this is wrong": whether it matters
      depends on the data, which this script never sees.
diff  Compares two queries structurally (joins and their type, filter
      conjuncts, aggregates, grouping, output columns, DISTINCT/LIMIT) and
      lists what differs, each difference tied to a hypothesis. Table
      qualifiers are ignored so renamed aliases do not show as changes. It does
      not prove two queries are equivalent or different in result.

Needs sqlglot; without it the script stops instead of reading SQL by hand.
Exit codes: 0 ran (findings are listed, they do not change the code),
2 invalid input or sqlglot missing.
"""
import argparse
import pathlib
import sys

try:
    import sqlglot
    from sqlglot import exp
except ImportError:
    print("sql_review: sqlglot is not installed. Install it (pip install sqlglot) or declare a reduced mode; "
          "do not review the SQL by hand and present it as tool output.", file=sys.stderr)
    sys.exit(2)


def fail(msg):
    print(f"sql_review: {msg}", file=sys.stderr)
    sys.exit(2)


def parse(path, dialect):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    try:
        trees = [t for t in sqlglot.parse(text, read=dialect) if t is not None]
    except sqlglot.errors.ParseError as e:
        fail(f"cannot parse {path} as {dialect}: {e}")
    if not trees:
        fail(f"{path} has no SQL statement")
    opaque = [t for t in trees if isinstance(t, exp.Command) or t.find(exp.Command) is not None]
    if opaque:
        print(f"sql_review: NOTE {len(opaque)} statement(s) in {path} could only be read as opaque commands "
              "(unsupported syntax or procedural code). They are not analyzed; review them by hand.", file=sys.stderr)
        trees = [t for t in trees if t not in opaque]
        if not trees:
            fail(f"{path} has no statement sqlglot could analyze")
    return trees


def line_of(node):
    lines = [i.meta["line"] for i in node.find_all(exp.Identifier) if "line" in i.meta]
    return min(lines) if lines else None


def strip_qualifiers(node):
    def f(n):
        if isinstance(n, exp.Column) and n.table:
            return exp.column(n.name)
        return n
    return node.copy().transform(f)


def norm(node):
    return strip_qualifiers(node).sql().lower()


def conjuncts(node):
    if node is None:
        return []
    if isinstance(node, exp.Where):
        node = node.this
    if isinstance(node, exp.Paren):
        return conjuncts(node.this)
    if isinstance(node, exp.And):
        return conjuncts(node.left) + conjuncts(node.right)
    return [node]


def columns_of(node):
    return {c.name.lower() for c in node.find_all(exp.Column)}


# --------------------------------------------------------------------------
# lint
# --------------------------------------------------------------------------

def lint(trees):
    findings = []

    def add(hyp, node, text, severity="check"):
        findings.append((line_of(node) or 0, hyp, severity, text, node.sql()[:90].replace("\n", " ")))

    for tree in trees:
        for node in tree.walk():
            # H07: predicates that drop NULL silently
            if isinstance(node, exp.NEQ) or (isinstance(node, exp.Not) and isinstance(node.this, exp.In)):
                cols = columns_of(node)
                handled = False
                parent = node.parent
                while parent is not None and not isinstance(parent, (exp.Select, exp.Subquery)):
                    if isinstance(parent, exp.Or) and any(isinstance(n, exp.Is) and columns_of(n) & cols
                                                          for n in parent.walk()):
                        handled = True
                        break
                    parent = parent.parent
                if not handled and cols:
                    add("H07", node, "Predicate evaluates to NULL, so it drops rows where the column is NULL "
                                     "(`<>` and NOT IN do). Check whether NULL rows exist and whether they should count.")
            # H09 / H08: joins
            if isinstance(node, exp.Join):
                kind = (node.args.get("side") or node.args.get("kind") or "").upper()
                select = node.parent
                if kind in ("", "INNER"):
                    add("H09", node, "INNER JOIN drops rows with no match in the joined table. Compare with the "
                                     "unmatched mass (test H09), and check the join key's type and level (H10).")
                if isinstance(select, exp.Select) and any(isinstance(a, exp.AggFunc) for a in select.find_all(exp.AggFunc)):
                    add("H08", node, "An aggregate is computed over a joined table. If the joined table is not unique "
                                     "on the join key, the measure is repeated for each match (test H08).", "info")
                on = node.args.get("on")
                if on is not None and any(isinstance(n, (exp.Cast, exp.Func)) and not isinstance(n, exp.AggFunc)
                                          for n in on.walk() if n is not on):
                    add("H10", node, "The join condition wraps a column in a cast or function: the two sides may have "
                                     "different types or formats (test H10).", "info")
            # LEFT JOIN neutralized by WHERE on the right table
            if isinstance(node, exp.Select):
                aliases = {}
                for j in node.args.get("joins") or []:
                    if (j.args.get("side") or "").upper() == "LEFT" and isinstance(j.this, exp.Table):
                        aliases[(j.this.alias or j.this.name).lower()] = j
                for pred in conjuncts(node.args.get("where")):
                    tabs = {c.table.lower() for c in pred.find_all(exp.Column) if c.table}
                    if tabs & set(aliases) and not any(isinstance(n, exp.Is) for n in pred.walk()):
                        add("H09", pred, "A WHERE condition on the right table of a LEFT JOIN removes the unmatched "
                                         "rows, which makes the join behave like an INNER JOIN.")
            # H16: rounding inside an aggregate
            if isinstance(node, exp.Round) and node.find_ancestor(exp.AggFunc):
                add("H16", node, "ROUND is applied per row inside an aggregate; rounding the total instead gives a "
                                 "different result (test H16).")
            if isinstance(node, exp.Cast) and node.args.get("to") is not None and \
                    node.args["to"].this in (exp.DataType.Type.FLOAT, exp.DataType.Type.DOUBLE):
                add("H16", node, "Cast to a floating-point type: sums may differ from a decimal sum in the last digits.", "info")
            # H15: arithmetic on nullable columns, division without protection
            if isinstance(node, (exp.Add, exp.Sub, exp.Mul)) and isinstance(node.left, exp.Column) \
                    and isinstance(node.right, exp.Column):
                add("H15", node, "Arithmetic between two columns: the result is NULL if either is NULL, and the row "
                                 "disappears from a SUM (test H15).", "info")
            if isinstance(node, exp.Div) and not isinstance(node.right, (exp.Literal, exp.Nullif)) \
                    and not (isinstance(node.right, exp.Paren) and isinstance(node.right.this, exp.Nullif)):
                add("H15", node, "Division by an expression that may be zero or NULL, with no NULLIF.", "info")
            # H21: positional UNION
            if isinstance(node, exp.Union):
                def branches(n):
                    if isinstance(n, exp.Union):
                        return branches(n.left) + branches(n.right)
                    return [n]
                bs = [b.unnest() if isinstance(b, exp.Subquery) else b for b in branches(node)]
                names = [[(e.alias_or_name or "").lower() for e in b.expressions] for b in bs if isinstance(b, exp.Select)]
                if names and (len({len(n) for n in names}) > 1 or any(n != names[0] for n in names[1:])):
                    add("H21", node, "UNION branches have different column names or counts at the same positions; "
                                     "UNION pairs columns by position, not by name (test H21).")
            # H22 / H13: selection and duplicates
            if isinstance(node, exp.Select) and node.args.get("limit") is not None and not node.args.get("order"):
                add("H22", node, "LIMIT without ORDER BY returns an arbitrary set of rows.")
            if isinstance(node, exp.RowNumber):
                add("H22", node, "ROW_NUMBER picks one row per group. If its ORDER BY admits ties the choice is "
                                 "not deterministic: add a unique tie-breaker (test H22).", "info")
            if isinstance(node, exp.Select) and node.args.get("distinct"):
                add("H13", node, "DISTINCT can hide duplicated source rows. If the other side does not use it, "
                                 "compare duplicates in the base table (test H13).", "info")
            # H17: time-zone dependent constructs
            if isinstance(node, (exp.DateTrunc, exp.TimestampTrunc, exp.AtTimeZone, exp.CurrentDate,
                                 exp.CurrentTimestamp, exp.Extract)):
                add("H17", node, "Date or time construct that depends on the session or column time zone; check where "
                                 "the period boundary falls on each engine (test H17).", "info")
            # H05: equality filters on a categorical value
            if isinstance(node, exp.EQ) and isinstance(node.parent, (exp.Where, exp.And)) \
                    and isinstance(node.right, exp.Literal) and node.right.is_string and isinstance(node.left, exp.Column):
                add("H05", node, "Filter on a literal value. Profile the column's values first so you know what this "
                                 "filter leaves out (test H05).", "info")

    seen, out = set(), []
    for item in sorted(findings, key=lambda x: (x[0], x[1], x[4])):
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def run_lint(args):
    findings = lint(parse(args.file, args.dialect))
    print(f"# SQL lint: {args.file} (dialect {args.dialect}, sqlglot {sqlglot.__version__})\n")
    print("Signals to test, not defects. Each hypothesis is described in references/hypotheses.md.\n")
    if not findings:
        print("No signals found. That does not mean the query is correct.")
        return
    print("| Line | Hypothesis | Weight | Signal | Code |")
    print("|---|---|---|---|---|")
    for line, hyp, sev, text, code in findings:
        print(f"| {line or '?'} | {hyp} | {sev} | {text} | `{code}` |")


# --------------------------------------------------------------------------
# diff
# --------------------------------------------------------------------------

def features(trees):
    tree = trees[0]
    select = tree.find(exp.Select)
    f = {"joins": {}, "filters": set(), "aggregates": set(), "group": set(), "outputs": [], "flags": set(), "tables": set()}
    for t in tree.find_all(exp.Table):
        f["tables"].add(t.name.lower())
    if select is None:
        return f
    for j in select.args.get("joins") or []:
        kind = " ".join(x for x in ((j.args.get("side") or ""), (j.args.get("kind") or "")) if x).upper() or "INNER"
        if isinstance(j.this, exp.Table):
            f["joins"][j.this.name.lower()] = (kind, norm(j.args["on"]) if j.args.get("on") is not None else "")
    f["filters"] = {norm(c) for c in conjuncts(select.args.get("where"))}
    for j in select.args.get("joins") or []:
        on = j.args.get("on")
        if on is not None and isinstance(j.this, exp.Table):
            for c in conjuncts(on):
                if not (isinstance(c, exp.EQ) and isinstance(c.left, exp.Column) and isinstance(c.right, exp.Column)):
                    f["filters"].add(norm(c) + f"  [in ON of {j.this.name.lower()}]")
    for agg in select.find_all(exp.AggFunc):
        f["aggregates"].add(norm(agg))
    f["group"] = {norm(g) for g in (select.args.get("group").expressions if select.args.get("group") else [])}
    f["outputs"] = [(e.alias_or_name or "").lower() for e in select.expressions]
    if select.args.get("distinct"):
        f["flags"].add("DISTINCT")
    if select.args.get("limit") is not None:
        f["flags"].add("LIMIT")
    return f


def run_diff(args):
    a = features(parse(args.a, args.dialect))
    b = features(parse(args.b, args.dialect_b or args.dialect))
    rows = []

    for table in sorted(set(a["joins"]) | set(b["joins"])):
        ja, jb = a["joins"].get(table), b["joins"].get(table)
        if ja is None:
            rows.append(("H09", "join", f"only in B: {jb[0]} JOIN {table} ON {jb[1]}"))
        elif jb is None:
            rows.append(("H09", "join", f"only in A: {ja[0]} JOIN {table} ON {ja[1]}"))
        else:
            if ja[0] != jb[0]:
                rows.append(("H09", "join type", f"{table}: A uses {ja[0]} JOIN, B uses {jb[0]} JOIN"))
            if ja[1] != jb[1]:
                rows.append(("H08/H10", "join condition", f"{table}: A `{ja[1]}` | B `{jb[1]}`"))
    for p in sorted(a["filters"] - b["filters"]):
        rows.append(("H05/H07", "filter", f"only in A: `{p}`"))
    for p in sorted(b["filters"] - a["filters"]):
        rows.append(("H05/H07", "filter", f"only in B: `{p}`"))
    for p in sorted(a["aggregates"] - b["aggregates"]):
        rows.append(("H16/H15", "aggregate", f"only in A: `{p}`"))
    for p in sorted(b["aggregates"] - a["aggregates"]):
        rows.append(("H16/H15", "aggregate", f"only in B: `{p}`"))
    for p in sorted(a["group"] ^ b["group"]):
        rows.append(("H12", "grouping", f"`{p}` is grouped in {'A' if p in a['group'] else 'B'} only"))
    if a["outputs"] != b["outputs"]:
        rows.append(("H02", "output columns", f"A: {a['outputs']} | B: {b['outputs']}"))
    for fl in sorted(a["flags"] ^ b["flags"]):
        rows.append(("H13/H22", "modifier", f"{fl} is in {'A' if fl in a['flags'] else 'B'} only"))
    for t in sorted(a["tables"] ^ b["tables"]):
        if t not in a["joins"] and t not in b["joins"]:
            rows.append(("H02", "table", f"`{t}` is read in {'A' if t in a['tables'] else 'B'} only"))

    print(f"# SQL structural diff: A = {args.a}, B = {args.b} (sqlglot {sqlglot.__version__})\n")
    print("Structural differences between two queries. They point at hypotheses to test; they do not say which "
          "difference changes the result, or by how much.\n")
    if not rows:
        print("No structural differences found in the features compared. The queries may still differ in result.")
        return
    print("| Hypothesis | Kind | Difference |")
    print("|---|---|---|")
    for hyp, kind, text in rows:
        print(f"| {hyp} | {kind} | {text} |")


def main():
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to a legacy code page
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("lint")
    l.add_argument("file")
    l.add_argument("--dialect", default="duckdb")
    d = sub.add_parser("diff")
    d.add_argument("a")
    d.add_argument("b")
    d.add_argument("--dialect", default="duckdb")
    d.add_argument("--dialect-b", help="dialect of B if different from A")
    args = ap.parse_args()
    for name in ("dialect", "dialect_b"):
        value = getattr(args, name, None)
        if value:
            try:
                sqlglot.Dialect.get_or_raise(value)
            except ValueError as e:
                fail(str(e))
    (run_lint if args.cmd == "lint" else run_diff)(args)


if __name__ == "__main__":
    main()
