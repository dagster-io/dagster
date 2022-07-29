# pylint: disable=redefined-outer-name
from dagster import AssetKey, SourceAsset, asset, repository
from dagster._legacy import AssetGroup


@asset
def upstream_asset():
    return 5


upstream_asset_group = AssetGroup([upstream_asset])


@repository
def upstream_assets_repository():
    return [upstream_asset_group]


source_assets = [SourceAsset(AssetKey("upstream_asset"))]


@asset
def downstream_asset1(upstream_asset):
    assert upstream_asset


@asset
def downstream_asset2(upstream_asset):
    assert upstream_asset


downstream_asset_group1 = AssetGroup(assets=[downstream_asset1], source_assets=source_assets)
downstream_asset_group2 = AssetGroup(assets=[downstream_asset2], source_assets=source_assets)


@repository
def downstream_assets_repository1():
    return [downstream_asset_group1]


@repository
def downstream_assets_repository2():
    return [downstream_asset_group2]
