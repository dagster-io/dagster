from dagster import repository

from ..sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor
from ..sensors.slack_on_failure_sensor import make_slack_on_failure_sensor
from .hourly_hn_download_schedule import hourly_hn_download_schedule
from .pipelines.dbt_pipeline import dbt_pipeline
from .pipelines.download_pipeline import download_pipeline
from .pipelines.story_recommender import story_recommender

# Creates a hacker news reference repository using the legacy dagster APIs of pipeline, solid,
# and mode.


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
        make_slack_on_failure_sensor(base_url="my_dagit_url.com"),
        make_hn_tables_updated_sensor(pipeline_name="download_pipeline", mode="prod"),
        make_hn_tables_updated_sensor(pipeline_name="dbt_pipeline", mode="prod"),
    ]

    return pipelines + schedules + sensors
