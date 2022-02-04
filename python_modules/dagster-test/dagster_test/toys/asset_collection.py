from dagster import AssetKey
from dagster.core.asset_defs import AssetCollection, AssetIn, asset


@asset
def asset_foo():
    return "foo"


@asset
def asset_bar():
    return "bar"


@asset(
    ins={"bar_in": AssetIn(asset_key=AssetKey("asset_foo"))}
)  # should still use output from asset_foo
def last_asset(bar_in):
    return bar_in


asset_lst = [last_asset, asset_bar, asset_foo]
collection = AssetCollection(assets=asset_lst, resource_defs={}, executor_def=None)
