from dagster.core.asset_defs import asset
from pandas import DataFrame


@asset(io_manager_key="warehouse_io_manager")
def stories(items: DataFrame) -> DataFrame:
    return items.where(items["type"] == "stories")
