import os

from dagster import repository, with_resources

from .assets import activity_analytics_assets, core_assets, dbt_assets, recommender_assets
from .jobs import activity_analytics_assets_sensor, core_assets_schedule, recommender_assets_sensor
from .resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from .sensors import make_slack_on_failure_sensor

all_assets = [*core_assets, *recommender_assets, *dbt_assets, *activity_analytics_assets]

all_jobs = [
    activity_analytics_assets_sensor,
    core_assets_schedule,
    recommender_assets_sensor,
]

resource_defs_by_deployment_name = {
    "prod": RESOURCES_PROD,
    "staging": RESOURCES_STAGING,
    "local": RESOURCES_LOCAL,
}


@repository
def hacker_news_repository():
    deployment_name = os.environ.get("DAGSTER_DEPLOYMENT", "local")
    resource_defs = resource_defs_by_deployment_name[deployment_name]

    definitions = [
        with_resources(all_assets, resource_defs),
        *all_jobs,
    ]
    if deployment_name in ["prod", "staging"]:
        definitions.append(make_slack_on_failure_sensor(base_url="my_dagit_url"))

    return definitions
