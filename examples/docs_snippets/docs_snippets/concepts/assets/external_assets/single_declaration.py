from dagster import AssetsDefinition, Definitions

defs = Definitions(assets=[AssetsDefinition.single("file_in_s3")])
