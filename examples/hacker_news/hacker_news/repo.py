from dagster import build_schedule_from_partitioned_job, repository

from .jobs.dbt_metrics import dbt_prod_job, dbt_staging_job
from .jobs.hacker_news_api_download import (
    download_local_job,
    download_prod_job,
    download_staging_job,
)
from .jobs.story_recommender import story_recommender
from .sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor
from .sensors.slack_on_failure_sensor import make_slack_on_failure_sensor
from hacker_news.resources import RESOURCES_LOCAL, RESOURCES_PROD, RESOURCES_STAGING


@repository
def hacker_news(context):
    if context.deployment_info.deployment_name == "local":
        return [download_local_job, story_recommender, dbt_staging_job, RESOURCES_LOCAL]
    elif context.deployment_info.deployment_name == "staging":
        return [
            build_schedule_from_partitioned_job(download_staging_job),
            make_slack_on_failure_sensor(base_url="my_staging_dagit_url.com"),
            make_hn_tables_updated_sensor(story_recommender),
            make_hn_tables_updated_sensor(dbt_staging_job),
            RESOURCES_STAGING,
        ]

    elif context.deployment_nfo.deployment_name == "prod":
        return [
            build_schedule_from_partitioned_job(download_prod_job),
            make_slack_on_failure_sensor(base_url="my_prod_dagit_url.com"),
            make_hn_tables_updated_sensor(story_recommender),
            make_hn_tables_updated_sensor(dbt_prod_job),
            RESOURCES_PROD,
        ]
    else:
        raise Exception(f"Unexpected deployment {context.deployment_info.deployment_name}")
