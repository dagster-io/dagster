from dagster import build_schedule_from_partitioned_job, repository

from .jobs.dbt_metrics import dbt_prod_job, dbt_staging_job, dbt_sensor
from .jobs.hacker_news_api_download import (
    download_local_job,
    download_prod_job,
    download_staging_job,
    download_schedule,
)
from hacker_news.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING
from .jobs.story_recommender import (
    story_recommender_local_job,
    story_recommender_prod_job,
    story_recommender_staging_job,
    recommender_schedule,
)
from .sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor
from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor


@repository
def hacker_news_local():
    return [
        with_resources(
            [
                download_local_job,
                story_recommender_local_job,
                dbt_staging_job,
            ],
            resource_defs=RESOURCES_LOCAL,
        )
    ]


@repository
def hacker_news_prod():
    return [
        with_resources(
            [download_prod_job, story_recommender_prod_job, dbt_prod_job],
            resource_defs=RESOURCES_PROD,
        ),
        download_schedule,
        recommender_schedule,
        dbt_schedule,
        make_slack_on_failure_sensor(base_url="my_prod_dagit_url.com"),
    ]


# Got rid of staging versions of schedules/sensors here intentionally
@repository
def hacker_news_staging():
    return [
        with_resources(
            [download_prod_job, story_recommender_prod_job, dbt_prod_job],
            resource_defs=RESOURCES_STAGING,
        ),
        make_slack_on_failure_sensor(base_url="my_staging_dagit_url.com"),
    ]
