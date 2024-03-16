import os

import pandas as pd
from dagster_duckdb_pandas import duckdb_pandas_io_manager

from dagster import (
    AssetCheckResult,
    Definitions,
    StaticPartitionsDefinition,
    asset,
    asset_check,
)


@asset(
    partitions_def=StaticPartitionsDefinition(["a", "b", "c"]),
    metadata={"partition_expr": "col1"},
)
def partitioned_dataframe_asset(context) -> pd.DataFrame:
    return pd.DataFrame({"col1": [context.partition_key], "col2": ["foo"]})


@asset_check(asset=partitioned_dataframe_asset)
def no_nones_in_dataframe(partitioned_dataframe_asset: pd.DataFrame):
    # partitioned_dataframe_asset includes all the partitions that have been materialized:
    # pd.DataFrame({"col1": ["a", "b", "c"], "col2": ["foo", "foo", "foo"]})
    return AssetCheckResult(passed=all(partitioned_dataframe_asset["col2"].notna()))


db_io_manager = duckdb_pandas_io_manager.configured(
    {"database": os.path.join("tmp", "sample.duckdb")}
)

defs = Definitions(
    assets=[partitioned_dataframe_asset],
    asset_checks=[no_nones_in_dataframe],
    resources={"io_manager": db_io_manager},
)
