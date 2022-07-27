import os

from dagster_msteams.sensors import make_teams_on_run_failure_sensor

from dagster import repository
from dagster.core.test_utils import environ


def test_teams_run_failure_sensor_def():
    with environ({"TEAMS_WEBHOOK_URL": "https://some_url_here/"}):

        sensor_name = "my_failure_sensor"

        my_sensor = make_teams_on_run_failure_sensor(
            hook_url=os.getenv("TEAMS_WEBHOOK_URL"),
            name=sensor_name,
        )
        assert my_sensor.name == sensor_name

        @repository
        def my_repo():
            return [my_sensor]

        assert my_repo.has_sensor_def(sensor_name)
