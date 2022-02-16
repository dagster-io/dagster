from dagster import asset
from dagster.core.asset_defs.asset_collection import AssetCollection


@asset
def asset1():
    pass


@asset
def asset2():
    pass


my_asset_collection = AssetCollection([asset1, asset2])
