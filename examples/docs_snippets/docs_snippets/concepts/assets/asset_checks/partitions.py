from typing import Dict

from dagster import (
    AssetCheckResult,
    Definitions,
    StaticPartitionsDefinition,
    asset,
    asset_check,
)


@asset(partitions_def=StaticPartitionsDefinition(["1", "2", "3"]))
def partitioned_asset(context) -> int:
    return int(context.partition_key) * 2


@asset_check(asset=partitioned_asset)
def greater_than_zero(partitioned_asset: Dict[str, int]):
    # With the default io manager, partitioned_asset will be a dict of partition keys to materialized
    # values. In this case:
    #
    # partitioned_asset = {"1": 2, "2": 4, "3": 6}
    return AssetCheckResult(passed=all([x > 0 for x in partitioned_asset.values()]))


defs = Definitions(assets=[partitioned_asset], asset_checks=[greater_than_zero])
