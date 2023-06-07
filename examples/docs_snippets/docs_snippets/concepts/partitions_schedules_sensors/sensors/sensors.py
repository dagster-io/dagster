# isort: skip_file


from dagster import (
    Definitions,
    DefaultSensorStatus,
    SkipReason,
    asset,
    define_asset_job,
    JobSelector,
    CodeLocationSelector,
    DagsterRunStatus,
    run_status_sensor,
    run_failure_sensor,
)


# start_sensor_job_marker
from dagster import op, job, Config


class FileConfig(Config):
    filename: str


@op
def process_file(context, config: FileConfig):
    context.log.info(config.filename)


@job
def log_file_job():
    process_file()


# end_sensor_job_marker

MY_DIRECTORY = "./"

# start_directory_sensor_marker
import os
from dagster import sensor, RunRequest, RunConfig


@sensor(job=log_file_job)
def my_directory_sensor():
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            yield RunRequest(
                run_key=filename,
                run_config=RunConfig(
                    ops={"process_file": FileConfig(filename=filename)}
                ),
            )


# end_directory_sensor_marker


@asset
def my_asset():
    return 1


# start_asset_job_sensor_marker
asset_job = define_asset_job("asset_job", "*")


@sensor(job=asset_job)
def materializes_asset_sensor():
    yield RunRequest(...)


# end_asset_job_sensor_marker


# start_running_in_code
@sensor(job=asset_job, default_status=DefaultSensorStatus.RUNNING)
def my_running_sensor():
    ...


# end_running_in_code


# start_sensor_testing_no
from dagster import validate_run_config


@sensor(job=log_file_job)
def sensor_to_test():
    yield RunRequest(
        run_key="foo",
        run_config={"ops": {"process_file": {"config": {"filename": "foo"}}}},
    )


def test_sensor():
    for run_request in sensor_to_test():
        assert validate_run_config(log_file_job, run_request.run_config)


# end_sensor_testing_no


@job
def my_job():
    pass


# start_interval_sensors_maker


@sensor(job=my_job, minimum_interval_seconds=30)
def sensor_A():
    yield RunRequest(run_key=None, run_config={})


@sensor(job=my_job, minimum_interval_seconds=45)
def sensor_B():
    yield RunRequest(run_key=None, run_config={})


# end_interval_sensors_maker


# start_cursor_sensors_marker
@sensor(job=log_file_job)
def my_directory_sensor_cursor(context):
    last_mtime = float(context.cursor) if context.cursor else 0

    max_mtime = last_mtime
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            fstats = os.stat(filepath)
            file_mtime = fstats.st_mtime
            if file_mtime <= last_mtime:
                continue

            # the run key should include mtime if we want to kick off new runs based on file modifications
            run_key = f"{filename}:{file_mtime}"
            run_config = {"ops": {"process_file": {"config": {"filename": filename}}}}
            yield RunRequest(run_key=run_key, run_config=run_config)
            max_mtime = max(max_mtime, file_mtime)

    context.update_cursor(str(max_mtime))


# end_cursor_sensors_marker

# start_sensor_testing_with_context
from dagster import build_sensor_context


def test_my_directory_sensor_cursor():
    context = build_sensor_context(cursor="0")
    for run_request in my_directory_sensor_cursor(context):
        assert validate_run_config(log_file_job, run_request.run_config)


# end_sensor_testing_with_context


# start_skip_sensors_marker
@sensor(job=log_file_job)
def my_directory_sensor_with_skip_reasons():
    has_files = False
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            yield RunRequest(
                run_key=filename,
                run_config={
                    "ops": {"process_file": {"config": {"filename": filename}}}
                },
            )
            has_files = True
    if not has_files:
        yield SkipReason(f"No files found in {MY_DIRECTORY}.")


# end_skip_sensors_marker

# start_s3_sensors_marker
from dagster_aws.s3.sensor import get_s3_keys


@sensor(job=my_job)
def my_s3_sensor(context):
    since_key = context.cursor or None
    new_s3_keys = get_s3_keys("my_s3_bucket", since_key=since_key)
    if not new_s3_keys:
        return SkipReason("No new s3 files found for bucket my_s3_bucket.")
    last_key = new_s3_keys[-1]
    run_requests = [RunRequest(run_key=s3_key, run_config={}) for s3_key in new_s3_keys]
    context.update_cursor(last_key)
    return run_requests


# end_s3_sensors_marker


@job
def the_job():
    ...


def get_the_db_connection(_):
    ...


defs = Definitions(
    jobs=[my_job, log_file_job],
    sensors=[my_directory_sensor, sensor_A, sensor_B],
)


def send_slack_alert():
    pass


# start_cross_code_location_run_status_sensor


@run_status_sensor(
    monitored_jobs=[CodeLocationSelector(location_name="defs")],
    run_status=DagsterRunStatus.SUCCESS,
)
def code_location_a_sensor():
    # when any job in code_location_a succeeds, this sensor will trigger
    send_slack_alert()


@run_failure_sensor(
    monitored_jobs=[
        JobSelector(
            location_name="defs",
            repository_name="code_location_a",
            job_name="data_update",
        )
    ],
)
def code_location_a_data_update_failure_sensor():
    # when the data_update job in code_location_a fails, this sensor will trigger
    send_slack_alert()


# end_cross_code_location_run_status_sensor


# start_instance_sensor
@run_status_sensor(
    monitor_all_repositories=True,
    run_status=DagsterRunStatus.SUCCESS,
)
def instance_sensor():
    # when any job in the Dagster instance succeeds, this sensor will trigger
    send_slack_alert()


# end_instance_sensor


# start_sensor_logging
@sensor(job=the_job)
def logs_then_skips(context):
    context.log.info("Logging from a sensor!")
    return SkipReason("Nothing to do")


# end_sensor_logging
