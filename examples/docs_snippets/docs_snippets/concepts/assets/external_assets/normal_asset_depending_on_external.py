from dagster import AssetsDefinition, AssetSpec, asset

external_log_assets = AssetsDefinition(
    specs=[
        AssetSpec("raw_logs"),
        AssetSpec("processed_logs", deps=["raw_logs"]),
    ]
)


@asset(deps=["processed_logs"])
def aggregated_logs() -> None:
    # Loads "processed_log" into memory and performs some aggregation
    ...
