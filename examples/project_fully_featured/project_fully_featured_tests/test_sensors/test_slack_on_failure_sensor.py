from dagster import repository

from project_fully_featured.sensors.slack_on_failure_sensor import (
    make_slack_on_failure_sensor,
)


def test_slack_on_failure_def():
    @repository
    def my_repo_local():
        return [make_slack_on_failure_sensor("localhost")]

    @repository
    def my_repo_staging():
        return [make_slack_on_failure_sensor("https://dev.something.com")]

    @repository
    def my_repo_prod():
        return [make_slack_on_failure_sensor("https://prod.something.com")]

    assert my_repo_local.has_sensor_def("slack_on_run_failure")
    assert my_repo_staging.has_sensor_def("slack_on_run_failure")
    assert my_repo_prod.has_sensor_def("slack_on_run_failure")
