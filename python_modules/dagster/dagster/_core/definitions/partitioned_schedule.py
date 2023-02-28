from typing import Callable, Mapping, NamedTuple, Optional, Union, cast

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError

from .asset_graph import InternalAssetGraph
from .decorators.schedule_decorator import schedule
from .job_definition import JobDefinition
from .partition import PartitionsDefinition
from .run_request import RunRequest, SkipReason
from .schedule_definition import (
    DefaultScheduleStatus,
    ScheduleDefinition,
    ScheduleEvaluationContext,
)
from .time_window_partitions import TimeWindowPartitionsDefinition
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition


class UnresolvedPartitionedAssetScheduleDefinition(NamedTuple):
    """
    Points to an unresolved asset job. The asset selection isn't resolved yet, so we can't resolve
    the PartitionsDefinition, so we can't resolve the schedule cadence.
    """

    name: str
    job: UnresolvedAssetJobDefinition
    description: Optional[str]
    default_status: DefaultScheduleStatus
    minute_of_hour: Optional[int]
    hour_of_day: Optional[int]
    day_of_week: Optional[int]
    day_of_month: Optional[int]
    tags: Optional[Mapping[str, str]]

    def resolve(self, asset_graph: InternalAssetGraph) -> ScheduleDefinition:
        selected_assets = self.job.selection.resolve(asset_graph)
        partitions_defs = {
            cast(PartitionsDefinition, asset_graph.get_partitions_def(asset_key))
            for asset_key in selected_assets
            if asset_graph.get_partitions_def(asset_key) is not None
        }
        if len(partitions_defs) == 0:
            raise DagsterInvalidDefinitionError(
                "Tried to build a partitioned schedule from an asset job, but none of the assets"
                " are partitioned."
            )
        if len(partitions_defs) > 1:
            raise DagsterInvalidDefinitionError(
                "Tried to build a partitioned schedule from an asset job, but some of the assets"
                " have different PartitionsDefinitions."
            )

        time_window_partitions_def = _check_time_window_partitions_def(next(iter(partitions_defs)))

        cron_schedule = time_window_partitions_def.get_cron_schedule(
            self.minute_of_hour, self.hour_of_day, self.day_of_week, self.day_of_month
        )

        return ScheduleDefinition(
            job=self.job,
            name=self.name,
            execution_fn=_get_schedule_evaluation_fn(
                time_window_partitions_def, self.job, self.tags
            ),
            execution_timezone=time_window_partitions_def.timezone,
            cron_schedule=cron_schedule,
        )


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
) -> Union[UnresolvedPartitionedAssetScheduleDefinition, ScheduleDefinition]:
    """
    Creates a schedule from a time window-partitioned job or a job that targets
    time window-partitioned assets.

    The schedule executes at the cadence specified by the partitioning of the job or assets.

    Examples:
        .. code-block:: python

            ######################################
            # Job that targets partitioned assets
            ######################################

            from dagster import (
                DailyPartitionsDefinition,
                asset,
                build_schedule_from_partitioned_job,
                define_asset_job,
            )

            @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
            def asset1():
                ...

            asset1_job = define_asset_job("asset1_job", selection=[asset1])

            # The created schedule will fire daily
            asset1_job_schedule = build_schedule_from_partitioned_job(asset1_job)

            defs = Definitions(assets=[asset1], schedules=[asset1_job_schedule])

            ################
            # Non-asset job
            ################

            from dagster import DailyPartitionsDefinition, build_schedule_from_partitioned_job, jog


            @job(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
            def do_stuff_partitioned():
                ...

            # The created schedule will fire daily
            do_stuff_partitioned_schedule = build_schedule_from_partitioned_job(
                do_stuff_partitioned,
            )

            defs = Definitions(schedules=[do_stuff_partitioned_schedule])
    """
    check.invariant(
        not (day_of_week and day_of_month),
        (
            "Cannot provide both day_of_month and day_of_week parameter to"
            " build_schedule_from_partitioned_job."
        ),
    )

    if isinstance(job, UnresolvedAssetJobDefinition) and job.partitions_def is None:
        return UnresolvedPartitionedAssetScheduleDefinition(
            job=job,
            default_status=default_status,
            name=check.opt_str_param(name, "name", f"{job.name}_schedule"),
            description=check.opt_str_param(description, "description"),
            minute_of_hour=minute_of_hour,
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            tags=tags,
        )
    else:
        partitions_def = job.partitions_def
        if partitions_def is None:
            check.failed("The provided job is not partitioned")

        time_window_partitions_def = _check_time_window_partitions_def(partitions_def)

        cron_schedule = time_window_partitions_def.get_cron_schedule(
            minute_of_hour, hour_of_day, day_of_week, day_of_month
        )

        return schedule(
            cron_schedule=cron_schedule,
            job=job,
            default_status=default_status,
            execution_timezone=time_window_partitions_def.timezone,
            name=check.opt_str_param(name, "name", f"{job.name}_schedule"),
            description=check.opt_str_param(description, "description"),
        )(_get_schedule_evaluation_fn(partitions_def, job, tags))


def _get_schedule_evaluation_fn(
    partitions_def: PartitionsDefinition, job, tags
) -> Callable[[ScheduleEvaluationContext], Union[SkipReason, RunRequest]]:
    def schedule_fn(context):
        # Run for the latest partition. Prior partitions will have been handled by prior ticks.
        partition_key = partitions_def.get_last_partition_key(context.scheduled_execution_time)
        if partition_key is None:
            return SkipReason("The job's PartitionsDefinition has no partitions")

        return job.run_request_for_partition(
            partition_key=partition_key,
            run_key=partition_key,
            tags=tags,
            current_time=context.scheduled_execution_time,
        )

    return schedule_fn


def _check_time_window_partitions_def(
    partitions_def: PartitionsDefinition,
) -> TimeWindowPartitionsDefinition:
    if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
        raise DagsterInvalidDefinitionError(
            "Tried to build a partitioned schedule from an asset job, but the assets"
            " aren't partitioned by time window."
        )

    return partitions_def


schedule_from_partitions = build_schedule_from_partitioned_job
