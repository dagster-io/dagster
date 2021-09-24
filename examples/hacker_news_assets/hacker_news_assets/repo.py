from dagster import repository

from .pipelines.dbt_pipeline import activity_stats
from .pipelines.download_pipeline import download_comments_and_stories_prod
from .pipelines.story_recommender import story_recommender_prod
from .schedules.hourly_hn_download_schedule import create_hourly_hn_download_schedule
from .sensors.hn_tables_updated_sensor import story_recommender_on_hn_table_update
from .sensors.slack_on_pipeline_failure_sensor import make_pipeline_failure_sensor


@repository
def hacker_news_repository():
    pipelines = [
        activity_stats,
        download_comments_and_stories_prod,
        # story_recommender_prod,
    ]
    sensors_and_schedules = [
        # make_pipeline_failure_sensor(base_url="my_dagit_url.com"),
        # story_recommender_on_hn_table_update,
        # create_hourly_hn_download_schedule(),
    ]

    return pipelines + sensors_and_schedules
