from dagster import (
    AssetKey,
    AssetMaterialization,
    EventMetadataEntry,
    Field,
    Output,
    pipeline,
    solid,
)


@solid(
    config_schema={
        "bucket": Field(str, is_required=True),
        "s3_key": Field(str, is_required=True),
    }
)
def read_s3_key(context):
    s3_key = context.solid_config["s3_key"]
    bucket = context.solid_config["bucket"]
    path = f"s3://{bucket}/{s3_key}"
    context.log.info(f"Found file {path}")
    yield AssetMaterialization(
        asset_key=AssetKey(["log_s3", path]),
        metadata_entries=[EventMetadataEntry.url(path, "S3 path")],
    )
    yield Output(path)


@pipeline(description="Demo pipeline that spits out some file info, given a path")
def log_s3_pipeline():
    read_s3_key()
