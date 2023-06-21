from dagster import AssetOut, asset, multi_asset


@asset
def a_single_asset():
    return None


@asset(upstream_assets={a_single_asset})
def downstream_of_single_asset():
    return None


@multi_asset(outs={"asset_1": AssetOut(), "asset_2": AssetOut()})
def a_multi_asset():
    return None, None


@asset(upstream_assets={a_multi_asset})
def downstream_of_multi_asset():
    return None
