from dagster import AssetsDefinition, AssetSpec

external_log_assets = AssetsDefinition(
    specs=[
        AssetSpec("raw_logs"),
        AssetSpec("processed_logs", deps=["raw_logs"]),
    ]
)
