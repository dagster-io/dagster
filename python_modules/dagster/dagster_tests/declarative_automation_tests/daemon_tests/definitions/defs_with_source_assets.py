import dagster as dg

foo_source_asset = dg.SourceAsset(
    key="foo_source_asset",
    observe_fn=lambda context: dg.DataVersion("foo"),
    auto_observe_interval_minutes=10,
)


always_asset_spec = dg.AssetSpec(key=dg.AssetKey("always"))

defs = dg.Definitions(assets=[foo_source_asset, always_asset_spec])
