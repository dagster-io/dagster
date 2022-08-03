import os

from dagster import AssetSelection, define_asset_job, repository, with_resources

from .assets import (
    ACTIVITY_ANALYTICS,
    CORE,
    RECOMMENDER,
    activity_analytics_assets,
    core_assets,
    dbt_assets,
    recommender_assets,
)
from .jobs import core_assets_schedule
from .resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from .sensors import make_hn_tables_updated_sensor, make_slack_on_failure_sensor

all_assets = [*core_assets, *recommender_assets, *dbt_assets, *activity_analytics_assets]

activity_analytics_assets_sensor = make_hn_tables_updated_sensor(
    # selecting by group allows us to include the activity_analytics assets that are defined in dbt
    define_asset_job("activity_analytics_job", selection=AssetSelection.groups(ACTIVITY_ANALYTICS))
)

recommender_assets_sensor = make_hn_tables_updated_sensor(
    define_asset_job("story_recommender_job", selection=AssetSelection.groups(RECOMMENDER))
)

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
        activity_analytics_assets_sensor,
        recommender_assets_sensor,
        core_assets_schedule,
    ]
    if deployment_name in ["prod", "staging"]:
        definitions.append(make_slack_on_failure_sensor(base_url="my_dagit_url"))

    return definitions
