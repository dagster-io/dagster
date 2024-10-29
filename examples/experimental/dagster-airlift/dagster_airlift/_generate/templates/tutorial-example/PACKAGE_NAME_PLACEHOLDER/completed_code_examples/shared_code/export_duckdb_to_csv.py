from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import duckdb


@dataclass
class ExportDuckDbToCsvArgs:
    table_name: str
    csv_path: Path
    duckdb_path: Path
    duckdb_database_name: str
    duckdb_schema: Optional[str] = None


def export_duckdb_to_csv(args: ExportDuckDbToCsvArgs) -> None:
    duckdb_path, table_name = args.duckdb_path, args.table_name
    if not duckdb_path.exists():
        raise ValueError(f"DuckDB database not found at {duckdb_path}")

    # Connect to DuckDB and create a new table
    con = duckdb.connect(str(duckdb_path))
    qualified_table = (
        f"{args.duckdb_schema}.{args.table_name}" if args.duckdb_schema else table_name
    )
    df = con.execute(f"SELECT * FROM {args.duckdb_database_name}.{qualified_table}").df()
    con.close()

    # Write the dataframe to a CSV file
    df.to_csv(args.csv_path, index=False)
