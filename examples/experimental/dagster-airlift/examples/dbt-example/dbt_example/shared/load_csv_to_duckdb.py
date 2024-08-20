from pathlib import Path
from typing import List

import duckdb
import pandas as pd


def load_csv_to_duckdb(
    *,
    table_name: str,
    csv_path: Path,
    duckdb_path: Path,
    names: List[str],
    duckdb_schema: str,
    duckdb_database_name: str,
) -> None:
    # Ensure that path exists
    if not csv_path.exists():
        raise ValueError(f"CSV file not found at {csv_path}")
    if not duckdb_path.exists():
        raise ValueError(f"DuckDB database not found at {duckdb_path}")
    # Duckdb database stored in airflow home
    df = pd.read_csv(  # noqa: F841 # used by duckdb
        csv_path,
        names=names,
    )

    # Connect to DuckDB and create a new table
    con = duckdb.connect(str(duckdb_path))
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {duckdb_schema}").fetchall()
    con.execute(
        f"CREATE TABLE IF NOT EXISTS {duckdb_database_name}.{duckdb_schema}.{table_name} AS SELECT * FROM df"
    ).fetchall()
    con.close()
