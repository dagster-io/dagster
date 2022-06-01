from dagster import AssetGroup, asset, repository


@asset(group_name="group_1")
def grouped_asset_1():
    return 1


@asset(group_name="group_1")
def grouped_asset_2():
    return 1


@asset
def ungrouped_asset_3():
    return 1


@asset(group_name="group_2")
def grouped_asset_4():
    return 1


# For now the only way to add assets to repositories is via AssetGroup
# When AssetGroup is removed, these assets should be added directly to repository_with_named_groups
named_groups_assets = AssetGroup(
    [grouped_asset_1, grouped_asset_2, ungrouped_asset_3, grouped_asset_4]
)


@repository
def named_asset_groups_repo():
    return [named_groups_assets]
