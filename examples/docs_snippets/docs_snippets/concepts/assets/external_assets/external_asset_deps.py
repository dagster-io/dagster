from dagster import AssetsDefinition, Definitions

raw_logs = AssetsDefinition.single("raw_logs")
processed_logs = AssetsDefinition.single("processed_logs", deps=[raw_logs])

defs = Definitions(assets=[raw_logs, processed_logs])
