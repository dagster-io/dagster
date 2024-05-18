from dagster import AssetsDefinition, asset

raw_logs = AssetsDefinition.single("raw_logs")
processed_logs = AssetsDefinition.single("processed_logs", deps=[raw_logs])


@asset(deps=[processed_logs])
def aggregated_logs() -> None:
    # Loads "processed_log" into memory and performs some aggregation
    ...
