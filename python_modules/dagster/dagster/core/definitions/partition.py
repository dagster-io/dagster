import inspect
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime, time
from enum import Enum
from typing import Callable, List, NamedTuple, Optional, cast

import pendulum
from dagster import check
from dagster.core.definitions.run_request import RunRequest, SkipReason
from dagster.core.definitions.schedule import ScheduleDefinition, ScheduleExecutionContext
from dagster.core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.tags import check_tags
from dagster.seven.compat.pendulum import PendulumDateTime, to_timezone
from dagster.utils import frozenlist, merge_dicts
from dagster.utils.schedules import schedule_execution_time_iterator

from .mode import DEFAULT_MODE_NAME
from .utils import check_valid_name

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


class Partition(namedtuple("_Partition", ("value name"))):
    """
    Partition is the representation of a logical slice across an axis of a pipeline's work

    Args:
        value (Any): The object for this partition
        name (str): Name for this partition
    """

    def __new__(cls, value=None, name=None):
        return super(Partition, cls).__new__(
            cls, name=check.opt_str_param(name, "name", str(value)), value=value
        )


def schedule_partition_range(
    start,
    end,
    cron_schedule,
    fmt,
    timezone,
    execution_time_to_partition_fn,
):
    check.inst_param(start, "start", datetime)
    check.opt_inst_param(end, "end", datetime)
    check.str_param(cron_schedule, "cron_schedule")
    check.str_param(fmt, "fmt")
    check.opt_str_param(timezone, "timezone")
    check.callable_param(execution_time_to_partition_fn, "execution_time_to_partition_fn")

    if end and start > end:
        raise DagsterInvariantViolationError(
            'Selected date range start "{start}" is after date range end "{end}'.format(
                start=start.strftime(fmt),
                end=end.strftime(fmt),
            )
        )

    def _get_schedule_range_partitions(current_time=None):
        check.opt_inst_param(current_time, "current_time", datetime)
        tz = timezone if timezone else "UTC"

        _current_time = current_time if current_time else pendulum.now(tz)

        # Coerce to the definition timezone
        _start = (
            to_timezone(start, tz)
            if isinstance(start, PendulumDateTime)
            else pendulum.instance(start, tz=tz)
        )
        _current_time = (
            to_timezone(_current_time, tz)
            if isinstance(_current_time, PendulumDateTime)
            else pendulum.instance(_current_time, tz=tz)
        )

        # The end partition time should be before the last partition that
        # executes before the current time
        end_partition_time = execution_time_to_partition_fn(_current_time)

        # The partition set has an explicit end time that represents the end of the partition range
        if end:
            _end = (
                to_timezone(end, tz)
                if isinstance(end, PendulumDateTime)
                else pendulum.instance(end, tz=tz)
            )

            # If the explicit end time is before the last partition time,
            # update the end partition time
            end_partition_time = min(_end, end_partition_time)

        end_timestamp = end_partition_time.timestamp()

        partitions = []
        for next_time in schedule_execution_time_iterator(_start.timestamp(), cron_schedule, tz):

            partition_time = execution_time_to_partition_fn(next_time)

            if partition_time.timestamp() > end_timestamp:
                break

            if partition_time.timestamp() < _start.timestamp():
                continue

            partitions.append(Partition(value=partition_time, name=partition_time.strftime(fmt)))

        return partitions

    return _get_schedule_range_partitions


