import os

from dagster import repository
from dagster.core.test_utils import environ
from dagster_slack.sensors import make_slack_on_pipeline_failure_sensor


def test_slack_pipeline_failure_sensor_def():
    with environ({"SLACK_TOKEN": "blah"}):

        sensor_name = "my_failure_sensor"

        my_sensor = make_slack_on_pipeline_failure_sensor(
            channel="#foo", slack_token=os.getenv("SLACK_TOKEN"), name=sensor_name
        )
        assert my_sensor.name == sensor_name

        @repository
        def my_repo():
            return [my_sensor]

        assert my_repo.has_sensor_def(sensor_name)
