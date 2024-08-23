from pathlib import Path
from typing import Optional

import duckdb


def export_duckdb_to_csv(
    *,
    table_name: str,
    csv_path: Path,
    duckdb_path: Path,
    duckdb_schema: Optional[str],
    duckdb_database_name: str,
) -> None:
    if not duckdb_path.exists():
        raise ValueError(f"DuckDB database not found at {duckdb_path}")

    # Connect to DuckDB and create a new table
    con = duckdb.connect(str(duckdb_path))
    qualified_table = f"{duckdb_schema}.{table_name}" if duckdb_schema else table_name
    df = con.execute(f"SELECT * FROM {duckdb_database_name}.{qualified_table}").df()
    con.close()

    # Write the dataframe to a CSV file
    df.to_csv(csv_path, index=False)
