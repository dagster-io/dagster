from contextlib import suppress

from dagster import build_sensor_context, execute_pipeline, pipeline, reconstructable, solid
from dagster.core.definitions.run_request import RunRequest
from dagster.core.test_utils import instance_for_test
from docs_snippets.concepts.partitions_schedules_sensors.sensors.sensor_alert import (
    failure_alert_pipeline,
    pipeline_failure_sensor,
)
from docs_snippets.concepts.partitions_schedules_sensors.sensors.sensors import (
    isolated_run_request,
    log_file_pipeline,
    my_directory_sensor,
    sensor_A,
    sensor_B,
    test_sensor,
)


@solid(config_schema={"fail": bool})
def foo(context):
    if context.solid_config["fail"]:
        raise Exception("This will always fail!")


@pipeline
def your_pipeline_name():
    return foo()


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


def test_pipeline_failure_sensor_has_request():
    with instance_for_test() as instance:
        with suppress(Exception):
            execute_pipeline(
                reconstructable(your_pipeline_name),
                run_config={"solids": {"foo": {"config": {"fail": True}}}},
                instance=instance,
            )

        context = build_sensor_context(instance)
        requests = pipeline_failure_sensor.evaluate_tick(context)
        assert len(requests) == 1


def test_pipeline_failure_sensor_has_no_request():
    with instance_for_test() as instance:
        execute_pipeline(
            reconstructable(your_pipeline_name),
            run_config={"solids": {"foo": {"config": {"fail": False}}}},
            instance=instance,
        )

        context = build_sensor_context(instance)
        requests = pipeline_failure_sensor.evaluate_tick(context)
        assert len(requests) == 0


def test_sensor_testing_example():
    test_sensor()
