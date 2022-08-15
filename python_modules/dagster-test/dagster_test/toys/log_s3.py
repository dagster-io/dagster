from dagster import AssetKey, AssetMaterialization, Field, MetadataValue, Output, graph, op


@op(
    config_schema={
        "bucket": Field(str, is_required=True),
        "s3_key": Field(str, is_required=True),
    }
)
def read_s3_key(context):
    s3_key = context.op_config["s3_key"]
    bucket = context.op_config["bucket"]
    path = f"s3://{bucket}/{s3_key}"
    context.log.info(f"Found file {path}")
    yield AssetMaterialization(
        asset_key=AssetKey(["log_s3", path]),
        metadata={"S3 path": MetadataValue.url(path)},
    )
    yield Output(path)


@graph
def log_s3():
    read_s3_key()


log_s3_job = log_s3.to_job(description="Demo job that spits out some file info, given a path")
