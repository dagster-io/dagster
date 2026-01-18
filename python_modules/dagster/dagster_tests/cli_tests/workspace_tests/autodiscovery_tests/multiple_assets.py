import dagster as dg

source_asset = dg.SourceAsset(dg.AssetKey("source_asset"))


@dg.asset
def asset1(source_asset):
    assert source_asset


@dg.asset
def asset2():
    pass
