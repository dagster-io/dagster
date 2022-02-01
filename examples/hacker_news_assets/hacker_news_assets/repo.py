from dagster import repository, schedule_from_partitions

from .jobs.activity_stats import activity_stats_prod_job, activity_stats_staging_job
from .jobs.hacker_news_api_download import download_prod_job, download_staging_job, download_job
from .jobs.story_recommender import story_recommender_prod_job, story_recommender_staging_job
from .sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor
from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor
from .resources import RESOURCES_PROD, RESOURCES_STAGING
from .asset_collection import asset_collection


stuff = [
    asset_collection,
    download_job,
    asset_collection.schedule_from_partitions(...),
    make_slack_on_failure_sensor(asset_collection, base_url="my_dagit_url.com"),
    make_hn_tables_updated_sensor(subset="activity_subset", name="activity"),
    make_hn_tables_updated_sensor(subset="story_recommender_subset", name="story_recommender"),
]


@repository(resource_defs=RESOURCES_PROD)
def hacker_news_assets_prod():
    return stuff


@repository(resource_defs=RESOURCES_STAGING)
def hacker_news_assets_staging():
    return stuff
