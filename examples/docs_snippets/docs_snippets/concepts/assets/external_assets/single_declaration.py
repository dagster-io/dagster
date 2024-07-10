from dagster import AssetsDefinition, AssetSpec

file_in_s3 = AssetsDefinition(specs=[AssetSpec("file_in_s3")])
