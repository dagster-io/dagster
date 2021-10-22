from dagster import job, op, repository
from dagster.core.definitions.run_request import RunRequest
from docs_snippets.concepts.partitions_schedules_sensors.sensors.sensor_alert import (
    email_on_run_failure,
    my_slack_on_run_failure,
    my_slack_on_run_success,
    slack_on_run_failure,
)
from docs_snippets.concepts.partitions_schedules_sensors.sensors.sensors import (
    isolated_run_request,
    log_file_job,
    my_directory_sensor,
    sensor_A,
    sensor_B,
    test_my_directory_sensor_cursor,
    test_sensor,
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


def test_isolated_run_rquest():
    request = next(isolated_run_request())
    assert request
    assert isinstance(request, RunRequest)


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
