"""Build b.csv (candidate) from a.csv (reference) by injecting known defects.

All data is synthetic. The defects map to hypotheses in the catalog:
  H05  B keeps only typ = 'SALE', so credit notes are lost
  H13  the candidate's source repeats two lines (D005/1 and D008/1)
  H16  B stores amounts rounded per row to 2 decimals; A keeps 4

b.csv is committed; this script documents how it was made and lets you
rebuild it: python examples/reconcile-synthetic/make_data.py
"""
import pathlib

import duckdb

HERE = pathlib.Path(__file__).resolve().parent

con = duckdb.connect()
con.execute(f"""
CREATE TABLE a AS SELECT * FROM read_csv('{HERE / 'a.csv'}', header = true,
  columns = {{'k': 'VARCHAR', 'line': 'INTEGER', 'period': 'VARCHAR', 'typ': 'VARCHAR',
             'dim': 'VARCHAR', 'm': 'DECIMAL(18,4)'}})
""")
con.execute("""
CREATE TABLE b AS
WITH sale_only AS (                                   -- H05
  SELECT k, line, period, typ, dim, ROUND(m, 2) AS m  -- H16
  FROM a WHERE typ = 'SALE'
)
SELECT * FROM sale_only
UNION ALL
SELECT * FROM sale_only                               -- H13
WHERE (k, line) IN (('D005', 1), ('D008', 1))
ORDER BY k, line
""")
con.execute(f"COPY b TO '{HERE / 'b.csv'}' (HEADER, DELIMITER ',')")
print(f"wrote {HERE / 'b.csv'}: {con.execute('SELECT COUNT(*) FROM b').fetchone()[0]} rows")
