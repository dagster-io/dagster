from dataclasses import dataclass
from pathlib import Path
from typing import List

from dagster import AssetKey, AssetSpec, Definitions, multi_asset
from dagster_airlift.core import DefsFactory

from tutorial_example.shared.load_csv_to_duckdb import load_csv_to_duckdb


@dataclass
class CSVToDuckdbDefs(DefsFactory):
    name: str
    table_name: str
    duckdb_schema: str
    csv_path: Path
    duckdb_path: Path
    column_names: List[str]
    duckdb_database_name: str

    def build_defs(self) -> Definitions:
        ...

        @multi_asset(
            specs=[AssetSpec(key=AssetKey([self.duckdb_schema, self.table_name]))], name=self.name
        )
        def _multi_asset():
            load_csv_to_duckdb(
                table_name=self.table_name,
                csv_path=self.csv_path,
                duckdb_path=self.duckdb_path,
                names=self.column_names,
                duckdb_schema=self.duckdb_schema,
                duckdb_database_name=self.duckdb_database_name,
            )

        return Definitions(assets=[_multi_asset])
