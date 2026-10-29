"""Runs the SQL tests published in skills/tieout/references/hypotheses.md.

Each hypothesis runs twice in DuckDB on synthetic data:
  - 'defect': data with the defect injected  -> the test must CONFIRM
  - 'clean' : data without the defect        -> the test must RULE OUT
It also checks that each SQL block transpiles with sqlglot to BigQuery and
Databricks (syntax only; it is NOT executed on those engines).

The SQL is read from the catalog itself so that what is published is what is tested.

Usage: python tests/test_hypotheses.py
"""
import pathlib
import re
import sys

import duckdb
import sqlglot

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "skills" / "tieout" / "references" / "hypotheses.md"
BLOCK = re.compile(r"```sql test:(\w+)\n(.*?)```", re.S)


def values(table, cols, *rows):
    return f"CREATE TABLE {table} AS SELECT * FROM (VALUES {', '.join(rows)}) AS t({cols})"


def ts(s):
    return f"TIMESTAMP '{s}'"


# id -> (setup_defect, setup_clean); each setup is a list of SQL statements
FIXTURES = {
    "H01": (
        [values("a", "k, ts", f"(1, {ts('2026-01-31 10:00:00')})", f"(2, {ts('2026-02-28 10:00:00')})"),
         values("b", "k, ts", f"(1, {ts('2026-01-31 10:00:00')})", f"(2, {ts('2026-02-28 10:00:00')})",
                f"(3, {ts('2026-03-05 10:00:00')})")],
        [values("a", "k, ts", f"(1, {ts('2026-01-31 10:00:00')})", f"(2, {ts('2026-02-28 10:00:00')})"),
         "CREATE TABLE b AS SELECT * FROM a"],
    ),
    "H03": (
        [values("a", "period, m", "('2026-01', 1)", "('2026-02', 1)", "('2026-03', 1)"),
         values("b", "period, m", "('2026-01', 1)", "('2026-02', 1)")],
        [values("a", "period, m", "('2026-01', 1)", "('2026-02', 1)"),
         "CREATE TABLE b AS SELECT * FROM a"],
    ),
    "H04": (
        [values("a", "period, m", "('2026-01', 100)", "('2026-02', 200)", "('2026-03', 300)", "('2026-04', 400)"),
         values("b", "period, m", "('2026-01', 118)", "('2026-02', 236)", "('2026-03', 354)", "('2026-04', 472)")],
        [values("a", "period, m", "('2026-01', 100)", "('2026-02', 200)", "('2026-03', 300)", "('2026-04', 400)"),
         "CREATE TABLE b AS SELECT * FROM a"],
    ),
    "H05": (
        [values("a", "typ, m", "('SALE', 100)", "('CREDIT', -10)", "(NULL, 5)"),
         values("b", "typ, m", "('SALE', 100)")],
        [values("a", "typ, m", "('SALE', 100)", "('CREDIT', -10)", "(NULL, 5)"),
         "CREATE TABLE b AS SELECT * FROM a"],
    ),
    "H07": (
        [values("a", "typ, m", "('SALE', 100)", "(NULL, 25)")],
        [values("a", "typ, m", "('SALE', 100)", "('CREDIT', -10)")],
    ),
    "H08": (
        [values("a", "k, m", "(1, 100)", "(2, 50)"),
         values("d", "k, attr", "(1, 'x')", "(2, 'y')", "(2, 'z')")],
        [values("a", "k, m", "(1, 100)", "(2, 50)"),
         values("d", "k, attr", "(1, 'x')", "(2, 'y')")],
    ),
    "H09": (
        [values("a", "k, m", "(1, 100)", "(2, 50)", "(3, 25)"),
         values("d", "k, attr", "(1, 'x')", "(2, 'y')")],
        [values("a", "k, m", "(1, 100)", "(2, 50)", "(3, 25)"),
         values("d", "k, attr", "(1, 'x')", "(2, 'y')", "(3, 'z')")],
    ),
    "H10": (
        [values("a", "k, m", "('000123', 10)", "('000124', 20)"),
         values("d", "k, attr", "(123, 'x')", "(124, 'y')")],
        [values("a", "k, m", "('123', 10)", "('124', 20)"),
         values("d", "k, attr", "(123, 'x')", "(124, 'y')")],
    ),
    "H11": (
        [values("d", "k, valid_from", "(1, DATE '2025-01-01')", "(1, DATE '2026-01-01')", "(2, DATE '2025-01-01')")],
        [values("d", "k, valid_from", "(1, DATE '2025-01-01')", "(2, DATE '2025-01-01')")],
    ),
    "H12": (
        [values("a", "k, m", "(1, 100)", "(2, 50)"),
         values("b", "k, m", "(1, 60)", "(1, 40)", "(2, 50)")],
        [values("a", "k, m", "(1, 100)", "(2, 50)"),
         values("b", "k, m", "(1, 100)", "(2, 50)")],
    ),
    "H13": (
        [values("a", "k, line, m", "(1, 1, 100)", "(1, 1, 100)", "(2, 1, 50)")],
        [values("a", "k, line, m", "(1, 1, 100)", "(1, 2, 100)", "(2, 1, 50)")],
    ),
    "H14": (
        [values("snap_old", "m", "(100)", "(200)"),
         values("snap_new", "m", "(100)", "(200)", "(30)")],
        [values("snap_old", "m", "(100)", "(200)"),
         "CREATE TABLE snap_new AS SELECT * FROM snap_old"],
    ),
    "H15": (
        [values("a", "m1, m2", "(10, NULL)", "(5, 5)")],
        [values("a", "m1, m2", "(10, 0)", "(5, 5)")],
    ),
    "H16": (
        [values("a", "m", *["(CAST(0.0040 AS DECIMAL(18,4)))"] * 3)],
        [values("a", "m", "(CAST(1.10 AS DECIMAL(18,4)))", "(CAST(2.20 AS DECIMAL(18,4)))")],
    ),
    "H17": (
        [values("a", "ts, m", f"({ts('2026-02-01 02:00:00')}, 100)", f"({ts('2026-02-15 12:00:00')}, 50)")],
        [values("a", "ts, m", f"({ts('2026-02-10 12:00:00')}, 100)", f"({ts('2026-02-15 12:00:00')}, 50)")],
    ),
    "H18": (
        [values("a", "dim, m", "('Lima', 1)", "('lima ', 1)", "('LIMA', 1)")],
        [values("a", "dim, m", "('Lima', 1)", "('Cusco', 1)")],
    ),
    "H20": (
        [values("a", "period, m", "('2026-01', 100)", "('2026-02', 200)"),
         values("b", "period, m", "('2026-01', 100)", "('2026-02', 200)"),
         values("r", "period, m", "('2026-01', 100)", "('2026-02', 90)")],
        [values("a", "period, m", "('2026-01', 100)", "('2026-02', 200)"),
         "CREATE TABLE b AS SELECT * FROM a",
         "CREATE TABLE r AS SELECT * FROM a"],
    ),
    "H21": (
        [values("u1", "c", "('A')", "('B')"), values("u2", "c", "('X')", "('Y')")],
        [values("u1", "c", "('A')", "('B')"), values("u2", "c", "('A')", "('C')")],
    ),
    "H22": (
        [values("a", "k, ts, m", f"(1, {ts('2026-01-01 10:00:00')}, 10)", f"(1, {ts('2026-01-01 10:00:00')}, 12)")],
        [values("a", "k, ts, m", f"(1, {ts('2026-01-01 10:00:00')}, 10)", f"(1, {ts('2026-01-01 11:00:00')}, 12)")],
    ),
}

