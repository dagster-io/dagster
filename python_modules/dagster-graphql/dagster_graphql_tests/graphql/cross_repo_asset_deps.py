# pylint: disable=redefined-outer-name
from dagster import AssetGroup, AssetKey, SourceAsset, asset, repository


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


@asset(group_name="group_1")
def grouped_asset_1():
    return 1


@asset(group_name="group_1")
def grouped_asset_2():
    return 1


@asset
def ungrouped_asset_3():
    return 1


# For now the only way to add assets to repositories is via AssetGroup
# When AssetGroup is removed, these assets should be added directly to repository_with_named_groups
named_groups_assets = AssetGroup([grouped_asset_1, grouped_asset_2, ungrouped_asset_3])


@repository
def repository_with_named_groups():
    return [named_groups_assets]
