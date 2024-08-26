from pathlib import Path
from typing import List

from dagster import AssetKey, AssetSpec, Definitions, multi_asset

from tutorial_example.shared.load_csv_to_duckdb import load_csv_to_duckdb


def load_csv_to_duckdb_defs(
    table_name: str,
    csv_path: Path,
    duckdb_path: Path,
    column_names: List[str],
    duckdb_schema: str,
    duckdb_database_name: str,
) -> Definitions:
    @multi_asset(specs=[AssetSpec(key=AssetKey([duckdb_schema, table_name]))])
    def _multi_asset() -> None:
        load_csv_to_duckdb(
            table_name=table_name,
            csv_path=csv_path,
            duckdb_path=duckdb_path,
            names=column_names,
            duckdb_schema=duckdb_schema,
            duckdb_database_name=duckdb_database_name,
        )

    return Definitions(assets=[_multi_asset])
