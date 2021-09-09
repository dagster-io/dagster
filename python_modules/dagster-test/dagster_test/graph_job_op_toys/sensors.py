import os

from dagster import AssetKey, RunRequest, SkipReason, check, sensor
from dagster.core.definitions.decorators.sensor import asset_sensor
from dagster.core.definitions.pipeline_sensor import RunFailureSensorContext, run_failure_sensor
from dagster_test.graph_job_op_toys.error_monster import error_monster_failing_job
from dagster_test.graph_job_op_toys.log_asset import log_asset_job
from dagster_test.graph_job_op_toys.log_file import log_file_job
from dagster_test.graph_job_op_toys.log_s3 import log_s3_job
from slack_sdk import WebClient


def get_directory_files(directory_name, since=None):
    check.str_param(directory_name, "directory_name")
    if not os.path.isdir(directory_name):
        return []

    try:
        since = float(since)
    except (TypeError, ValueError):
        since = None

    files = []
    for filename in os.listdir(directory_name):
        filepath = os.path.join(directory_name, filename)
        if not os.path.isfile(filepath):
            continue
        fstats = os.stat(filepath)
        if not since or fstats.st_mtime > since:
            files.append((filename, fstats.st_mtime))

    return files


def get_toys_sensors():

    directory_name = os.environ.get("DAGSTER_TOY_SENSOR_DIRECTORY")

    @sensor(job=log_file_job)
    def toy_file_sensor(context):
        if not directory_name:
            yield SkipReason(
                "No directory specified at environment variable `DAGSTER_TOY_SENSOR_DIRECTORY`"
            )
            return

        if not os.path.isdir(directory_name):
            yield SkipReason(f"Directory {directory_name} not found")
            return

        directory_files = get_directory_files(directory_name, context.cursor)
        if not directory_files:
            yield SkipReason(f"No new files found in {directory_name} (after {context.cursor})")
            return

        for filename, mtime in directory_files:
            yield RunRequest(
                run_key="{}:{}".format(filename, str(mtime)),
                run_config={
                    "solids": {
                        "read_file": {"config": {"directory": directory_name, "filename": filename}}
                    }
                },
            )

    bucket = os.environ.get("DAGSTER_TOY_SENSOR_S3_BUCKET")

    from dagster_aws.s3.sensor import get_s3_keys

    @sensor(job=log_s3_job)
    def toy_s3_sensor(context):
        if not bucket:
            raise Exception(
                "S3 bucket not specified at environment variable `DAGSTER_TOY_SENSOR_S3_BUCKET`."
            )

        new_s3_keys = get_s3_keys(bucket, since_key=context.last_run_key)
        if not new_s3_keys:
            yield SkipReason(f"No s3 updates found for bucket {bucket}.")
            return

        for s3_key in new_s3_keys:
            yield RunRequest(
                run_key=s3_key,
                run_config={
                    "solids": {"read_s3_key": {"config": {"bucket": bucket, "s3_key": s3_key}}}
                },
            )

    @run_failure_sensor(job_selection=[error_monster_failing_job])
    def custom_slack_on_job_failure(context: RunFailureSensorContext):

        base_url = "http://localhost:3000"

        # TBD: support resources?
        slack_client = WebClient(token=os.environ["SLACK_DAGSTER_ETL_BOT_TOKEN"])

        run_page_url = f"{base_url}/instance/runs/{context.pipeline_run.run_id}"
        channel = "#yuhan-test"
        message = "\n".join(
            [
                f'Pipeline "{context.pipeline_run.pipeline_name}" failed.',
                f"error: {context.failure_event.message}",
                f"mode: {context.pipeline_run.mode}",
                f"run_page_url: {run_page_url}",
            ]
        )

        slack_client.chat_postMessage(
            channel=channel,
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": message}}],
        )

    @asset_sensor(asset_key=AssetKey("model"), job=log_asset_job)
    def toy_asset_sensor(context, asset_event):
        yield RunRequest(
            run_key=context.cursor,
            run_config={
                "ops": {
                    "read_materialization": {
                        "config": {"asset_key": ["model"], "graph": asset_event.pipeline_name}
                    }
                }
            },
        )

    return [
        toy_file_sensor,
        toy_asset_sensor,
        toy_s3_sensor,
        custom_slack_on_job_failure,
    ]
