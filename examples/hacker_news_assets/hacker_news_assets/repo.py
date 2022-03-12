from dagster import repository, schedule_from_partitions

from .assets import asset_group
from .jobs.activity_stats import activity_stats_job
from .jobs.hacker_news_api_download import download_job
from .jobs.story_recommender import story_recommender_job
from .sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor
from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor


@repository
def hacker_news_assets():
    return [
        asset_group,
        schedule_from_partitions(download_job),
        make_slack_on_failure_sensor(base_url="my_dagit_url.com"),
        make_hn_tables_updated_sensor(activity_stats_job),
        make_hn_tables_updated_sensor(story_recommender_job),
    ]
