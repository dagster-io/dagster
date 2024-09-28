from dagster import AssetSpec, Definitions, asset

raw_logs = AssetSpec("raw_logs")
processed_logs = AssetSpec("processed_logs", deps=[raw_logs])


@asset(deps=[processed_logs])
def aggregated_logs() -> None:
    # Loads "processed_log" into memory and performs some aggregation
    ...


defs = Definitions(assets=[aggregated_logs, raw_logs, processed_logs])
