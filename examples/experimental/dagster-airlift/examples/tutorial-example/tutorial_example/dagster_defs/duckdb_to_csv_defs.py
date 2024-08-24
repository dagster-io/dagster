from pathlib import Path
from typing import Optional

from dagster import AssetKey, AssetSpec, Definitions, multi_asset

from tutorial_example.shared.export_duckdb_to_csv import export_duckdb_to_csv


def export_duckdb_to_csv_defs(
    table_name: str,
    csv_path: Path,
    duckdb_path: Path,
    duckdb_database_name: str,
    duckdb_schema: Optional[str] = None,
) -> Definitions:
    upstream_key = (
        AssetKey([duckdb_schema, table_name])
        if duckdb_schema is not None
        else AssetKey([table_name])
    )

    @multi_asset(
        specs=[
            AssetSpec(
                key=AssetKey([csv_path.name.replace(".", "_")]),
                deps={upstream_key},
            )
        ],
    )
    def _multi_asset() -> None:
        export_duckdb_to_csv(
            table_name=table_name,
            csv_path=csv_path,
            duckdb_path=duckdb_path,
            duckdb_schema=duckdb_schema,
            duckdb_database_name=duckdb_database_name,
        )

    return Definitions(assets=[_multi_asset])
