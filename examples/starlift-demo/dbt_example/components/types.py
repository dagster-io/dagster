from dataclasses import dataclass
from pathlib import Path

from dagster import AssetKey, AssetSpec, Component, Resolvable, multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.core.context import ComponentLoadContext

from dbt_example.shared.lakehouse_utils import get_min_value, id_from_path, load_csv_to_duckdb


def lakehouse_asset_key(*, csv_path) -> AssetKey:
    return AssetKey(["lakehouse", id_from_path(csv_path)])


@dataclass
class LakehouseComponent(Component, Resolvable):
    csv_path: str
    duckdb_path: str
    columns: list[str]
    columns_for_min: list[str]

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        full_csv_path = context.path / self.csv_path
        assert full_csv_path.exists()
        full_duckdb_path = context.path / self.duckdb_path
        assert full_duckdb_path.exists()

        @multi_asset(
            specs=[
                AssetSpec(key=lakehouse_asset_key(csv_path=Path(self.csv_path)), kinds={"duckdb"})
            ],
        )
        def _multi_asset(context: AssetExecutionContext):
            load_csv_to_duckdb(
                csv_path=full_csv_path,
                db_path=full_duckdb_path,
                columns=self.columns,
            )
            res = {}
            for column in self.columns_for_min:
                min_value = get_min_value(
                    db_path=full_duckdb_path,
                    csv_path=full_csv_path,
                    column=column,
                )
                res[f"{column}_min"] = min_value
            context.add_asset_metadata(
                asset_key=lakehouse_asset_key(csv_path=Path(self.csv_path)),
                metadata=res,
            )

        return Definitions(assets=[_multi_asset])
