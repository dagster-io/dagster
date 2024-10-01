from dagster import AssetSpec, Definitions

defs = Definitions(assets=[AssetSpec("file_in_s3")])
