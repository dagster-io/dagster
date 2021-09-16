from dagster import repository, schedule_from_partitions

from .jobs.hacker_news_api_download import download_prod_job, download_staging_job
from .sensors.download_finished_sensor import (
    dbt_on_hn_download_finished_prod,
    dbt_on_hn_download_finished_staging,
)
from .sensors.hn_tables_updated_sensor import (
    story_recommender_on_hn_table_update_prod,
    story_recommender_on_hn_table_update_staging,
)
from .sensors.slack_on_failure_sensor import make_job_failure_sensor


@repository
def hacker_news_prod():
    return [
        schedule_from_partitions(download_prod_job),
        make_job_failure_sensor(
            base_url="my_dagit_url.com", job_selection=[download_prod_job.name]
        ),
        story_recommender_on_hn_table_update_prod,
        dbt_on_hn_download_finished_prod,
    ]


@repository
def hacker_news_staging():
    return [
        schedule_from_partitions(download_staging_job),
        make_job_failure_sensor(
            base_url="my_dagit_url.com", job_selection=[download_staging_job.name]
        ),
        story_recommender_on_hn_table_update_staging,
        dbt_on_hn_download_finished_staging,
    ]
