from dagster import AssetSpec, Definitions, external_assets_from_specs

raw_logs = AssetSpec("raw_logs")
processed_logs = AssetSpec("processed_logs", deps=[raw_logs])

defs = Definitions(assets=external_assets_from_specs([raw_logs, processed_logs]))
