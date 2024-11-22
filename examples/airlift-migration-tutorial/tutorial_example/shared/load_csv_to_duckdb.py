from dataclasses import dataclass
from pathlib import Path
from typing import List

import duckdb
import pandas as pd


@dataclass
class LoadCsvToDuckDbArgs:
    table_name: str
    csv_path: Path
    duckdb_path: Path
    names: list[str]
    duckdb_schema: str
    duckdb_database_name: str


def load_csv_to_duckdb(args: LoadCsvToDuckDbArgs) -> None:
    # Ensure that path exists
    if not args.csv_path.exists():
        raise ValueError(f"CSV file not found at {args.csv_path}")
    if not args.duckdb_path.exists():
        raise ValueError(f"DuckDB database not found at {args.duckdb_path}")
    # Duckdb database stored in airflow home
    df = pd.read_csv(  # noqa: F841 # used by duckdb
        args.csv_path,
        names=args.names,
    )

    # Connect to DuckDB and create a new table
    con = duckdb.connect(str(args.duckdb_path))
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {args.duckdb_schema}").fetchall()
    con.execute(
        f"CREATE TABLE IF NOT EXISTS {args.duckdb_database_name}.{args.duckdb_schema}.{args.table_name} AS SELECT * FROM df"
    ).fetchall()
    con.close()
