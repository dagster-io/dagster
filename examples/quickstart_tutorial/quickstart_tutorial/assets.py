from dagster import asset
from dagster import AssetCheckResult, Definitions, asset, asset_check


@asset(group_name="simple_dependencies")
def example_asset_one(): ...


@asset(deps=[example_asset_one], group_name="simple_dependencies")
def example_asset_two(): ...


@asset
def orders(): ...


@asset_check(asset=orders)
def orders_id_has_no_nulls():
    return AssetCheckResult(
        passed=bool(True),
    )
