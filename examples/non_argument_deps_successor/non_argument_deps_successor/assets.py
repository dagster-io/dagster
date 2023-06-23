from dagster import AssetKey, AssetOut, asset, multi_asset


# single asset case, passing by AssetsDefinition works
@asset
def a_single_asset():
    return None


@asset(deps=[a_single_asset])
def downstream_of_single_asset():
    return None


# multi asset case, passing by AssetsDefinitions does not work, so pass by CoercibleToAssetKey instead
@multi_asset(outs={"asset_1": AssetOut(), "asset_2": AssetOut()})
def a_multi_asset():
    return None, None


@asset(deps=["asset_1", AssetKey("asset_2")])
def downstream_of_multi_asset():
    return None
