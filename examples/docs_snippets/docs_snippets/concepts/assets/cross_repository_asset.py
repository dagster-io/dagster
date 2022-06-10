from dagster import AssetKey, SourceAsset, asset, repository


@asset
def repository_a_asset():
    return 5


@repository
def repository_a():
    return [repository_a_asset]


repository_a_source_asset = SourceAsset(key=AssetKey("repository_a_asset"))


@asset
def repository_b_asset(repository_a_asset):
    return repository_a_asset + 6


@repository
def repository_b():
    return [repository_b_asset, repository_a_source_asset]
