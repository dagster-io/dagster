from typing import Mapping, Optional, Union, cast

import dagster._check as check

from .decorators.schedule_decorator import schedule
from .job_definition import JobDefinition
from .run_request import SkipReason
from .schedule_definition import DefaultScheduleStatus, ScheduleDefinition
from .time_window_partitions import TimeWindowPartitionsDefinition
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition


def build_schedule_from_partitioned_job(
    job: Union[JobDefinition, UnresolvedAssetJobDefinition],
    description: Optional[str] = None,
    name: Optional[str] = None,
    minute_of_hour: Optional[int] = None,
    hour_of_day: Optional[int] = None,
    day_of_week: Optional[int] = None,
    day_of_month: Optional[int] = None,
    default_status: DefaultScheduleStatus = DefaultScheduleStatus.STOPPED,
    tags: Optional[Mapping[str, str]] = None,
) -> ScheduleDefinition:
    """
    Creates a schedule from a time window-partitioned job.

    The schedule executes at the cadence specified by the partitioning of the given job.
    """
    check.invariant(
        not (day_of_week and day_of_month),
        (
            "Cannot provide both day_of_month and day_of_week parameter to"
            " build_schedule_from_partitioned_job."
        ),
    )
    partitions_def = job.partitions_def
    if partitions_def is None:
        check.failed("The provided job is not partitioned")
    if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
        check.failed(
            "The provided job's partitions definition is not a TimeWindowPartitionsDefinition"
        )

    time_window_partitions_def = cast(TimeWindowPartitionsDefinition, partitions_def)

    cron_schedule = time_window_partitions_def.get_cron_schedule(
        minute_of_hour, hour_of_day, day_of_week, day_of_month
    )

    @schedule(
        cron_schedule=cron_schedule,
        job=job,
        default_status=default_status,
        execution_timezone=time_window_partitions_def.timezone,
        name=check.opt_str_param(name, "name", f"{job.name}_schedule"),
        description=check.opt_str_param(description, "description"),
    )
    def schedule_def(context):
        # Run for the latest partition. Prior partitions will have been handled by prior ticks.
        partition_key = partitions_def.get_last_partition_key(context.scheduled_execution_time)
        if partition_key is None:
            return SkipReason("The job's PartitionsDefinition has no partitions")

        yield job.run_request_for_partition(
            partition_key=partition_key, run_key=partition_key, tags=tags
        )

    return schedule_def


schedule_from_partitions = build_schedule_from_partitioned_job
