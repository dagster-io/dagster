from dagster import asset
from dagster._core.asset_defs.asset_group import AssetGroup


@asset
def asset1():
    pass


@asset
def asset2():
    pass


ac1 = AssetGroup([asset1])
ac2 = AssetGroup([asset2])
