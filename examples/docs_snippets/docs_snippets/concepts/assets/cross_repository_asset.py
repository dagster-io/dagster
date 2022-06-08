from dagster import AssetGroup, AssetKey, SourceAsset, asset, repository


@asset
def repository_a_asset():
    return 5


repository_a_asset_group = AssetGroup(assets=[repository_a_asset])


@repository
def repository_a():
    return [repository_a_asset_group]


repository_a_source_asset = SourceAsset(key=AssetKey("repository_a_asset"))


@asset
def repository_b_asset(repository_a_asset):
    return repository_a_asset + 6


repository_b_asset_group = AssetGroup(
    assets=[repository_b_asset], source_assets=[repository_a_source_asset]
)


@repository
def repository_b():
    return [repository_b_asset_group]
