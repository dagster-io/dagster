from dagster import asset
from dagster._core.asset_defs.asset_group import AssetGroup


@asset
def asset1():
    pass


@asset
def asset2():
    pass


my_asset_group = AssetGroup([asset1, asset2])
