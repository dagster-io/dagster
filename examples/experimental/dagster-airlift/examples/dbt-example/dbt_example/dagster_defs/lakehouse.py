from pathlib import Path
from typing import List, Sequence

from dagster import AssetKey, AssetsDefinition, AssetSpec, multi_asset
from dagster_airlift.core import specs_from_task

from dbt_example.shared.load_iris import id_from_path, load_csv_to_duckdb


def lakehouse_asset_key(*, csv_path) -> AssetKey:
    return AssetKey(["lakehouse", id_from_path(csv_path)])

def load_lakehouse_defs(
    specs: Sequence[AssetSpec], csv_path: Path, duckdb_path: Path, columns: List[str]
)
    @multi_asset(specs=specs)
    def _multi_asset() -> None:
        load_csv_to_duckdb(
            csv_path=csv_path,
            db_path=duckdb_path,
            columns=columns,
        )

    return _multi_asset
