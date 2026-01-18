"""Script to seed a DuckDB database with a CSV file for testing purposes."""

import os
from pathlib import Path

import duckdb
import pandas as pd

DB_PATH = Path(__file__).parent / Path(os.environ["DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH"])
DB_NAME = os.environ["DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_NAME"]
CSV_PATH = Path(__file__).parent / "raw_customers.csv"
if not DB_PATH.parent.exists():
    os.mkdir(DB_PATH.parent)
duckdb_file_name = DB_PATH.stem
df = pd.read_csv(CSV_PATH, dtype={"id": int})
con = duckdb.connect(str(DB_PATH))
con.execute("CREATE SCHEMA IF NOT EXISTS main").fetchall()
con.execute("CREATE TABLE IF NOT EXISTS main.raw_customers AS SELECT * FROM df").fetchall()
con.execute("SELECT * FROM main.raw_customers").fetchall()
con.close()
