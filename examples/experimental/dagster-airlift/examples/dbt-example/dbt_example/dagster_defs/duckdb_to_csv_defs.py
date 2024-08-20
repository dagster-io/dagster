from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dagster import AssetKey, AssetSpec, Definitions, multi_asset
from dagster_airlift.core import DefsFactory

from dbt_example.shared.export_duckdb_to_csv import export_duckdb_to_csv


@dataclass
class ExportDuckdbToCSVDefs(DefsFactory):
    table_name: str
    csv_path: Path
    duckdb_path: Path
    duckdb_database_name: str
    name: str
    duckdb_schema: Optional[str] = None

    def build_defs(self) -> Definitions:
        upstream_key = (
            AssetKey([self.duckdb_schema, self.table_name])
            if self.duckdb_schema is not None
            else AssetKey([self.table_name])
        )

        @multi_asset(
            specs=[
                AssetSpec(
                    key=AssetKey([self.csv_path.name.replace(".", "_")]),
                    deps={upstream_key},
                )
            ],
            name=self.name,
        )
        def _multi_asset() -> None:
            export_duckdb_to_csv(
                table_name=self.table_name,
                csv_path=self.csv_path,
                duckdb_path=self.duckdb_path,
                duckdb_schema=self.duckdb_schema,
                duckdb_database_name=self.duckdb_database_name,
            )

        return Definitions(assets=[_multi_asset])
