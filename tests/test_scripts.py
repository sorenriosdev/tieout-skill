"""Tests for the deterministic scripts in skills/tieout/scripts/.

Each script is run as a subprocess, the way an agent runs it.

Usage: python tests/test_scripts.py
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import duckdb
import sqlglot

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "tieout" / "scripts"
TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def run(script, *args, python=sys.executable):
    return subprocess.run([python, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True)


# --- output encoding -----------------------------------------------------------

@test
def scripts_do_not_crash_on_a_legacy_console_encoding():
    import os
    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    for script in ("waterfall.py", "check_capabilities.py", "bi_fields.py"):
        r = subprocess.run([sys.executable, str(SCRIPTS / script), "--help"], capture_output=True, env=env)
        assert r.returncode == 0, (script, r.stderr.decode("utf-8", "replace")[-200:])


# --- check_capabilities.py ---------------------------------------------------

@test
def capabilities_reports_python_and_table():
    r = run("check_capabilities.py")
    assert r.returncode == 0, r.stderr
    assert "## Capabilities [verified: check_capabilities.py," in r.stdout
    assert "| library | sqlglot |" in r.stdout


@test
def capabilities_require_present_exits_0():
    r = run("check_capabilities.py", "--require", "sqlglot")
    assert r.returncode == 0, r.stdout


@test
def capabilities_require_missing_exits_1():
    r = run("check_capabilities.py", "--require", "no-such-tool-xyz")
    assert r.returncode == 1, r.stdout
    assert "**Missing: no-such-tool-xyz.**" in r.stdout


# --- waterfall.py ------------------------------------------------------------

HEADER = "id,description,effect,evidence\n"


def effects_file(body):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(HEADER + body)
    f.close()
    return f.name


def close(a, b, body, eps_abs="0.01", eps_rel="0"):
    return run("waterfall.py", "close", "--a", a, "--b", b, "--effects", effects_file(body),
               "--eps-abs", eps_abs, "--eps-rel", eps_rel)


@test
def waterfall_closes_when_residual_within_tolerance():
    r = close("1000", "1050.004", "H13,dup,30,e1\nH05,filter,20,e2\n")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "r = Δ − Σ effects = +0.004" in r.stdout
    assert "**Result: CLOSED**" in r.stdout


@test
def waterfall_stays_open_when_residual_exceeds_tolerance():
    r = close("1000", "1050", "H13,dup,30,e1\n")
    assert r.returncode == 1, r.stdout
    assert "r = Δ − Σ effects = +20" in r.stdout
    assert "**Result: OPEN**" in r.stdout


@test
def waterfall_uses_relative_tolerance_when_larger():
    # max(0.01, 0.001 * 1000) = 1, residual 0.5 -> closed
    r = close("1000", "1000.5", "", eps_rel="0.001")
    assert r.returncode == 0, r.stdout
    assert "= 1.000" in r.stdout or "= 1" in r.stdout


@test
def waterfall_is_exact_decimal():
    # 0.1 + 0.2 must equal 0.3 exactly
    r = close("0", "0.3", "X,a,0.1,e\nY,b,0.2,e\n", eps_abs="0")
    assert r.returncode == 0, r.stdout
    assert "r = Δ − Σ effects = 0" in r.stdout


@test
def waterfall_header_only_means_residual_is_delta():
    r = close("100", "90", "")
    assert r.returncode == 1
    assert "r = Δ − Σ effects = -10" in r.stdout


@test
def waterfall_rejects_comma_numbers():
    r = close("1,000", "1050", "")
    assert r.returncode == 2 and "not a plain number" in r.stderr, r.stderr


@test
def waterfall_rejects_bad_header_and_duplicates():
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
    f.write("hyp,amount\nH1,3\n")
    f.close()
    r = run("waterfall.py", "close", "--a", "0", "--b", "3", "--effects", f.name, "--eps-abs", "0", "--eps-rel", "0")
    assert r.returncode == 2 and "header" in r.stderr, r.stderr
    r = close("0", "2", "H1,a,1,e\nH1,b,1,e\n")
    assert r.returncode == 2 and "duplicate id" in r.stderr, r.stderr


@test
def waterfall_requires_tolerances():
    r = run("waterfall.py", "close", "--a", "0", "--b", "0", "--effects", effects_file(""))
    assert r.returncode == 2 and "--eps-abs" in r.stderr, r.stderr


@test
def compare_match_and_mismatch():
    ok = run("waterfall.py", "compare", "--expected", "-12.50", "--actual", "-12.495", "--base", "1000",
             "--eps-abs", "0.01", "--eps-rel", "0")
    assert ok.returncode == 0 and "MATCH: the case may close" in ok.stdout, ok.stdout
    bad = run("waterfall.py", "compare", "--expected", "-12.50", "--actual", "-30", "--base", "1000",
              "--eps-abs", "0.01", "--eps-rel", "0")
    assert bad.returncode == 1 and "MISMATCH: do not close" in bad.stdout, bad.stdout


# --- u1_query.py -------------------------------------------------------------

def u1(dialect, a, b, key, measure):
    return run("u1_query.py", "--dialect", dialect, "--a-table", a, "--b-table", b, "--key", key, "--measure", measure)


@test
def u1_generated_for_duckdb_runs_and_satisfies_identity():
    r = u1("duckdb", "sales_old", "sales_new", '"Order ID"', "amount")
    assert r.returncode == 0, r.stderr
    con = duckdb.connect()
    con.execute('CREATE TABLE sales_old AS SELECT * FROM (VALUES (1, 100), (2, 50), (3, 25)) t("Order ID", amount)')
    con.execute('CREATE TABLE sales_new AS SELECT * FROM (VALUES (1, 100), (2, 60), (4, 40)) t("Order ID", amount)')
    solo_a, solo_b, comunes, total = [float(x) for x in con.execute(r.stdout).fetchone()]
    assert (solo_a, solo_b, comunes, total) == (25.0, 40.0, 10.0, 25.0), (solo_a, solo_b, comunes, total)
    assert total == -solo_a + solo_b + comunes


@test
def u1_bigquery_and_databricks_parse_back():
    for dialect, table in (("bigquery", "my-proj.ds.sales"), ("databricks", "cat.sch.sales")):
        r = u1(dialect, table, table + "_new", "order_id", "amount")
        assert r.returncode == 0, r.stderr
        sqlglot.parse_one(r.stdout, read=dialect)
        assert "sales_new" in r.stdout and "SUM(amount) AS m" in r.stdout, r.stdout


@test
def u1_refuses_composite_key_and_unknown_dialect():
    r = u1("duckdb", "a1", "b1", "k1, k2", "m")
    assert r.returncode == 2 and "composite keys" in r.stderr, r.stderr
    r = u1("no-such-dialect", "a1", "b1", "k", "m")
    assert r.returncode == 2, r.stderr


@test
def u1_stops_without_sqlglot():
    code = ("import sys, runpy; sys.modules['sqlglot'] = None; "
            f"sys.argv = ['u1_query.py', '--dialect', 'duckdb', '--a-table', 'x', '--b-table', 'y', '--key', 'k', '--measure', 'm']; "
            f"runpy.run_path({str(SCRIPTS / 'u1_query.py')!r}, run_name='__main__')")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 2 and "sqlglot is not installed" in r.stderr and "WITH" not in r.stdout, r.stderr


# --- sql_review.py -----------------------------------------------------------

S3Q = ROOT / "evals" / "s3-code-only" / "files" / "queries"


def review(*args):
    return run("sql_review.py", *args)


@test
def review_diff_finds_the_planted_differences():
    r = review("diff", S3Q / "revenue_legacy.sql", S3Q / "revenue_new.sql")
    assert r.returncode == 0, r.stderr
    out = r.stdout
    assert "dim_store: A uses LEFT JOIN, B uses INNER JOIN" in out
    assert "only in A: `type is null or type <> 'void'`" in out and "only in B: `type <> 'void'`" in out
    assert "only in B: `sum(round(amount, 0))`" in out and "is_active = true" in out


@test
def review_diff_of_identical_queries_is_empty():
    r = review("diff", S3Q / "revenue_new.sql", S3Q / "revenue_new.sql")
    assert r.returncode == 0 and "No structural differences found" in r.stdout


@test
def review_lint_flags_signals_and_respects_null_handling():
    new = review("lint", S3Q / "revenue_new.sql").stdout
    assert "| H07 |" in new and "| H09 |" in new and "| H16 |" in new
    legacy = review("lint", S3Q / "revenue_legacy.sql").stdout
    assert "| H07 |" not in legacy, "`type IS NULL OR type <> 'VOID'` already handles NULL"
    assert "| H09 |" not in legacy, "a LEFT JOIN is not an INNER JOIN"


@test
def review_lint_other_signals():
    f = tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False)
    f.write("SELECT a, b FROM t1 UNION ALL SELECT b, a FROM t2;\n"
            "SELECT x FROM t LEFT JOIN d ON t.k = d.k WHERE d.flag = 1 LIMIT 5;\n"
            "SELECT m1 + m2 AS s, m1 / m2 AS r FROM t;\n")
    f.close()
    out = review("lint", f.name).stdout
    for hyp in ("H21", "H09", "H22", "H15"):
        assert f"| {hyp} |" in out, (hyp, out)


@test
def review_stops_without_sqlglot_and_on_bad_sql():
    code = ("import sys, runpy; sys.modules['sqlglot'] = None; "
            f"sys.argv = ['sql_review.py', 'lint', {str(S3Q / 'revenue_new.sql')!r}]; "
            f"runpy.run_path({str(SCRIPTS / 'sql_review.py')!r}, run_name='__main__')")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 2 and "sqlglot is not installed" in r.stderr and "| H" not in r.stdout
    bad = tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False)
    bad.write("SELEC FROM WHERE (")
    bad.close()
    assert review("lint", bad.name).returncode == 2


# --- transpile_sql.py --------------------------------------------------------

S2Q = ROOT / "evals" / "s2-missing-tool" / "files" / "queries" / "monthly_revenue.sql"


def transpile(*args):
    return run("transpile_sql.py", *args)


@test
def transpile_reports_translation_and_what_to_check():
    r = transpile(S2Q, "--from", "duckdb", "--to", "bigquery")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Syntax only: not executed on either engine" in r.stdout
    assert "Parse-back in bigquery: ok" in r.stdout
    assert "INTERVAL '5' HOUR" in r.stdout.split("REPORT")[1], "quoted interval literal must be flagged for manual check"
    assert "numeric casts" in r.stdout and "ORDER BY: Default NULL ordering differs" in r.stdout


@test
def transpile_out_never_overwrites():
    target = pathlib.Path(tempfile.mkdtemp()) / "out.sql"
    assert transpile(S2Q, "--from", "duckdb", "--to", "databricks", "--out", target).returncode in (0, 1)
    assert target.is_file() and target.read_text().strip().endswith(";")
    first = target.read_text()
    r = transpile(S2Q, "--from", "duckdb", "--to", "bigquery", "--out", target)
    assert r.returncode == 2 and "refusing to overwrite" in r.stderr and target.read_text() == first


@test
def transpile_rejects_unknown_dialect_and_missing_file():
    assert transpile(S2Q, "--from", "duckdb", "--to", "no-such-dialect").returncode == 2
    assert transpile(S2Q.with_name("nope.sql"), "--from", "duckdb", "--to", "bigquery").returncode == 2


@test
def transpile_stops_without_sqlglot():
    code = ("import sys, runpy; sys.modules['sqlglot'] = None; "
            f"sys.argv = ['transpile_sql.py', {str(S2Q)!r}, '--from', 'duckdb', '--to', 'bigquery']; "
            f"runpy.run_path({str(SCRIPTS / 'transpile_sql.py')!r}, run_name='__main__')")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 2 and "sqlglot is not installed" in r.stderr and "SELECT" not in r.stdout


# --- SKILL.md frontmatter ----------------------------------------------------

@test
def skill_frontmatter_is_valid_for_the_open_standard():
    import re
    text = (ROOT / "skills" / "tieout" / "SKILL.md").read_text(encoding="utf-8")
    front = text.split("---")[1]
    fields = dict(re.findall(r"^([a-z-]+): (.*)$", front, re.M))
    assert fields["name"] == "tieout" == (ROOT / "skills" / "tieout").name
    desc = fields["description"]
    assert 1 <= len(desc) <= 1024, len(desc)
    assert not desc.startswith(('"', "'")) and ": " not in desc and " #" not in desc, \
        "a plain YAML scalar cannot contain ': ' or ' #' (skills-ref rejects it)"
    assert len(fields["compatibility"]) <= 500
    assert text.count("\n") < 500


# --- schema_impact.py --------------------------------------------------------

def impact(*args):
    return run("schema_impact.py", *args)


def sql_dir(files):
    d = pathlib.Path(tempfile.mkdtemp())
    for name, body in files.items():
        (d / name).write_text(body)
    return d


@test
def impact_resolves_aliases_and_certainty():
    d = sql_dir({"a.sql": (
        "SELECT o.order_id, o.amount FROM orders o JOIN stores s ON o.store_id = s.store_id;\n"
        "SELECT amount FROM orders;\n"
        "SELECT amount FROM orders o JOIN stores s ON o.store_id = s.store_id;\n"
        "SELECT * FROM orders;\n"
        "SELECT s.amount FROM stores s;\n")})
    out = impact(d, "--table", "orders", "--column", "amount").stdout
    assert "| 1 | certain | `o.amount` |" in out
    assert "| 2 | certain | `amount` |" in out
    assert "| 3 | possible | `amount` |" in out, "unqualified column with two tables is only possible"
    assert "| 4 | star |" in out
    assert "| 5 |" not in out, "stores.amount is a different table"


@test
def impact_lists_unparsed_files_and_never_claims_clean():
    d = sql_dir({"ok.sql": "SELECT 1 FROM other;", "broken.sql": "SELEC ("})
    out = impact(d, "--table", "orders", "--column", "amount").stdout
    assert "No references found in what was scanned." in out
    assert "Not covered by this scan" in out and "broken.sql" in out


@test
def impact_reports_procedural_code_as_not_covered():
    d = sql_dir({"proc.sql": "CREATE PROCEDURE p() BEGIN\n  CALL x(;\nEND;\n", "ok.sql": "SELECT 1 FROM t;"})
    out = impact(d, "--table", "orders", "--column", "legacy_code").stdout
    assert "Not covered by this scan" in out and "proc.sql" in out and "opaque command" in out


@test
def impact_fail_flag_and_table_mode():
    d = sql_dir({"a.sql": "INSERT INTO t2 (a) SELECT amount FROM orders;"})
    r = impact(d, "--table", "orders", "--fail-if-referenced")
    assert r.returncode == 1 and "| table |" in r.stdout, r.stdout
    assert impact(d, "--table", "orders").returncode == 0


@test
def impact_scans_power_bi_report_files():
    out = impact(ROOT / "examples" / "clone-bi-synthetic" / "Beta.Report", "--table", "Sales", "--column", "Channel").stdout
    assert out.count("Column Sales[Channel]") == 2 and "detail_table" in out and "by_channel" in out


# --- bi_fields.py ------------------------------------------------------------

CLONE = ROOT / "examples" / "clone-bi-synthetic"


def bi(*args):
    return run("bi_fields.py", *args)


@test
def bi_clean_source_report_has_no_findings():
    r = bi("pbir", CLONE / "Alpha.Report")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "no structural problems found" in r.stdout and "None: every referenced field exists" in r.stdout


@test
def bi_clone_reports_missing_fields_including_hidden_ones():
    r = bi("pbir", CLONE / "Beta.Report")
    assert r.returncode == 1, r.stdout
    out = r.stdout
    assert "**Sales[Channel]** (Column)" in out and "**Sales[Variance]** (Measure)" in out
    assert "old_variance/visual.json` (hidden)" in out, "the hidden visual's missing field must be flagged as hidden"
    assert "detail_table/visual.json` (hidden)" in out, "a visual on a hidden page counts as hidden"
    assert "| Sales | Total Amount | Measure |" in out and "| yes |" in out


@test
def bi_clone_reports_structure_and_inherited_values():
    out = bi("pbir", CLONE / "Beta.Report").stdout
    assert "activePageName = 'old_overview'" in out
    assert "filter name 'saved_filter' is used 2 times" in out
    assert "| Alpha Unit Revenue |" in out and "| A1 |" in out
    assert "11111111-1111-1111-1111-111111111111" in out


@test
def bi_against_file_replaces_model_detection():
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    f.write("# fields of the target\nSales.Total Amount\nSales.Amount\nStore.StoreName\nStore.SegmentCode\n")
    f.close()
    r = bi("pbir", CLONE / "Beta.Report", "--against", f.name)
    assert "**Sales[Channel]**" in r.stdout and "**Sales[OrderId]**" in r.stdout and "**Store[StoreName]**" not in r.stdout


@test
def bi_refuses_pbir_legacy_and_missing_input():
    legacy = pathlib.Path(tempfile.mkdtemp()) / "Old.Report"
    legacy.mkdir()
    (legacy / "report.json").write_text("{}")
    r = bi("pbir", legacy)
    assert r.returncode == 2 and "PBIR-Legacy" in r.stderr, r.stderr
    assert bi("pbir", legacy / "nope").returncode == 2


@test
def bi_does_not_write_to_the_report():
    def snapshot():
        return {str(p): p.read_bytes() for p in sorted((CLONE / "Beta.Report").rglob("*")) if p.is_file()}
    before = snapshot()
    bi("pbir", CLONE / "Beta.Report")
    assert snapshot() == before


@test
def bi_model_lists_power_query_steps_and_flags():
    out = bi("model", CLONE / "Alpha.SemanticModel").stdout
    assert "| Sales | 2 | Filtered Rows | Table.SelectRows | removes rows |" in out
    assert "| Sales | 3 | Removed Duplicates | Table.Distinct | removes rows |" in out
    assert "join kind Inner (drops unmatched rows)" in out
    assert "conversion errors become errors or nulls" in out
    assert "select order_id, store_id, period, amount, channel from dbo.sales" in out, "native SQL, not the database name"


@test
def bi_model_lists_relationships_and_filter_context_measures():
    out = bi("model", CLONE / "Alpha.SemanticModel").stdout
    assert "| Sales.OrderId | Store.StoreId | NO | bothDirections | inactive: used only by USERELATIONSHIP; bidirectional filtering |" in out
    assert "| Sales | Amount All Stores | ALL |" in out


@test
def bi_model_flags_date_dependent_and_incremental_steps():
    d = pathlib.Path(tempfile.mkdtemp()) / "M.SemanticModel" / "definition" / "tables"
    d.mkdir(parents=True)
    (d / "T.tmdl").write_text(
        "table T\n\tpartition T = m\n\t\tmode: import\n\t\tsource =\n"
        "\t\t\t\tlet\n"
        "\t\t\t\t    Source = Sql.Database(\"s\", \"d\"),\n"
        "\t\t\t\t    Recent = Table.SelectRows(Source, each [d] >= Date.AddMonths(Date.From(DateTime.LocalNow()), -3)),\n"
        "\t\t\t\t    Window = Table.SelectRows(Recent, each [d] >= RangeStart and [d] < RangeEnd)\n"
        "\t\t\t\tin\n\t\t\t\t    Window\n")
    out = bi("model", d.parent.parent).stdout
    assert "depends on today's date" in out and "incremental-refresh range filter" in out


@test
def bi_model_reads_model_bim():
    d = pathlib.Path(tempfile.mkdtemp()) / "B.SemanticModel"
    d.mkdir()
    (d / "model.bim").write_text(json.dumps({"model": {
        "tables": [{"name": "Sales", "partitions": [{"name": "p", "source": {"type": "m", "expression": [
            "let", "    Source = Sql.Database(\"s\", \"d\"),", "    F = Table.Distinct(Source)", "in", "    F"]}}],
            "measures": [{"name": "All", "expression": "CALCULATE([x], ALLEXCEPT(Sales, Sales[k]))"}]}],
        "relationships": [{"fromTable": "Sales", "fromColumn": "k", "toTable": "D", "toColumn": "k",
                           "isActive": False, "crossFilteringBehavior": "bothDirections"}]}}))
    out = bi("model", d).stdout
    assert "Table.Distinct | removes rows" in out and "ALLEXCEPT" in out and "| Sales.k | D.k | NO |" in out


@test
def bi_tableau_workbook():
    r = bi("twb", CLONE / "sample.twb")
    assert r.returncode == 1, r.stdout
    assert "| Old check | HIDDEN | no | 1 |" in r.stdout
    assert "| Old check | Sales (synthetic) | Dif |" in r.stdout
    assert "| By segment | [federated.syn001].[none:Segment:nk] | Alpha |" in r.stdout


@test
def bi_tableau_refuses_xml_entities():
    f = tempfile.NamedTemporaryFile("w", suffix=".twb", delete=False)
    f.write('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><workbook/>')
    f.close()
    r = bi("twb", f.name)
    assert r.returncode == 2 and "entities" in r.stderr, r.stderr


def main():
    failures = []
    for fn in TESTS:
        try:
            fn()
            print(f"ok    {fn.__name__}")
        except AssertionError as e:
            failures.append(fn.__name__)
            print(f"FAIL  {fn.__name__}: {e}")
    print()
    if failures:
        print(f"FAILURES: {len(failures)} of {len(TESTS)}")
        sys.exit(1)
    print(f"OK: {len(TESTS)} script tests passed.")


if __name__ == "__main__":
    main()
