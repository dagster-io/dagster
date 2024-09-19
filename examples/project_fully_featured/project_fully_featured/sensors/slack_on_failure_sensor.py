import os

from dagster import SensorDefinition
from dagster_slack import make_slack_on_run_failure_sensor


def make_slack_on_failure_sensor(base_url: str) -> SensorDefinition:
    return make_slack_on_run_failure_sensor(
        channel="#dogfooding-alert",
        slack_token=os.environ.get("SLACK_DAGSTER_ETL_BOT_TOKEN", ""),
        webserver_base_url=base_url,
    )
