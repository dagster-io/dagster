from dagster import (
    AssetExecutionContext,
    Config,
    Definitions,
    EnvVar,
    RunConfig,
    RunRequest,
    SkipReason,
    asset,
    sensor,
)
from dagster_aws.s3 import S3Resource
from dagster_aws.s3.sensor import get_s3_keys

AWS_S3_BUCKET = "example-source-bucket"
AWS_S3_OBJECT_PREFIX = "example-source-prefix"

s3_resource = S3Resource(
    aws_access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=EnvVar("AWS_SESSION_TOKEN"),
    region_name="us-west-2",
)


class ObjectConfig(Config):
    key: str


@asset()
def s3_file_backup(context: AssetExecutionContext, s3: S3Resource, config: ObjectConfig):
    s3 = context.resources.s3
    context.log.info(f"Reading {config.key}")
    _ = s3.get_object(Bucket=AWS_S3_BUCKET, Key=config.key)  # process object here


@sensor(target=s3_file_backup)
def s3_backup_sensor(context):
    latest_key = context.cursor or None
    unprocessed_object_keys = get_s3_keys(
        bucket=AWS_S3_BUCKET, prefix=AWS_S3_OBJECT_PREFIX, since_key=latest_key
    )

    for key in unprocessed_object_keys:
        yield RunRequest(
            run_key=key, run_config=RunConfig(ops={"s3_file_backup": ObjectConfig(key=key)})
        )

    if not unprocessed_object_keys:
        return SkipReason("No new s3 files found for bucket source-bucket.")

    last_key = unprocessed_object_keys[-1]
    context.update_cursor(last_key)


defs = Definitions(
    assets=[s3_file_backup],
    resources={
        "s3": s3_resource,
    },
    sensors=[s3_backup_sensor],
)
