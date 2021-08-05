import os
from datetime import datetime

from dagster import Partition
from dagster.core.definitions import PipelineDefinition
from dagster.core.definitions.partition import PartitionScheduleDefinition
from dagster.core.execution.api import create_execution_plan
from hacker_news_assets.pipelines.download_pipeline import download_pipeline
from hacker_news_assets.schedules.hourly_hn_download_schedule import hourly_hn_download_schedule


def assert_partitioned_schedule_builds(
    schedule_def: PartitionScheduleDefinition,
    pipeline_def: PipelineDefinition,
    partition: datetime,
):
    run_config = schedule_def.get_partition_set().run_config_for_partition(Partition(partition))
    create_execution_plan(pipeline_def, run_config=run_config, mode=schedule_def.mode)


def test_daily_download_schedule():
    os.environ["SLACK_DAGSTER_ETL_BOT_TOKEN"] = "something"
    assert_partitioned_schedule_builds(
        hourly_hn_download_schedule, download_pipeline, datetime.strptime("2020-10-01", "%Y-%m-%d")
    )
