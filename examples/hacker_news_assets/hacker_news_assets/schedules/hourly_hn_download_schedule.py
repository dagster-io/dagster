import datetime

from hacker_news_assets.pipelines.download_pipeline import download_comments_and_stories_prod
from dagster.core.definitions.partition import (
    PartitionSetDefinition,
    ScheduleTimeBasedPartitionsDefinition,
    ScheduleType,
)
from dagster.utils.partitions import (
    DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
    create_offset_partition_selector,
)


def get_hourly_download_def_schedule_config(start_time: datetime.datetime):
    return {
        "resources": {
            "partition_start": {"config": start_time.strftime("%Y-%m-%d %H:00:00")},
            "partition_end": {"config": start_time.strftime("%Y-%m-%d %H:59:59")},
        }
    }


def create_hourly_hn_download_schedule():
    pipeline_name = "download_pipeline"
    schedule_name = "hourly_hn_download_schedule"
    start_date = datetime.datetime(2021, 1, 1)
    execution_time = datetime.time(0, 0)
    partitions_def = ScheduleTimeBasedPartitionsDefinition(
        schedule_type=ScheduleType.HOURLY,
        start=start_date,
        execution_time=execution_time,
        fmt=DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
        timezone="UTC",
    )

    partition_set = PartitionSetDefinition(
        name="{}_partitions".format(schedule_name),
        pipeline_name=pipeline_name,  # type: ignore[arg-type]
        run_config_fn_for_partition=lambda partition: get_hourly_download_def_schedule_config(
            partition.value
        ),
        mode="prod",
        partitions_def=partitions_def,
    )

    schedule_def = partition_set.create_schedule_definition(
        schedule_name,
        partitions_def.get_cron_schedule(),
        partition_selector=create_offset_partition_selector(
            execution_time_to_partition_fn=partitions_def.get_execution_time_to_partition_fn(),
        ),
        execution_timezone="UTC",
        decorated_fn=get_hourly_download_def_schedule_config,
        job=download_comments_and_stories_prod,
    )

    return schedule_def