class ScheduleType(Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class PartitionParams(ABC):
    @abstractmethod
    def get_partitions(self, current_time: Optional[datetime] = None) -> List[Partition]:
        ...


class StaticPartitionParams(
    PartitionParams, NamedTuple("_StaticPartitionParams", [("partitions", List[Partition])])
):
    def __new__(cls, partitions: List[Partition]):
        return super(StaticPartitionParams, cls).__new__(
            cls, check.list_param(partitions, "partitions", of_type=Partition)
        )

    def get_partitions(self, current_time: Optional[datetime] = None) -> List[Partition]:
        return self.partitions


class TimeBasedPartitionParams(
    PartitionParams,
    NamedTuple(
        "_TimeBasedPartitionParams",
        [
            ("schedule_type", ScheduleType),
            ("start", datetime),
            ("execution_time", time),
            ("execution_day", Optional[int]),
            ("end", Optional[datetime]),
            ("fmt", Optional[str]),
            ("timezone", Optional[str]),
            ("offset", Optional[int]),
        ],
    ),
):
    def __new__(
        cls,
        schedule_type: ScheduleType,
        start: datetime,
        execution_time: Optional[time] = None,
        execution_day: Optional[int] = None,
        end: Optional[datetime] = None,
        fmt: Optional[str] = None,
        timezone: Optional[str] = None,
        offset: Optional[int] = None,
    ):
        if end is not None:
            check.invariant(
                start <= end,
                f'Selected date range start "{start}" '
                f'is after date range end "{end}"'.format(
                    start=start.strftime(fmt) if fmt is not None else start,
                    end=cast(datetime, end).strftime(fmt) if fmt is not None else end,
                ),
            )
        if schedule_type in [ScheduleType.HOURLY, ScheduleType.DAILY]:
            check.invariant(
                not execution_day,
                f'Execution day should not be provided for schedule type "{schedule_type}"',
            )
        elif schedule_type is ScheduleType.WEEKLY:
            execution_day = execution_day if execution_day is not None else 0
            check.invariant(
                execution_day is not None and 0 <= execution_day <= 6,
                f'Execution day "{execution_day}" must be between 0 and 6 for '
                f'schedule type "{schedule_type}"',
            )
        elif schedule_type is ScheduleType.MONTHLY:
            execution_day = execution_day if execution_day is not None else 1
            check.invariant(
                execution_day is not None and 1 <= execution_day <= 31,
                f'Execution day "{execution_day}" must be between 1 and 31 for '
                f'schedule type "{schedule_type}"',
            )

        return super(TimeBasedPartitionParams, cls).__new__(
            cls,
            check.inst_param(schedule_type, "schedule_type", ScheduleType),
            check.inst_param(start, "start", datetime),
            check.opt_inst_param(execution_time, "execution_time", time, time(0, 0)),
            check.opt_int_param(
                execution_day,
                "execution_day",
            ),
            check.opt_inst_param(end, "end", datetime),
            check.opt_str_param(fmt, "fmt", default=DEFAULT_DATE_FORMAT),
            check.opt_str_param(timezone, "timezone", default="UTC"),
            check.opt_int_param(offset, "offset", default=1),
        )

    def get_partitions(self, current_time: Optional[datetime] = None) -> List[Partition]:
        check.opt_inst_param(current_time, "current_time", datetime)

        partition_fn = schedule_partition_range(
            start=self.start,
            end=self.end,
            cron_schedule=self.get_cron_schedule(),
            fmt=self.fmt,
            timezone=self.timezone,
            execution_time_to_partition_fn=self.get_execution_time_to_partition_fn(),
        )

        return partition_fn(current_time=current_time)

    def get_cron_schedule(self) -> str:
        minute = self.execution_time.minute
        hour = self.execution_time.hour
        day = self.execution_day

        if self.schedule_type is ScheduleType.HOURLY:
            return f"{minute} * * * *"
        elif self.schedule_type is ScheduleType.DAILY:
            return f"{minute} {hour} * * *"
        elif self.schedule_type is ScheduleType.WEEKLY:
            return f"{minute} {hour} * * {day}"
        elif self.schedule_type is ScheduleType.MONTHLY:
            return f"{minute} {hour} {day} * *"
        else:
            check.assert_never(self.schedule_type)

    def get_execution_time_to_partition_fn(self) -> Callable[[datetime], datetime]:
        if self.schedule_type is ScheduleType.HOURLY:
            return lambda d: pendulum.instance(d).subtract(hours=self.offset, minutes=d.minute)
        elif self.schedule_type is ScheduleType.DAILY:
            return lambda d: pendulum.instance(d).subtract(
                days=self.offset, hours=d.hour, minutes=d.minute
            )
        elif self.schedule_type is ScheduleType.WEEKLY:
            execution_day = cast(int, self.execution_day)
            day_difference = (execution_day - (self.start.weekday() + 1)) % 7
            return lambda d: pendulum.instance(d).subtract(
                weeks=self.offset, days=day_difference, hours=d.hour, minutes=d.minute
            )
        elif self.schedule_type is ScheduleType.MONTHLY:
            execution_day = cast(int, self.execution_day)
            return lambda d: pendulum.instance(d).subtract(
                months=self.offset, days=execution_day - 1, hours=d.hour, minutes=d.minute
            )
        else:
            check.assert_never(self.schedule_type)


class DynamicPartitionParams(
    PartitionParams,
    NamedTuple(
        "_DynamicPartitionParams",
        [("partition_fn", Callable[[Optional[datetime]], List[Partition]])],
    ),
):
    def __new__(cls, partition_fn: Callable[[Optional[datetime]], List[Partition]]):
        return super(DynamicPartitionParams, cls).__new__(
            cls, check.callable_param(partition_fn, "partition_fn")
        )

    def get_partitions(self, current_time: Optional[datetime] = None) -> List[Partition]:
        return self.partition_fn(current_time)


class PartitionSetDefinition(
    namedtuple(
        "_PartitionSetDefinition",
        (
            "name pipeline_name partition_fn solid_selection mode "
            "user_defined_run_config_fn_for_partition user_defined_tags_fn_for_partition "
            "partition_params"
        ),
    )
):
    """
    Defines a partition set, representing the set of slices making up an axis of a pipeline

    Args:
        name (str): Name for this partition set
        pipeline_name (str): The name of the pipeline definition
        partition_fn (Optional[Callable[void, List[Partition]]]): User-provided function to define
            the set of valid partition objects.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute with this partition. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing this partition. (default: 'default')
        run_config_fn_for_partition (Callable[[Partition], [Dict]]): A
            function that takes a :py:class:`~dagster.Partition` and returns the run
            configuration that parameterizes the execution for this partition, as a dict
        tags_fn_for_partition (Callable[[Partition], Optional[dict[str, str]]]): A function that
            takes a :py:class:`~dagster.Partition` and returns a list of key value pairs that will
            be added to the generated run for this partition.
        partition_params (Optional[PartitionParams]): A set of parameters used to construct the set
            of valid partition objects.
    """

    def __new__(
        cls,
        name,
        pipeline_name,
        partition_fn=None,
        solid_selection=None,
        mode=None,
        run_config_fn_for_partition=lambda _partition: {},
        tags_fn_for_partition=lambda _partition: {},
        partition_params=None,
    ):
        check.invariant(
            partition_fn is not None or partition_params is not None,
            "One of `partition_fn` or `partition_params` must be supplied.",
        )
        check.invariant(
            not (partition_fn and partition_params),
            "Only one of `partition_fn` or `partition_params` must be supplied.",
        )

        _wrap_partition_fn = None

        if partition_fn is not None:
            partition_fn_param_count = len(inspect.signature(partition_fn).parameters)

            def _wrap_partition(x):
                if isinstance(x, Partition):
                    return x
                if isinstance(x, str):
                    return Partition(x)
                raise DagsterInvalidDefinitionError(
                    "Expected <Partition> | <str>, received {type}".format(type=type(x))
                )

            def _wrap_partition_fn(current_time=None):
                if not current_time:
                    current_time = pendulum.now("UTC")

                check.callable_param(partition_fn, "partition_fn")

                if partition_fn_param_count == 1:
                    obj_list = partition_fn(current_time)
                else:
                    obj_list = partition_fn()

                return [_wrap_partition(obj) for obj in obj_list]

        return super(PartitionSetDefinition, cls).__new__(
            cls,
            name=check_valid_name(name),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            partition_fn=_wrap_partition_fn,
            solid_selection=check.opt_nullable_list_param(
                solid_selection, "solid_selection", of_type=str
            ),
            mode=check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME),
            user_defined_run_config_fn_for_partition=check.callable_param(
                run_config_fn_for_partition, "run_config_fn_for_partition"
            ),
            user_defined_tags_fn_for_partition=check.callable_param(
                tags_fn_for_partition, "tags_fn_for_partition"
            ),
            partition_params=check.opt_inst_param(
                partition_params,
                "partition_params",
                PartitionParams,
                default=DynamicPartitionParams(partition_fn=_wrap_partition_fn)
                if partition_fn is not None
                else None,
            ),
        )

    def run_config_for_partition(self, partition):
        return self.user_defined_run_config_fn_for_partition(partition)

    def tags_for_partition(self, partition):
        user_tags = self.user_defined_tags_fn_for_partition(partition)
        check_tags(user_tags, "user_tags")

        tags = merge_dicts(user_tags, PipelineRun.tags_for_partition_set(self, partition))

        return tags

    def get_partitions(self, current_time=None):
        """Return the set of known partitions.

        Arguments:
            current_time (Optional[datetime]): The evaluation time for the partition function, which
                is passed through to the ``partition_fn`` (if it accepts a parameter).  Defaults to
                the current time in UTC.
        """
        return self.partition_params.get_partitions(current_time)

    def get_partition(self, name):
        for partition in self.get_partitions():
            if partition.name == name:
                return partition

        check.failed("Partition name {} not found!".format(name))

    def get_partition_names(self, current_time=None):
        return [part.name for part in self.get_partitions(current_time)]

    def create_schedule_definition(
        self,
        schedule_name,
        cron_schedule,
        partition_selector,
        should_execute=None,
        environment_vars=None,
        execution_timezone=None,
        description=None,
    ):
        """Create a ScheduleDefinition from a PartitionSetDefinition.

        Arguments:
            schedule_name (str): The name of the schedule.
            cron_schedule (str): A valid cron string for the schedule
            partition_selector (Callable[ScheduleExecutionContext, PartitionSetDefinition], Union[Partition, List[Partition]]):
                Function that determines the partition to use at a given execution time. Can return
                either a single Partition or a list of Partitions. For time-based partition sets,
                will likely be either `identity_partition_selector` or a selector returned by
                `create_offset_partition_selector`.
            should_execute (Optional[function]): Function that runs at schedule execution time that
                determines whether a schedule should execute. Defaults to a function that always returns
                ``True``.
            environment_vars (Optional[dict]): The environment variables to set for the schedule.
            execution_timezone (Optional[str]): Timezone in which the schedule should run. Only works
                with DagsterDaemonScheduler, and must be set when using that scheduler.
            description (Optional[str]): A human-readable description of the schedule.

        Returns:
            PartitionScheduleDefinition: The generated PartitionScheduleDefinition for the partition
                selector
        """

        check.str_param(schedule_name, "schedule_name")
        check.str_param(cron_schedule, "cron_schedule")
        check.opt_callable_param(should_execute, "should_execute")
        check.opt_dict_param(environment_vars, "environment_vars", key_type=str, value_type=str)
        check.callable_param(partition_selector, "partition_selector")
        check.opt_str_param(execution_timezone, "execution_timezone")
        check.opt_str_param(description, "description")

        def _execution_fn(context):
            check.inst_param(context, "context", ScheduleExecutionContext)
            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: f"Error occurred during the execution of partition_selector for schedule {schedule_name}",
            ):
                selector_result = partition_selector(context, self)

            if isinstance(selector_result, SkipReason):
                yield selector_result
                return

            selected_partitions = (
                selector_result
                if isinstance(selector_result, (frozenlist, list))
                else [selector_result]
            )

            check.is_list(selected_partitions, of_type=Partition)

            if not selected_partitions:
                yield SkipReason("Partition selector returned an empty list of partitions.")
                return

            missing_partition_names = [
                partition.name
                for partition in selected_partitions
                if partition.name not in self.get_partition_names(context.scheduled_execution_time)
            ]

            if missing_partition_names:
                yield SkipReason(
                    "Partition selector returned partition"
                    + ("s" if len(missing_partition_names) > 1 else "")
                    + f" not in the partition set: {', '.join(missing_partition_names)}."
                )
                return

            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: f"Error occurred during the execution of should_execute for schedule {schedule_name}",
            ):
                if should_execute and not should_execute(context):
                    yield SkipReason(
                        "should_execute function for {schedule_name} returned false.".format(
                            schedule_name=schedule_name
                        )
                    )
                    return

            for selected_partition in selected_partitions:
                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: f"Error occurred during the execution of run_config_fn for schedule {schedule_name}",
                ):
                    run_config = self.run_config_for_partition(selected_partition)

                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: f"Error occurred during the execution of tags_fn for schedule {schedule_name}",
                ):
                    tags = self.tags_for_partition(selected_partition)
                yield RunRequest(
                    run_key=selected_partition.name if len(selected_partitions) > 0 else None,
                    run_config=run_config,
                    tags=tags,
                )

        return PartitionScheduleDefinition(
            name=schedule_name,
            cron_schedule=cron_schedule,
            pipeline_name=self.pipeline_name,
            tags_fn=None,
            solid_selection=self.solid_selection,
            mode=self.mode,
            should_execute=None,
            environment_vars=environment_vars,
            partition_set=self,
            execution_timezone=execution_timezone,
            execution_fn=_execution_fn,
            description=description,
        )


class PartitionScheduleDefinition(ScheduleDefinition):
    __slots__ = ["_partition_set"]

    def __init__(
        self,
        name,
        cron_schedule,
        pipeline_name,
        tags_fn,
        solid_selection,
        mode,
        should_execute,
        environment_vars,
        partition_set,
        run_config_fn=None,
        execution_timezone=None,
        execution_fn=None,
        description=None,
    ):
        super(PartitionScheduleDefinition, self).__init__(
            name=check_valid_name(name),
            cron_schedule=cron_schedule,
            pipeline_name=pipeline_name,
            run_config_fn=run_config_fn,
            tags_fn=tags_fn,
            solid_selection=solid_selection,
            mode=mode,
            should_execute=should_execute,
            environment_vars=environment_vars,
            execution_timezone=execution_timezone,
            execution_fn=execution_fn,
            description=description,
        )
        self._partition_set = check.inst_param(
            partition_set, "partition_set", PartitionSetDefinition
        )

    def get_partition_set(self):
        return self._partition_set
