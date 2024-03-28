from dagster import AssetKey, SourceAsset, asset, repository
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset


@asset
def derived_asset():
    return 5


@repository
def upstream_assets_repository():
    return [derived_asset]


@observable_source_asset
def sometimes_observable_source_asset():
    return 5


unexecutable_src = SourceAsset("sometimes_observable_source_asset")

source_assets = [SourceAsset(AssetKey("derived_asset")), SourceAsset("always_source_asset")]


@asset
def downstream_asset1(derived_asset, always_source_asset):
    assert derived_asset


@asset
def downstream_asset2(derived_asset, always_source_asset):
    assert derived_asset


@repository
def downstream_assets_repository1():
    return [downstream_asset1, *source_assets, unexecutable_src]


@repository
def downstream_assets_repository2():
    return [downstream_asset2, *source_assets, sometimes_observable_source_asset]
