import os
from datetime import datetime, timedelta

from dagster import Partition
from dagster.core.definitions import PipelineDefinition
from dagster.core.execution.api import create_execution_plan
from hacker_news.jobs.download_job import download_prod_job, download_staging_job


def assert_partitioned_schedule_builds(
    job_def: PipelineDefinition,
    start: datetime,
    end: datetime,
):
    mode = job_def.mode_definitions[0]
    partition_set = mode.get_partition_set_def(job_def.name)
    run_config = partition_set.run_config_for_partition(Partition((start, end)))
    create_execution_plan(job_def, run_config=run_config)


def test_daily_download_schedule():
    os.environ["SLACK_DAGSTER_ETL_BOT_TOKEN"] = "something"
    start = datetime.strptime("2020-10-01", "%Y-%m-%d")
    end = start + timedelta(hours=1)

    assert_partitioned_schedule_builds(
        download_prod_job,
        start,
        end,
    )
    assert_partitioned_schedule_builds(
        download_staging_job,
        start,
        end,
    )
