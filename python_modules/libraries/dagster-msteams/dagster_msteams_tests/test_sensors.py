import os

from dagster import repository
from dagster._core.definitions.run_status_sensor_definition import RunFailureSensorContext
from dagster._core.test_utils import environ
from dagster_msteams.sensors import make_teams_on_run_failure_sensor


def test_teams_run_failure_sensor_def():
    with environ({"TEAMS_WEBHOOK_URL": "https://some_url_here/"}):
        sensor_name = "my_failure_sensor"

        my_sensor = make_teams_on_run_failure_sensor(
            hook_url=os.getenv("TEAMS_WEBHOOK_URL"),  # pyright: ignore[reportArgumentType]
            name=sensor_name,
        )
        assert my_sensor.name == sensor_name

        @repository
        def my_repo():
            return [my_sensor]

        assert my_repo.has_sensor_def(sensor_name)


def test_teams_run_failure_sensor_with_skip_alert_fn():
    """Test that sensor can be created with skip_alert_fn parameter."""
    with environ({"TEAMS_WEBHOOK_URL": "https://some_url_here/"}):
        sensor_name = "my_failure_sensor_with_skip"

        def should_skip_alert(context: RunFailureSensorContext) -> bool:
            # Skip alert if run has will_retry tag
            return context.dagster_run.tags.get("will_retry") == "true"

        my_sensor = make_teams_on_run_failure_sensor(
            hook_url=os.getenv("TEAMS_WEBHOOK_URL"),  # pyright: ignore[reportArgumentType]
            name=sensor_name,
            skip_alert_fn=should_skip_alert,
        )
        assert my_sensor.name == sensor_name

        @repository
        def my_repo():
            return [my_sensor]

        assert my_repo.has_sensor_def(sensor_name)
