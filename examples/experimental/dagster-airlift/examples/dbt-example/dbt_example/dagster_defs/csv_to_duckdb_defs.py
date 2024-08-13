from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dagster import AssetKey, AssetSpec, Definitions, multi_asset
from dagster_airlift.core import DefsFactory

from dbt_example.shared.load_iris import load_csv_to_duckdb


@dataclass
class CSVToDuckdbDefs(DefsFactory):
    table_name: str
    duckdb_schema: str
    name: str
    csv_path: Optional[Path] = None
    duckdb_path: Optional[Path] = None
    column_names: Optional[List[str]] = None
    duckdb_database_name: Optional[str] = None

    def build_defs(self) -> Definitions:
        asset_spec = AssetSpec(key=AssetKey([self.duckdb_schema, self.table_name]))

        @multi_asset(specs=[asset_spec], name=self.name)
        def _multi_asset():
            if self.duckdb_path is None:
                raise Exception("This asset is not yet executable. Need to provide a duckdb_path.")
            else:
                load_csv_to_duckdb(
                    table_name=self.table_name,
                    csv_path=self.csv_path,
                    duckdb_path=self.duckdb_path,
                    names=self.column_names,
                    duckdb_schema=self.duckdb_schema,
                    duckdb_database_name=self.duckdb_database_name,
                )

        return Definitions(assets=[_multi_asset])
