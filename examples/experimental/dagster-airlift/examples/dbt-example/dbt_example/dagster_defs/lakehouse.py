from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dagster import AssetKey, AssetSpec, Definitions, multi_asset
from dagster_airlift.core import DefsFactory

from dbt_example.shared.load_iris import id_from_path, load_csv_to_duckdb


@dataclass
class CSVToDuckdbDefs(DefsFactory):
    name: str
    csv_path: Path
    duckdb_path: Optional[Path] = None
    columns: Optional[List[str]] = None

    def build_defs(self) -> Definitions:
        asset_spec = AssetSpec(key=AssetKey(["lakehouse", id_from_path(self.csv_path)]))

        @multi_asset(specs=[asset_spec], name=self.name)
        def _multi_asset() -> None:
            if self.duckdb_path is None or self.columns is None:
                raise Exception("This asset is not yet executable. Need to provide a duckdb_path.")
            else:
                load_csv_to_duckdb(
                    csv_path=self.csv_path,
                    db_path=self.duckdb_path,
                    columns=self.columns,
                )

        return Definitions(assets=[_multi_asset])
