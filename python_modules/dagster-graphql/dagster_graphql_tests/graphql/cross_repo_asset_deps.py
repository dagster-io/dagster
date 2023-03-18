from dagster import AssetKey, SourceAsset, asset, repository


@asset
def upstream_asset():
    return 5


@repository
def upstream_assets_repository():
    return [upstream_asset]


source_assets = [SourceAsset(AssetKey("upstream_asset"))]


@asset
def downstream_asset1(upstream_asset):
    assert upstream_asset


@asset
def downstream_asset2(upstream_asset):
    assert upstream_asset


@repository
def downstream_assets_repository1():
    return [downstream_asset1, *source_assets]


@repository
def downstream_assets_repository2():
    return [downstream_asset2, *source_assets]
