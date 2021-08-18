from dagster import execute_pipeline, pipeline, repository, solid
from dagster.core.definitions.run_request import RunRequest
from docs_snippets_crag.concepts.partitions_schedules_sensors.sensors.sensor_alert import (
    email_on_pipeline_failure,
    my_slack_on_pipeline_failure,
    my_slack_on_pipeline_success,
    slack_on_pipeline_failure,
)
from docs_snippets_crag.concepts.partitions_schedules_sensors.sensors.sensors import (
    isolated_run_request,
    log_file_pipeline,
    my_directory_sensor,
    sensor_A,
    sensor_B,
    test_my_directory_sensor_cursor,
    test_sensor,
)


@solid(config_schema={"fail": bool})
def foo(context):
    if context.solid_config["fail"]:
        raise Exception("This will always fail!")


@pipeline
def your_pipeline_name():
    return foo()


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


def test_pipeline_failure_sensor_def():
    @repository
    def my_repo():
        return [
            my_slack_on_pipeline_failure,
            slack_on_pipeline_failure,
            email_on_pipeline_failure,
            my_slack_on_pipeline_success,
        ]

    assert my_repo.has_sensor_def("my_slack_on_pipeline_failure")
    assert my_repo.has_sensor_def("slack_on_pipeline_failure")
    assert my_repo.has_sensor_def("email_on_pipeline_failure")
    assert my_repo.has_sensor_def("my_slack_on_pipeline_success")


def test_sensor_testing_example():
    test_sensor()
    test_my_directory_sensor_cursor()
