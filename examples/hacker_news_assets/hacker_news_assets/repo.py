from dagster import repository, schedule_from_partitions

from .assets import local_assets, prod_assets, staging_assets
from .jobs.activity_stats import (
    activity_stats_local_job,
    activity_stats_prod_job,
    activity_stats_staging_job,
)
from .jobs.hacker_news_api_download import (
    download_local_job,
    download_prod_job,
    download_staging_job,
)
from .jobs.story_recommender import (
    story_recommender_local_job,
    story_recommender_prod_job,
    story_recommender_staging_job,
)
from .sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor
from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor


@repository
def hacker_news_assets_prod():
    return [
        prod_assets,
        schedule_from_partitions(download_prod_job),
        make_slack_on_failure_sensor(base_url="my_dagit_url.com"),
        make_hn_tables_updated_sensor(activity_stats_prod_job),
        make_hn_tables_updated_sensor(story_recommender_prod_job),
    ]


@repository
def hacker_news_assets_staging():
    return [
        staging_assets,
        schedule_from_partitions(download_staging_job),
        make_slack_on_failure_sensor(base_url="my_dagit_url.com"),
        make_hn_tables_updated_sensor(activity_stats_staging_job),
        make_hn_tables_updated_sensor(story_recommender_staging_job),
    ]


@repository
def hacker_news_assets_local():
    return [local_assets, download_local_job, activity_stats_local_job, story_recommender_local_job]
