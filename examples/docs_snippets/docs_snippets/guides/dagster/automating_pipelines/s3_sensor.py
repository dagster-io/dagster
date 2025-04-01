# ruff: isort: skip_file
import dagster as dg

from dagster_aws.s3.sensor import get_s3_keys


@dg.op(config_schema={"filename": str})
def process_file(context: dg.OpExecutionContext):
    filename = context.op_config["filename"]
    context.log.info(filename)


@dg.job
def log_file_job():
    process_file()


# s3_sensor_start
from dagster_aws.s3.sensor import get_s3_keys


@dg.sensor(job=log_file_job)
def my_s3_sensor(context):
    since_key = context.cursor or None
    new_s3_keys = get_s3_keys("my_s3_rfp_bucket", since_key=since_key)
    if not new_s3_keys:
        return dg.SkipReason("No new s3 files found for bucket my_s3_rfp_bucket.")
    last_key = new_s3_keys[-1]
    run_requests = [
        dg.RunRequest(run_key=s3_key, run_config={}) for s3_key in new_s3_keys
    ]
    context.update_cursor(last_key)
    return run_requests


# s3_sensor_end
