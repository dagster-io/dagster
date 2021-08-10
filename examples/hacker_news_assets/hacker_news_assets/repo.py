from dagster import repository

from .pipelines.download_pipeline import (
    download_comments_and_stories_dev,
    download_comments_and_stories_prod,
)
from .pipelines.story_recommender import story_recommender_dev, story_recommender_prod
from .sensors.hn_tables_updated_sensor import story_recommender_on_hn_table_update
from .sensors.slack_on_pipeline_failure_sensor import make_pipeline_failure_sensor


@repository
def hacker_news_repository():
    pipelines = [
        # download_comments_and_stories_dev,
        download_comments_and_stories_prod,
        # story_recommender_dev,
        story_recommender_prod,
    ]
    sensors = [
        make_pipeline_failure_sensor(base_url="my_dagit_url.com"),
        story_recommender_on_hn_table_update,
    ]

    return pipelines + sensors
