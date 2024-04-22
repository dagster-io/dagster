from dagster import AssetsDefinition, Definitions, asset

raw_logs = AssetsDefinition.single("raw_logs")
processed_logs = AssetsDefinition.single("processed_logs", deps=[raw_logs])


@asset(deps=[processed_logs])
def aggregated_logs() -> None:
    # Loads "processed_log" into memory and performs some aggregation
    ...


defs = Definitions(assets=[aggregated_logs, raw_logs, processed_logs])
