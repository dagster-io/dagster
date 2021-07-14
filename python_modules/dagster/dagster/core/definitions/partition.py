import inspect
from abc import ABC, abstractmethod
from datetime import datetime, time
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, NamedTuple, Optional, TypeVar, Union, cast

import pendulum
from dagster import check

from ...seven.compat.pendulum import PendulumDateTime, to_timezone
from ...utils import frozenlist, merge_dicts
from ...utils.schedules import schedule_execution_time_iterator
from ..decorator_utils import get_function_params
from ..errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from ..storage.pipeline_run import PipelineRun
from ..storage.tags import check_tags
from .mode import DEFAULT_MODE_NAME
from .run_request import RunRequest, SkipReason
from .schedule import ScheduleDefinition, ScheduleEvaluationContext
from .utils import check_valid_name

DEFAULT_DATE_FORMAT = "%Y-%m-%d"

T = TypeVar("T")


class Partition(Generic[T]):
    """
    Partition is the representation of a logical slice across an axis of a pipeline's work

    Args:
        value (Any): The object for this partition
        name (str): Name for this partition
    """

    def __init__(self, value: T, name: Optional[str] = None):
        self._value = value
        self._name = cast(str, check.opt_str_param(name, "name", str(value)))

    @property
    def value(self) -> T:
        return self._value

    @property
    def name(self) -> str:
        return self._name


def schedule_partition_range(
    start: datetime,
    end: Optional[datetime],
    cron_schedule: str,
    fmt: str,
    timezone: Optional[str],
    execution_time_to_partition_fn: Callable,
    current_time: Optional[datetime],
) -> List[Partition[datetime]]:
    if end and start > end:
        raise DagsterInvariantViolationError(
            'Selected date range start "{start}" is after date range end "{end}'.format(
                start=start.strftime(fmt),
                end=end.strftime(fmt),
            )
        )

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

    partitions: List[Partition[datetime]] = []
    for next_time in schedule_execution_time_iterator(_start.timestamp(), cron_schedule, tz):

        partition_time = execution_time_to_partition_fn(next_time)

        if partition_time.timestamp() > end_timestamp:
            break

        if partition_time.timestamp() < _start.timestamp():
            continue

        partitions.append(Partition(value=partition_time, name=partition_time.strftime(fmt)))

    return partitions


