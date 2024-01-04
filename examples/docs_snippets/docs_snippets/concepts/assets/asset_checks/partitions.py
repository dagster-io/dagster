from typing import Dict

from dagster import (
    AssetCheckResult,
    Definitions,
    StaticPartitionsDefinition,
    asset,
    asset_check,
)


@asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
def partitioned_asset(context):
    return "sample_data"


@asset_check(asset=partitioned_asset)
def no_nones(partitioned_asset: Dict[str, str]):
    # partitioned_asset will be a dict of partition keys to materialized values.
    # partitioned_asset = {"a": "sample_data", "b": "sample_data", "c": "sample_data"}
    return AssetCheckResult(
        passed=all([x is not None for x in partitioned_asset.values()])
    )


defs = Definitions(assets=[partitioned_asset], asset_checks=[no_nones])
