from dagster import AssetExecutionContext, Definitions, RunRequest, SkipReason, asset, sensor
from dagster_aws.s3 import S3Resource
from dagster_aws.s3.sensor import get_s3_keys

S3_SOURCE_BUCKET = "source-bucket"
S3_DESTINATION_BUCKET = "destination-bucket"

s3_resource = S3Resource()


@asset(required_resource_keys={"s3"})
def s3_file_backup(context: AssetExecutionContext):
    s3 = context.resources.s3
    s3_key = context.run.run_id
    s3.meta.client.copy({"Bucket": S3_SOURCE_BUCKET, "Key": s3_key}, S3_DESTINATION_BUCKET, s3_key)
    context.log.info(f"Copied {s3_key} from source-bucket to backup-bucket")


@sensor(target=s3_file_backup)
def s3_backup_sensor(context):
    since_key = context.cursor or None
    new_s3_keys = get_s3_keys(S3_SOURCE_BUCKET, since_key=since_key)

    for key in new_s3_keys:
        yield RunRequest(run_key=key)

    if not new_s3_keys:
        yield SkipReason("No new s3 files found for bucket source-bucket.")

    last_key = new_s3_keys[-1]
    context.update_cursor(last_key)


defs = Definitions(
    assets=[s3_file_backup],
    resources={
        "s3": s3_resource,
    },
    sensors=[s3_backup_sensor],
)
