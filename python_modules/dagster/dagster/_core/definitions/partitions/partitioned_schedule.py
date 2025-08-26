from collections.abc import Mapping
from typing import Any, Callable, Optional, Union, cast

from dagster_shared.record import copy, record
from typing_extensions import Self

import dagster._check as check
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.definition.multi import MultiPartitionsDefinition
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.definition.static import StaticPartitionsDefinition
from dagster._core.definitions.partitions.definition.time_window import (
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.utils.multi import (
    get_time_partitions_def,
    has_one_dimension_time_window_partitioning,
)
from dagster._core.definitions.run_request import RunRequest, SkipReason
from dagster._core.definitions.schedule_definition import (
    DefaultScheduleStatus,
    RunRequestIterator,
    ScheduleDefinition,
    ScheduleEvaluationContext,
)
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import DagsterInvalidDefinitionError


@record
class UnresolvedPartitionedAssetScheduleDefinition:
    """Points to an unresolved asset job. The asset selection isn't resolved yet, so we can't resolve
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
    metadata: Optional[Mapping[str, Any]]

    def resolve(self, resolved_job: JobDefinition) -> ScheduleDefinition:
        partitions_def = resolved_job.partitions_def
        if partitions_def is None:
            check.failed(
                f"Job '{resolved_job.name}' provided to build_schedule_from_partitioned_job must"
                " contain partitioned assets or a partitions definition."
            )

        partitions_def = _check_valid_schedule_partitions_def(partitions_def)
        time_partitions_def = check.not_none(get_time_partitions_def(partitions_def))

        return schedule(
            name=self.name,
            cron_schedule=time_partitions_def.get_cron_schedule(
                self.minute_of_hour, self.hour_of_day, self.day_of_week, self.day_of_month
            ),
            job=resolved_job,
            default_status=self.default_status,
            execution_timezone=time_partitions_def.timezone,
            description=self.description,
            metadata=self.metadata,
        )(_get_schedule_evaluation_fn(partitions_def, resolved_job, self.tags))

    def with_metadata(self, metadata: RawMetadataMapping) -> Self:
        return copy(self, metadata=metadata)


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
    cron_schedule: Optional[str] = None,
    execution_timezone: Optional[str] = None,
    metadata: Optional[RawMetadataMapping] = None,
) -> Union[UnresolvedPartitionedAssetScheduleDefinition, ScheduleDefinition]:
    """Creates a schedule from a job that targets
    time window-partitioned or statically-partitioned assets. The job can also be
    multi-partitioned, as long as one of the partition dimensions is time-partitioned.

    The schedule executes at the cadence specified by the time partitioning of the job or assets.

    **Example:**
        .. code-block:: python

            ######################################
            # Job that targets partitioned assets
            ######################################

            from dagster import (
                DailyPartitionsDefinition,
                asset,
                build_schedule_from_partitioned_job,
                define_asset_job,
                Definitions,
            )

            @asset(partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"))
            def asset1():
                ...

            asset1_job = define_asset_job("asset1_job", selection=[asset1])

            # The created schedule will fire daily
            asset1_job_schedule = build_schedule_from_partitioned_job(asset1_job)

            Definitions(assets=[asset1], schedules=[asset1_job_schedule])

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

            Definitions(schedules=[do_stuff_partitioned_schedule])
    """
    check.invariant(
        not (day_of_week and day_of_month),
        "Cannot provide both day_of_month and day_of_week parameter to"
        " build_schedule_from_partitioned_job.",
    )

    check.invariant(
        not (
            (cron_schedule or execution_timezone)
            and (
                day_of_month is not None
                or day_of_week is not None
                or hour_of_day is not None
                or minute_of_hour is not None
            )
        ),
        "Cannot provide both cron_schedule / execution_timezone parameters and"
        " day_of_month / day_of_week / hour_of_day / minute_of_hour parameters to"
        " build_schedule_from_partitioned_job.",
    )

    if isinstance(job, UnresolvedAssetJobDefinition) and job.partitions_def is None:
        if cron_schedule or execution_timezone:
            check.failed(
                "Cannot provide cron_schedule or execution_timezone to"
                " build_schedule_from_partitioned_job for a time-partitioned job."
            )

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
            metadata=metadata,
        )
    else:
        partitions_def = job.partitions_def
        if partitions_def is None:
            check.failed("The provided job is not partitioned")

        partitions_def = _check_valid_schedule_partitions_def(partitions_def)
        if isinstance(partitions_def, StaticPartitionsDefinition):
            check.not_none(
                cron_schedule,
                "Creating a schedule from a static partitions definition requires a cron schedule",
            )
            should_execute = None
        else:
            if cron_schedule or execution_timezone:
                check.failed(
                    "Cannot provide cron_schedule or execution_timezone to"
                    " build_schedule_from_partitioned_job for a time-partitioned job."
                )
            time_partitions_def = check.not_none(get_time_partitions_def(partitions_def))
            cron_schedule = time_partitions_def.get_cron_schedule(
                minute_of_hour, hour_of_day, day_of_week, day_of_month
            )
            execution_timezone = time_partitions_def.timezone
            if time_partitions_def.exclusions:

                def _should_execute(context: ScheduleEvaluationContext) -> bool:
                    with partition_loading_context(
                        effective_dt=context.scheduled_execution_time,
                        dynamic_partitions_store=context.instance
                        if context.instance_ref is not None
                        else None,
                    ):
                        window = time_partitions_def.get_last_partition_window_ignoring_exclusions()
                        if not window:
                            return True
                        return not time_partitions_def.is_window_start_excluded(window.start)

                should_execute = _should_execute
            else:
                should_execute = None

        return schedule(
            cron_schedule=cron_schedule,  # type: ignore[arg-type]
            job=job,
            default_status=default_status,
            execution_timezone=execution_timezone,
            name=check.opt_str_param(name, "name", f"{job.name}_schedule"),
            description=check.opt_str_param(description, "description"),
            should_execute=should_execute,
        )(_get_schedule_evaluation_fn(partitions_def, job, tags))


def _get_schedule_evaluation_fn(
    partitions_def: PartitionsDefinition,
    job: Union[JobDefinition, UnresolvedAssetJobDefinition],
    tags: Optional[Mapping[str, str]] = None,
) -> Callable[[ScheduleEvaluationContext], Union[SkipReason, RunRequest, RunRequestIterator]]:
    def schedule_fn(context):
        # Run for the latest partition. Prior partitions will have been handled by prior ticks.
        with partition_loading_context(
            effective_dt=context._scheduled_execution_time,  # noqa
            dynamic_partitions_store=context.instance if context.instance_ref is not None else None,
        ):
            if isinstance(partitions_def, TimeWindowPartitionsDefinition):
                partition_key = partitions_def.get_last_partition_key()
                if partition_key is None:
                    return SkipReason("The job's PartitionsDefinition has no partitions")

                return job.run_request_for_partition(
                    partition_key=partition_key, run_key=partition_key, tags=tags
                )
            if isinstance(partitions_def, StaticPartitionsDefinition):
                return [
                    job.run_request_for_partition(partition_key=key, run_key=key, tags=tags)
                    for key in partitions_def.get_partition_keys()
                ]
            else:
                check.invariant(isinstance(partitions_def, MultiPartitionsDefinition))
                time_window_dimension = partitions_def.time_window_dimension  # pyright: ignore[reportAttributeAccessIssue]
                partition_key = time_window_dimension.partitions_def.get_last_partition_key()
                if partition_key is None:
                    return SkipReason("The job's PartitionsDefinition has no partitions")

                return [
                    job.run_request_for_partition(partition_key=key, run_key=key, tags=tags)
                    for key in partitions_def.get_multipartition_keys_with_dimension_value(  # pyright: ignore[reportAttributeAccessIssue]
                        time_window_dimension.name, partition_key
                    )
                ]

    return schedule_fn  # pyright: ignore[reportReturnType]


def _check_valid_schedule_partitions_def(
    partitions_def: PartitionsDefinition,
) -> Union[
    TimeWindowPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
]:
    if not has_one_dimension_time_window_partitioning(partitions_def) and not isinstance(
        partitions_def, StaticPartitionsDefinition
    ):
        raise DagsterInvalidDefinitionError(
            "Tried to build a partitioned schedule from an asset job, but received an invalid"
            " partitions definition. The permitted partitions definitions are: \n1."
            " TimeWindowPartitionsDefinition\n2. MultiPartitionsDefinition with a single"
            " TimeWindowPartitionsDefinition dimension\n3. StaticPartitionsDefinition"
        )

    return cast(
        "Union[TimeWindowPartitionsDefinition, MultiPartitionsDefinition, StaticPartitionsDefinition]",
        partitions_def,
    )


schedule_from_partitions = build_schedule_from_partitioned_job
