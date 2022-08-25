# pylint: disable=redefined-outer-name
from dagster import AssetKey, SourceAsset, asset
from dagster._legacy import AssetGroup


@asset
def upstream_asset():
    return 5


upstream_asset_group = AssetGroup([upstream_asset])

source_assets = [SourceAsset(AssetKey("upstream_asset"))]


@asset
def downstream_asset1(upstream_asset):
    assert upstream_asset


@asset
def downstream_asset2(upstream_asset):
    assert upstream_asset


downstream_asset_group1 = AssetGroup([downstream_asset1], source_assets)
downstream_asset_group2 = AssetGroup([downstream_asset2], source_assets)
