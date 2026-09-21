"""Create the source_raw_customers table in DuckDB before dbt runs.

stg_customers.sql reads from source('jaffle_shop', 'source_raw_customers') — a
table that dbt treats as externally managed. This script creates that table from
the raw_customers.csv seed data so the source declaration is honest: the table
genuinely exists before dbt touches it.

The raw_customers *seed* remains as a separate dbt-managed asset (producing the
main.raw_customers table). Having distinct physical tables for the source and
the seed avoids a dagster/table_name collision that previously caused a
topological-order race in Dagster's multi-asset event emission.
"""

import os
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).parent / Path(os.environ["DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH"])
CSV_PATH = Path(__file__).parent / "seeds" / "raw_customers.csv"
if not DB_PATH.parent.exists():
    os.mkdir(DB_PATH.parent)
con = duckdb.connect(str(DB_PATH))
con.execute("CREATE SCHEMA IF NOT EXISTS main").fetchall()
# Column types must match what dbt seed produces (INTEGER for id, VARCHAR(256)
# for text columns) so that downstream column-schema assertions pass.
con.execute(
    f"""
    CREATE TABLE IF NOT EXISTS main.source_raw_customers AS
    SELECT
        CAST(id AS INTEGER) AS id,
        CAST(first_name AS VARCHAR(256)) AS first_name,
        CAST(last_name AS VARCHAR(256)) AS last_name
    FROM read_csv_auto('{CSV_PATH}')
    """
).fetchall()
con.close()
