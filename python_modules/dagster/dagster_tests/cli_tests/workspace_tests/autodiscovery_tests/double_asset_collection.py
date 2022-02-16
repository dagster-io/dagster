from dagster import asset
from dagster.core.asset_defs.asset_collection import AssetCollection


@asset
def asset1():
    pass


@asset
def asset2():
    pass


ac1 = AssetCollection([asset1])
ac2 = AssetCollection([asset2])
