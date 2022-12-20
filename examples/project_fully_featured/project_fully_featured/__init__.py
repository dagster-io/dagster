import os

from dagster import Definitions

from .assets import activity_analytics_assets, core_assets, dbt_assets, recommender_assets
from .jobs import activity_analytics_assets_sensor, core_assets_schedule, recommender_assets_sensor
from .resources import get_local_resources, get_prod_resources, get_staging_resources
from .sensors import make_slack_on_failure_sensor

all_assets = [*core_assets, *recommender_assets, *dbt_assets, *activity_analytics_assets]

deployment_name = os.environ.get("DAGSTER_DEPLOYMENT", "local")

all_sensors = [activity_analytics_assets_sensor, recommender_assets_sensor]
if deployment_name in ["prod", "staging"]:
    all_sensors.append(make_slack_on_failure_sensor(base_url="my_dagit_url"))


def get_resources():
    if deployment_name == "prod":
        return get_prod_resources()
    elif deployment_name == "staging":
        return get_staging_resources()
    elif deployment_name == "local":
        return get_local_resources()

    raise Exception(f"Invalid deployment name {deployment_name}")


defs = Definitions(
    assets=all_assets,
    resources=get_resources(),
    schedules=[core_assets_schedule],
    sensors=all_sensors,
)
