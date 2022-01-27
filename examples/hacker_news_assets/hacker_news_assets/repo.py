from dagster import repository
from dagster.core.asset_defs import (
    ScheduledAssetsJob,
    SensoredAssetsJob,
    gather_assets_from_package,
)
from hacker_news_assets import assets as assets_pkg

from .resources import RESOURCES_PROD, RESOURCES_STAGING
from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor

assets = gather_assets_from_package(assets_pkg)
download_job = ScheduledAssetsJob(
    asset_selection=["*comments", "*stories"], infer_schedule_from_partitions=True
)
activity_stats_job = SensoredAssetsJob()
story_recommender_job = SensoredAssetsJob(
    asset_selection=[
        "*recommender_model",
        "*component_top_stories",
        "*user_top_recommended_stories",
        "-*comments",
        "-*stories",
    ]
)

shared_repo_defs = [assets, download_job, activity_stats_job, story_recommender_job]


@repository(resource_defs=RESOURCES_PROD)
def hacker_news_assets_prod():
    return shared_repo_defs + [make_slack_on_failure_sensor(base_url="my_prod_dagit_url.com")]


@repository(resource_defs=RESOURCES_STAGING)
def hacker_news_assets_staging():
    return shared_repo_defs + [make_slack_on_failure_sensor(base_url="my_staging_dagit_url.com")]
