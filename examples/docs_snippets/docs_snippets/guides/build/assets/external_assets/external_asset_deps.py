from dagster import AssetSpec, Definitions

raw_logs = AssetSpec("raw_logs")
processed_logs = AssetSpec("processed_logs", deps=[raw_logs])

defs = Definitions(assets=[raw_logs, processed_logs])
