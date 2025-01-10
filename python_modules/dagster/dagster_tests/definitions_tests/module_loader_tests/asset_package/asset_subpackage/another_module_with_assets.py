from dagster import AssetKey, AssetSpec, SourceAsset, asset, multi_asset

patsy_cline = SourceAsset(key=AssetKey("patsy_cline"))


@asset
def miles_davis():
    pass


specs = [AssetSpec("a"), AssetSpec("b")]


@multi_asset(specs=specs)
def foo(): ...
