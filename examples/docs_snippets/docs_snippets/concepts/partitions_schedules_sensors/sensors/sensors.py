# isort: skip_file
# pylint: disable=unnecessary-ellipsis

from dagster import (
    repository,
    DefaultSensorStatus,
    SkipReason,
    asset,
    define_asset_job,
    multi_asset_sensor,
)


# start_sensor_job_marker
from dagster import op, job


@op(config_schema={"filename": str})
def process_file(context):
    filename = context.op_config["filename"]
    context.log.info(filename)


@job
def log_file_job():
    process_file()


# end_sensor_job_marker

MY_DIRECTORY = "./"

# start_directory_sensor_marker
import os
from dagster import sensor, RunRequest


@sensor(job=log_file_job)
def my_directory_sensor():
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            yield RunRequest(
                run_key=filename,
                run_config={
                    "ops": {"process_file": {"config": {"filename": filename}}}
                },
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
            run_key = f"{filename}:{str(file_mtime)}"
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

# start_asset_sensor_marker
from dagster import AssetKey, asset_sensor


@asset_sensor(asset_key=AssetKey("my_table"), job=my_job)
def my_asset_sensor(context, asset_event):
    yield RunRequest(
        run_key=context.cursor,
        run_config={
            "ops": {
                "read_materialization": {
                    "config": {
                        "asset_key": asset_event.dagster_event.asset_key.path,
                    }
                }
            }
        },
    )


# end_asset_sensor_marker

# start_custom_multi_asset_sensor_marker
import json
from dagster import EventRecordsFilter, DagsterEventType


@sensor(job=my_job)
def custom_multi_asset_sensor(context):
    cursor_dict = json.loads(context.cursor) if context.cursor else {}
    a_cursor = cursor_dict.get("a")
    b_cursor = cursor_dict.get("b")

    # in this sensor we want to monitor for two different asset events
    a_event_records = context.instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=AssetKey("table_a"),
            after_cursor=a_cursor,
        ),
        ascending=False,
        limit=1,
    )
    b_event_records = context.instance.get_event_records(
        EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            asset_key=AssetKey("table_b"),
            after_cursor=b_cursor,
        ),
        ascending=False,
        limit=1,
    )

    if not a_event_records or not b_event_records:
        return

    # make sure we only generate events if both table_a and table_b have been materialized since
    # the last evaluation.
    yield RunRequest(run_key=None)

    # update the sensor cursor by combining the individual event cursors from the two separate
    # asset event streams
    context.update_cursor(
        json.dumps(
            {
                "a": a_event_records[0].storage_id,
                "b": b_event_records[0].storage_id,
            }
        )
    )


# end_custom_multi_asset_sensor_marker

# start_multi_asset_sensor_marker


@multi_asset_sensor(
    asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")],
    job=my_job,
)
def asset_a_and_b_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        logger_str = (
            f"Assets {asset_events[AssetKey('asset_a')].event_log_entry.dagster_event.asset_key.path} "
            f"and {asset_events[AssetKey('asset_b')].event_log_entry.dagster_event.asset_key.path} materialized"
        )
        yield RunRequest(
            run_key=f"{context.cursor}",
            run_config={"ops": {"logger_op": {"config": {"logger_str": logger_str}}}},
        )
        context.advance_all_cursors()


# end_multi_asset_sensor_marker

# start_multi_asset_sensor_w_skip_reason


@multi_asset_sensor(
    asset_keys=[AssetKey("asset_c")],
    job=my_job,
)
def every_fifth_asset_c_sensor(context):
    # this sensor will return a run request every fifth materialization of asset_c
    asset_events = context.materialization_records_for_key(
        asset_key=AssetKey("asset_c"), limit=5
    )
    if len(asset_events) == 5:
        yield RunRequest(run_key=f"{context.cursor}")
        context.advance_cursor({AssetKey("asset_c"): asset_events[-1]})
    else:
        # you can optionally return a SkipReason
        # we don't update the cursor here since we want to keep fetching the same events until we
        # fetch 5 events
        return SkipReason(f"asset_c only materialized {len(asset_events)} times.")


# end_multi_asset_sensor_w_skip_reason


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


# pylint: disable=unused-variable,reimported
# start_build_resources_example
from dagster import resource, build_resources, sensor


@resource
def the_credentials():
    ...


@resource(required_resource_keys={"credentials"})
def the_db_connection(init_context):
    get_the_db_connection(init_context.resources.credentials)


@sensor(job=the_job)
def uses_db_connection():
    with build_resources(
        {"db_connection": the_db_connection, "credentials": the_credentials}
    ) as resources:
        conn = resources.db_connection
        ...


# end_build_resources_example


@repository
def my_repository():
    return [my_job, log_file_job, my_directory_sensor, sensor_A, sensor_B]
