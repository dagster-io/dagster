from dagster import AssetGroup, AssetKey, Output, SourceAsset, asset, repository


@asset
def my_source_asset():
    yield Output(5)


@asset
def second_asset(my_source_asset):
    yield Output(1)


upstream_asset_group = AssetGroup(assets=[my_source_asset, second_asset])


@repository
def upstream_repo():
    return [upstream_asset_group]


my_source_asset = SourceAsset(key=AssetKey("my_source_asset"))


@asset
def downstream_asset(my_source_asset):
    yield Output(5)


asset_group = AssetGroup(assets=[downstream_asset], source_assets=[my_source_asset])


@repository
def downstream_repo():
    return [asset_group]