class ScheduleType(Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class PartitionsDefinition(ABC, Generic[T]):
    @abstractmethod
    def get_partitions(self, current_time: Optional[datetime] = None) -> List[Partition[T]]:
        ...


class StaticPartitionsDefinition(PartitionsDefinition[T]):  # pylint: disable=unsubscriptable-object
    def __init__(self, partitions: List[Partition[T]]):
        self._partitions = check.list_param(partitions, "partitions", of_type=Partition)

    def get_partitions(
        self, current_time: Optional[datetime] = None  # pylint: disable=unused-argument
    ) -> List[Partition[T]]:
        return self._partitions


class ScheduleTimeBasedPartitionsDefinition(
    PartitionsDefinition[datetime],  # pylint: disable=unsubscriptable-object
    NamedTuple(
        "_ScheduleTimeBasedPartitionsDefinition",
        [
            ("schedule_type", ScheduleType),
            ("start", datetime),
            ("execution_time", time),
            ("execution_day", Optional[int]),
            ("end", Optional[datetime]),
            ("fmt", str),
            ("timezone", Optional[str]),
            ("offset", Optional[int]),
        ],
    ),
):
    """Computes the partitions backwards from the scheduled execution times"""

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

        return super(ScheduleTimeBasedPartitionsDefinition, cls).__new__(
            cls,
            check.inst_param(schedule_type, "schedule_type", ScheduleType),
            check.inst_param(start, "start", datetime),
            check.opt_inst_param(execution_time, "execution_time", time, time(0, 0)),
            check.opt_int_param(
                execution_day,
                "execution_day",
            ),
            check.opt_inst_param(end, "end", datetime),
            cast(str, check.opt_str_param(fmt, "fmt", default=DEFAULT_DATE_FORMAT)),
            check.opt_str_param(timezone, "timezone", default="UTC"),
            check.opt_int_param(offset, "offset", default=1),
        )

    def get_partitions(self, current_time: Optional[datetime] = None) -> List[Partition[datetime]]:
        check.opt_inst_param(current_time, "current_time", datetime)

        return schedule_partition_range(
            start=self.start,
            end=self.end,
            cron_schedule=self.get_cron_schedule(),
            fmt=self.fmt,
            timezone=self.timezone,
            execution_time_to_partition_fn=self.get_execution_time_to_partition_fn(),
            current_time=current_time,
        )

    def get_cron_schedule(self) -> str:
        return get_cron_schedule(self.schedule_type, self.execution_time, self.execution_day)

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


class DynamicPartitionsDefinition(
    PartitionsDefinition,
    NamedTuple(
        "_DynamicPartitionsDefinition",
        [("partition_fn", Callable[[Optional[datetime]], List[Partition]])],
    ),
):
    def __new__(cls, partition_fn: Callable[[Optional[datetime]], List[Partition]]):
        return super(DynamicPartitionsDefinition, cls).__new__(
            cls, check.callable_param(partition_fn, "partition_fn")
        )

    def get_partitions(self, current_time: Optional[datetime] = None) -> List[Partition]:
        return self.partition_fn(current_time)


class PartitionSetDefinition(Generic[T]):
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
        run_config_fn_for_partition (Callable[[Partition], Any]): A
            function that takes a :py:class:`~dagster.Partition` and returns the run
            configuration that parameterizes the execution for this partition.
        tags_fn_for_partition (Callable[[Partition], Optional[dict[str, str]]]): A function that
            takes a :py:class:`~dagster.Partition` and returns a list of key value pairs that will
            be added to the generated run for this partition.
        partitions_def (Optional[PartitionsDefinition]): A set of parameters used to construct the set
            of valid partition objects.
    """

    def __init__(
        self,
        name: str,
        pipeline_name: str,
        partition_fn: Optional[Callable[..., Union[List[Partition[T]], List[str]]]] = None,
        solid_selection: Optional[List[str]] = None,
        mode: Optional[str] = None,
        run_config_fn_for_partition: Callable[[Partition[T]], Any] = lambda _partition: {},
        tags_fn_for_partition: Callable[
            [Partition[T]], Optional[Dict[str, str]]
        ] = lambda _partition: {},
        partitions_def: Optional[
            PartitionsDefinition[T]  # pylint: disable=unsubscriptable-object
        ] = None,
    ):
        check.invariant(
            partition_fn is not None or partitions_def is not None,
            "One of `partition_fn` or `partitions_def` must be supplied.",
        )
        check.invariant(
            not (partition_fn and partitions_def),
            "Only one of `partition_fn` or `partitions_def` must be supplied.",
        )

        _wrap_partition_fn = None

        if partition_fn is not None:
            partition_fn_param_count = len(inspect.signature(partition_fn).parameters)

            def _wrap_partition(x: Union[str, Partition]) -> Partition:
                if isinstance(x, Partition):
                    return x
                if isinstance(x, str):
                    return Partition(x)
                raise DagsterInvalidDefinitionError(
                    "Expected <Partition> | <str>, received {type}".format(type=type(x))
                )

            def _wrap_partition_fn(current_time=None) -> List[Partition]:
                if not current_time:
                    current_time = pendulum.now("UTC")

                check.callable_param(partition_fn, "partition_fn")

                if partition_fn_param_count == 1:
                    obj_list = cast(
                        Callable[..., List[Union[Partition[T], str]]],
                        partition_fn,
                    )(current_time)
                else:
                    obj_list = partition_fn()  # type: ignore

                return [_wrap_partition(obj) for obj in obj_list]

        self._name = check_valid_name(name)
        self._pipeline_name = check.opt_str_param(pipeline_name, "pipeline_name")
        self._partition_fn = _wrap_partition_fn
        self._solid_selection = check.opt_nullable_list_param(
            solid_selection, "solid_selection", of_type=str
        )
        self._mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)
        self._user_defined_run_config_fn_for_partition = check.callable_param(
            run_config_fn_for_partition, "run_config_fn_for_partition"
        )
        self._user_defined_tags_fn_for_partition = check.callable_param(
            tags_fn_for_partition, "tags_fn_for_partition"
        )
        check.opt_inst_param(partitions_def, "partitions_def", PartitionsDefinition)
        if partitions_def is not None:
            self._partitions_def = partitions_def
        else:
            if partition_fn is None:
                check.failed("One of `partition_fn` or `partitions_def` must be supplied.")
            self._partitions_def = DynamicPartitionsDefinition(partition_fn=_wrap_partition_fn)

    @property
    def name(self):
        return self._name

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def solid_selection(self):
        return self._solid_selection

    @property
    def mode(self):
        return self._mode

    def run_config_for_partition(self, partition: Partition[T]) -> Dict[str, Any]:
        return self._user_defined_run_config_fn_for_partition(partition)

    def tags_for_partition(self, partition: Partition[T]) -> Dict[str, str]:
        user_tags = self._user_defined_tags_fn_for_partition(partition)
        check_tags(user_tags, "user_tags")

        tags = merge_dicts(user_tags, PipelineRun.tags_for_partition_set(self, partition))

        return tags

    def get_partitions(self, current_time: Optional[datetime] = None) -> List[Partition[T]]:
        """Return the set of known partitions.

        Arguments:
            current_time (Optional[datetime]): The evaluation time for the partition function, which
                is passed through to the ``partition_fn`` (if it accepts a parameter).  Defaults to
                the current time in UTC.
        """
        return self._partitions_def.get_partitions(current_time)

    def get_partition(self, name: str) -> Partition[T]:
        for partition in self.get_partitions():
            if partition.name == name:
                return partition

        check.failed("Partition name {} not found!".format(name))

    def get_partition_names(self, current_time: Optional[datetime] = None) -> List[str]:
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
        decorated_fn=None,
        job=None,
    ):
        """Create a ScheduleDefinition from a PartitionSetDefinition.

        Arguments:
            schedule_name (str): The name of the schedule.
            cron_schedule (str): A valid cron string for the schedule
            partition_selector (Callable[ScheduleEvaluationContext, PartitionSetDefinition], Union[Partition, List[Partition]]):
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
            check.inst_param(context, "context", ScheduleEvaluationContext)
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
            pipeline_name=self._pipeline_name,
            tags_fn=None,
            solid_selection=self._solid_selection,
            mode=self._mode,
            should_execute=None,
            environment_vars=environment_vars,
            partition_set=self,
            execution_timezone=execution_timezone,
            execution_fn=_execution_fn,
            description=description,
            decorated_fn=decorated_fn,
            job=job,
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
        decorated_fn=None,
        job=None,
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
            job=job,
        )
        self._partition_set = check.inst_param(
            partition_set, "partition_set", PartitionSetDefinition
        )
        self._decorated_fn = check.opt_callable_param(decorated_fn, "decorated_fn")

    def __call__(self, *args, **kwargs):
        if not self._decorated_fn:
            raise DagsterInvalidInvocationError(
                "Only partition schedules created using one of the partition schedule decorators "
                "can be directly invoked."
            )
        if len(args) == 0 and len(kwargs) == 0:
            raise DagsterInvalidInvocationError(
                "Schedule decorated function has date argument, but no date argument was "
                "provided when invoking."
            )
        if len(args) + len(kwargs) > 1:
            raise DagsterInvalidInvocationError(
                "Schedule invocation received multiple arguments. Only a first "
                "positional date parameter should be provided when invoking."
            )

        date_param_name = get_function_params(self._decorated_fn)[0].name

        if args:
            date = check.opt_inst_param(args[0], date_param_name, datetime)
        else:
            if date_param_name not in kwargs:
                raise DagsterInvalidInvocationError(
                    f"Schedule invocation expected argument '{date_param_name}'."
                )
            date = check.opt_inst_param(kwargs[date_param_name], date_param_name, datetime)

        return self._decorated_fn(date)

    def get_partition_set(self):
        return self._partition_set


