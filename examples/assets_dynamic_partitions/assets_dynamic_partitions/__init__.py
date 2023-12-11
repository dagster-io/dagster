from typing import Any

from dagster import (
    AssetKey,
    Definitions,
    OpExecutionContext,
    job,
    load_assets_from_modules,
    op,
)
from dagster_duckdb import build_duckdb_io_manager
from dagster_duckdb_pandas import DuckDBPandasTypeHandler

from . import assets
from .release_sensor import release_sensor

duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()])


@op
def dynamic_partition_loader(
    context: OpExecutionContext, asset_key: str, partition_key: str
) -> Any:
    """Dynamically fetches a previous value of asset_key at partition_id.

    Args:
        context (OpExecutionContext): standard op context
        asset_key (str): unique identifier of the asset to load partition from
        partition_key (str): unique identifier of the partition

    Returns:
        Any: the previously stored value of the dynamic partition ww
    """
    with defs.get_asset_value_loader(instance=context.instance) as loader:
        partition_value = loader.load_asset_value(
            AssetKey(asset_key),
            partition_key=partition_key,
        )

        return partition_value


@job
def adhoc_partition_load():
    """Job wrapper of dynamic_partition_loader."""
    dynamic_partition_loader()


defs = Definitions(
    assets=load_assets_from_modules([assets]),
    sensors=[release_sensor],
    jobs=[adhoc_partition_load],
    resources={"warehouse": duckdb_io_manager.configured({"database": "releases.duckdb"})},
)
