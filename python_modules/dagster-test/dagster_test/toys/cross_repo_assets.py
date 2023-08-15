from dagster import AssetKey, SourceAsset, asset


@asset
def upstream_asset():
    return 5


upstream_repo_assets = [upstream_asset]

source_assets = [
    SourceAsset(AssetKey("upstream_asset")),
    SourceAsset(AssetKey("always_source_asset")),
]


@asset
def downstream_asset1(upstream_asset, always_source_asset):
    assert upstream_asset
    assert always_source_asset


@asset
def downstream_asset2(upstream_asset, always_source_asset):
    assert upstream_asset
    assert always_source_asset


downstream_repo1_assets = [downstream_asset1, source_assets]
downstream_repo2_assets = [downstream_asset2, source_assets]