class PartitionedConfig(Generic[T]):
    """Defines a way of configuring a job where the job can be run on one of a discrete set of
    partitions, and each partition corresponds to run configuration for the job."""

    def __init__(
        self,
        partitions_def: PartitionsDefinition[T],  # pylint: disable=unsubscriptable-object
        run_config_for_partition_fn: Callable[[Partition[T]], Dict[str, Any]],
    ):
        self._partitions = check.inst_param(partitions_def, "partitions_def", PartitionsDefinition)
        self._run_config_for_partition_fn = check.callable_param(
            run_config_for_partition_fn, "run_config_for_partition_fn"
        )

    @property
    def partitions_def(self) -> PartitionsDefinition[T]:  # pylint: disable=unsubscriptable-object
        return self._partitions

    @property
    def run_config_for_partition_fn(self) -> Callable[[Partition[T]], Dict[str, Any]]:
        return self._run_config_for_partition_fn


def get_cron_schedule(
    schedule_type: ScheduleType,
    time_of_day: time = time(0, 0),
    day_of_week: Optional[int] = 0,
) -> str:
    minute = time_of_day.minute
    hour = time_of_day.hour
    day = day_of_week

    if schedule_type is ScheduleType.HOURLY:
        return f"{minute} * * * *"
    elif schedule_type is ScheduleType.DAILY:
        return f"{minute} {hour} * * *"
    elif schedule_type is ScheduleType.WEEKLY:
        return f"{minute} {hour} * * {day}"
    elif schedule_type is ScheduleType.MONTHLY:
        return f"{minute} {hour} {day} * *"
    else:
        check.assert_never(schedule_type)
