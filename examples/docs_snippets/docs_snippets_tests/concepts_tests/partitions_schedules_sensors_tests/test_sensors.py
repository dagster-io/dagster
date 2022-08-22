from unittest import mock

from dagster import (
    AssetKey,
    DagsterInstance,
    asset,
    build_multi_asset_sensor_context,
    build_sensor_context,
    job,
    materialize,
    op,
    repository,
)
from docs_snippets.concepts.partitions_schedules_sensors.sensors.sensor_alert import (
    email_on_run_failure,
    my_slack_on_run_failure,
    my_slack_on_run_success,
    slack_on_run_failure,
)
from docs_snippets.concepts.partitions_schedules_sensors.sensors.sensors import (
    asset_a_and_b_sensor,
    every_fifth_asset_c_sensor,
    log_file_job,
    my_directory_sensor,
    my_s3_sensor,
    sensor_A,
    sensor_B,
    test_my_directory_sensor_cursor,
    test_sensor,
    uses_db_connection,
)


@op(config_schema={"fail": bool})
def foo(context):
    if context.solid_config["fail"]:
        raise Exception("This will always fail!")


@job
def your_job_name():
    foo()


def test_log_file_job():
    result = log_file_job.execute_in_process(
        run_config={"ops": {"process_file": {"config": {"filename": "test"}}}}
    )
    assert result.success


def test_my_directory_sensor():
    # TODO: Actually test
    assert my_directory_sensor


def test_interval_sensors():
    # TODO: Actually test
    assert sensor_A
    assert sensor_B


def test_run_failure_sensor_def():
    @repository
    def my_repo():
        return [
            my_slack_on_run_failure,
            slack_on_run_failure,
            email_on_run_failure,
            my_slack_on_run_success,
        ]

    assert my_repo.has_sensor_def("my_slack_on_run_failure")
    assert my_repo.has_sensor_def("slack_on_run_failure")
    assert my_repo.has_sensor_def("email_on_run_failure")
    assert my_repo.has_sensor_def("my_slack_on_run_success")


def test_sensor_testing_example():
    test_sensor()
    test_my_directory_sensor_cursor()


def test_resource_sensor_example():
    uses_db_connection()


def test_s3_sensor():
    with mock.patch(
        "docs_snippets.concepts.partitions_schedules_sensors.sensors.sensors.get_s3_keys"
    ) as mock_s3_keys:
        mock_s3_keys.return_value = ["a", "b", "c", "d", "e"]
        context = build_sensor_context()
        assert context.cursor is None
        run_requests = my_s3_sensor(context)
        assert len(list(run_requests)) == 5
        assert context.cursor == "e"


def test_asset_sensors():
    @asset
    def asset_a():
        return 1

    @asset
    def asset_b():
        return 2

    @asset
    def asset_c():
        return 3

    instance = DagsterInstance.ephemeral()
    materialize([asset_a, asset_b], instance=instance)
    ctx = build_multi_asset_sensor_context(
        asset_keys=[AssetKey("asset_a"), AssetKey("asset_b")], instance=instance
    )
    assert list(asset_a_and_b_sensor(ctx))[0].run_config == {
        "ops": {
            "logger_op": {
                "config": {
                    "logger_str": "Assets ['asset_a'] and ['asset_b'] materialized"
                }
            }
        }
    }

    for _ in range(5):
        materialize([asset_c], instance=instance)

    ctx = build_multi_asset_sensor_context(
        asset_keys=[AssetKey("asset_c")], instance=instance
    )
    assert list(every_fifth_asset_c_sensor(ctx))[0].run_config == {}
