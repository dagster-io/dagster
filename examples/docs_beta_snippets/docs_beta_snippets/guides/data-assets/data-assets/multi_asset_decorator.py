import dagster as dg


@dg.multi_asset(specs=[dg.AssetSpec("asset_one"), dg.AssetSpec("asset_two")])
def my_multi_asset():
    dg.MaterializeResult(asset_key="asset_one", metadata={"num_rows": 10})
    dg.MaterializeResult(asset_key="asset_two", metadata={"num_rows": 24})


defs = dg.Definitions(assets=[my_multi_asset])
