from dagster import asset, asset_check
from dagster._core.definitions.asset_check_result import AssetCheckResult


@asset
def asset_1():
    pass


@asset_check(asset=asset_1)
def asset_check_1(asset_1):
    return AssetCheckResult(passed=True)
