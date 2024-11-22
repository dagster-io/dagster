from pathlib import Path
from typing import List

import duckdb
import pandas as pd


def id_from_path(csv_path: Path) -> str:
    return csv_path.stem


def load_csv_to_duckdb(
    *,
    csv_path: Path,
    db_path: Path,
    columns: list[str],
) -> None:
    if not csv_path.exists():
        raise ValueError(f"CSV file not found at {csv_path}")
    if not db_path.exists():
        raise ValueError(f"Database not found at {db_path}")
    df = pd.read_csv(  # noqa: F841 # used by duckdb
        csv_path,
        names=columns,
    )

    table_name = id_from_path(csv_path)
    db_name = id_from_path(db_path)
    # Connect to DuckDB and create a new table
    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS lakehouse").fetchall()
    con.execute(
        f"CREATE TABLE IF NOT EXISTS {db_name}.lakehouse.{table_name} AS SELECT * FROM df"
    ).fetchall()
    con.close()
