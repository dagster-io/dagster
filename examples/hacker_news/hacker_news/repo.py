from dagster import repository
from hacker_news.pipelines.story_recommender import story_recommender

from .pipelines.download_pipeline import download_pipeline
from .schedules.hourly_hn_download_schedule import hourly_hn_download_schedule
from .sensors.hn_tables_updated_sensor import story_recommender_on_hn_table_update


@repository
def hacker_news_repository():
    pipelines = [
        download_pipeline,
        story_recommender,
    ]
    schedules = [
        hourly_hn_download_schedule,
    ]
    sensors = [
        story_recommender_on_hn_table_update,
    ]

    return pipelines + schedules + sensors
