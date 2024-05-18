from dagster import AssetsDefinition

raw_logs = AssetsDefinition.single("raw_logs")
processed_logs = AssetsDefinition.single("processed_logs", deps=[raw_logs])
