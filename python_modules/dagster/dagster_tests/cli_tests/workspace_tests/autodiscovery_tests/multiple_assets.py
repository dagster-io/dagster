# pylint: disable=redefined-outer-name
from dagster import AssetKey, SourceAsset, asset

source_asset = SourceAsset(AssetKey("source_asset"))


@asset
def asset1(source_asset):
    assert source_asset


@asset
def asset2():
    pass