# Tests that do not use the confirmed/evidence contract
SPECIAL = {"U1"}


def load_tests():
    text = CATALOG.read_text(encoding="utf-8")
    return {m.group(1): m.group(2).strip() for m in BLOCK.finditer(text)}


def run(setup, sql):
    con = duckdb.connect()
    for stmt in setup:
        con.execute(stmt)
    row = con.execute(sql).fetchone()
    con.close()
    return row


def check_u1(sql):
    setup = [values("a", "k, m", "(1, 100)", "(2, 50)", "(3, 25)"),
             values("b", "k, m", "(1, 100)", "(2, 60)", "(4, 40)")]
    solo_a, solo_b, dif_comunes, dif_total = [float(x) for x in run(setup, sql)]
    ok = (solo_a, solo_b, dif_comunes, dif_total) == (25.0, 40.0, 10.0, 25.0)
    identidad = abs(dif_total - (-solo_a + solo_b + dif_comunes)) < 1e-9
    return ok and identidad, f"solo_a={solo_a} solo_b={solo_b} comunes={dif_comunes} total={dif_total}"


def main():
    tests = load_tests()
    fallos = []

    faltan_fixture = sorted(set(tests) - set(FIXTURES) - SPECIAL)
    faltan_test = sorted(set(FIXTURES) - set(tests))
    if faltan_fixture:
        fallos.append(f"tests without fixture: {faltan_fixture}")
    if faltan_test:
        fallos.append(f"fixtures without a test in the catalog: {faltan_test}")

    print(f"{'id':5} {'defect':18} {'clean':18} {'bigquery':9} {'databricks':10}")
    for tid in sorted(tests):
        sql = tests[tid]
        transp = {}
        for dialect in ("bigquery", "databricks"):
            try:
                sqlglot.transpile(sql, read="duckdb", write=dialect)
                transp[dialect] = "ok"
            except Exception as e:  # noqa: BLE001
                transp[dialect] = "ERROR"
                fallos.append(f"{tid}: does not transpile to {dialect}: {e}")

        if tid in SPECIAL:
            ok, detalle = check_u1(sql)
            print(f"{tid:5} {'ok' if ok else 'FAIL':18} {'-':18} {transp['bigquery']:9} {transp['databricks']:10} {detalle}")
            if not ok:
                fallos.append(f"{tid}: {detalle}")
            continue

        if tid not in FIXTURES:
            continue
        defect, clean = FIXTURES[tid]
        try:
            rd = run(defect, sql)
            rc = run(clean, sql)
        except Exception as e:  # noqa: BLE001
            fallos.append(f"{tid}: execution error: {e}")
            print(f"{tid:5} ERROR {e}")
            continue
        okd = bool(rd[0]) is True
        okc = bool(rc[0]) is False
        print(f"{tid:5} {'confirms' if okd else 'FAIL':8} ev={str(rd[1]):8} "
              f"{'rules out' if okc else 'FAIL':8} ev={str(rc[1]):8} "
              f"{transp['bigquery']:9} {transp['databricks']:10}")
        if not okd:
            fallos.append(f"{tid}: does not confirm on data with the defect: {rd}")
        if not okc:
            fallos.append(f"{tid}: does not rule out on clean data: {rc}")

    print()
    if fallos:
        print("FAILURES:")
        for f in fallos:
            print(" -", f)
        sys.exit(1)
    print(f"OK: {len(tests)} SQL tests verified in DuckDB (defect and clean) and transpiled to BigQuery/Databricks (syntax only).")


if __name__ == "__main__":
    main()
