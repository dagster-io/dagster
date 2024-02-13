from dagster import AssetSpec, Definitions, external_asset_from_spec

defs = Definitions(assets=[external_asset_from_spec(AssetSpec("file_in_s3"))])
