import os

from dagster import AssetKey, RunRequest, SkipReason, check, sensor


def get_directory_files(directory_name):
    check.str_param(directory_name, "directory_name")
    if not os.path.isdir(directory_name):
        return []

    files = []
    for filename in os.listdir(directory_name):
        filepath = os.path.join(directory_name, filename)
        if not os.path.isfile(filepath):
            continue
        fstats = os.stat(filepath)
        files.append((filename, fstats.st_mtime))

    return files


def get_toys_sensors():

    directory_name = os.environ.get("DAGSTER_TOY_SENSOR_DIRECTORY")

    @sensor(pipeline_name="log_file_pipeline")
    def toy_file_sensor(_):
        if not directory_name:
            yield SkipReason(
                "No directory specified at environment variable `DAGSTER_TOY_SENSOR_DIRECTORY`"
            )
            return

        if not os.path.isdir(directory_name):
            yield SkipReason(f"Directory {directory_name} not found")
            return

        directory_files = get_directory_files(directory_name)
        if not directory_files:
            yield SkipReason(f"No files found in {directory_name}")
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

    @sensor(pipeline_name="log_asset_pipeline")
    def toy_asset_sensor(context):
        events = context.instance.events_for_asset_key(
            AssetKey(["model"]), after_cursor=context.last_run_key, ascending=False, limit=1
        )

        if not events:
            return

        record_id, event = events[0]  # take the most recent materialization
        from_pipeline = event.pipeline_name

        yield RunRequest(
            run_key=str(record_id),
            run_config={
                "solids": {
                    "read_materialization": {
                        "config": {"asset_key": ["model"], "pipeline": from_pipeline}
                    }
                }
            },
        )

    bucket = os.environ.get("DAGSTER_TOY_SENSOR_S3_BUCKET")

    from dagster_aws.s3.sensor import get_s3_keys

    @sensor(pipeline_name="log_s3_pipeline")
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

    return [toy_file_sensor, toy_asset_sensor, toy_s3_sensor]
