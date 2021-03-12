from dagster import execute_pipeline
from dagster.core.definitions.job import RunRequest
from docs_snippets.concepts.partitions_schedules_sensors.sensors.sensor_alert import (
    failure_alert_pipeline,
)
from docs_snippets.concepts.partitions_schedules_sensors.sensors.sensors import (
    isolated_run_request,
    log_file_pipeline,
    my_directory_sensor,
    sensor_A,
    sensor_B,
)


def test_failure_alert_pipeline():
    result = execute_pipeline(failure_alert_pipeline, mode="test")
    assert result.success


def test_log_file_pipeline():
    result = execute_pipeline(
        log_file_pipeline, run_config={"solids": {"process_file": {"config": {"filename": "test"}}}}
    )
    assert result.success


def test_my_directory_sensor():
    # TODO: Actually test
    assert my_directory_sensor


def test_isolated_run_rquest():
    request = next(isolated_run_request())
    assert request
    assert isinstance(request, RunRequest)


def test_interval_sensors():
    # TODO: Actually test
    assert sensor_A
    assert sensor_B
