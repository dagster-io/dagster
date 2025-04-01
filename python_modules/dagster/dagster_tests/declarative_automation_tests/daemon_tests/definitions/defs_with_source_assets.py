import dagster as dg


@dg.observable_source_asset(auto_observe_interval_minutes=10)
def foo_source_asset():
    return dg.DataVersion("foo")


always_asset_spec = dg.AssetSpec(key=dg.AssetKey("always"))

defs = dg.Definitions(assets=[foo_source_asset, always_asset_spec])
