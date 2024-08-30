import dagster as dg


@dg.multi_asset(specs=[dg.AssetSpec("asset_one"), dg.AssetSpec("asset_two")])
def my_multi_asset():
    # materialize both asset_one and asset_two
    ...


defs = dg.Definitions(assets=[my_multi_asset])
