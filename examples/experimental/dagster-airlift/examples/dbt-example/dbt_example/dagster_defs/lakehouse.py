from pathlib import Path
from typing import List, Sequence

from dagster import AssetKey, AssetsDefinition, AssetSpec, multi_asset
from dagster_airlift.core import specs_from_task

from dbt_example.shared.load_iris import id_from_path, load_csv_to_duckdb


def lakehouse_asset_key(*, csv_path) -> AssetKey:
    return AssetKey(["lakehouse", id_from_path(csv_path)])


def specs_from_lakehouse(*, task_id: str, dag_id: str, csv_path: Path) -> Sequence[AssetSpec]:
    return specs_from_task(
        task_id=task_id,
        dag_id=dag_id,
        assets=[lakehouse_asset_key(csv_path=csv_path)],
    )


def defs_from_lakehouse(
    *, task_id: str, dag_id: str, csv_path: Path, duckdb_path: Path, columns: List[str]
) -> AssetsDefinition:
    @multi_asset(specs=specs_from_lakehouse(task_id=task_id, dag_id=dag_id, csv_path=csv_path))
    def _multi_asset() -> None:
        load_csv_to_duckdb(
            csv_path=csv_path,
            db_path=duckdb_path,
            columns=columns,
        )

    return _multi_asset
