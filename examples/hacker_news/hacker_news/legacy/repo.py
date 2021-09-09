from dagster import repository

from ..schedules.hourly_hn_download_schedule import hourly_hn_download_schedule
from ..sensors.download_pipeline_finished_sensor import dbt_on_hn_download_finished
from ..sensors.hn_tables_updated_sensor import story_recommender_on_hn_table_update
from ..sensors.slack_on_failure_sensor import make_pipeline_failure_sensor
from .pipelines.dbt_pipeline import dbt_pipeline
from .pipelines.download_pipeline import download_pipeline
from .pipelines.story_recommender import story_recommender


@repository
def hacker_news_legacy():
    pipelines = [
        download_pipeline,
        story_recommender,
        dbt_pipeline,
    ]
    schedules = [
        hourly_hn_download_schedule,
    ]
    sensors = [
        make_pipeline_failure_sensor(base_url="my_dagit_url.com"),
        story_recommender_on_hn_table_update,
        dbt_on_hn_download_finished,
    ]

    return pipelines + schedules + sensors
