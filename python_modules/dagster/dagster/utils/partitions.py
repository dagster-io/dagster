import datetime

import pendulum
from dagster import check
from dagster.core.definitions.partition import Partition, PartitionSetDefinition
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.errors import DagsterInvariantViolationError
from dagster.seven import PendulumDateTime, to_timezone
from dagster.utils.schedules import schedule_execution_time_iterator

DEFAULT_MONTHLY_FORMAT = "%Y-%m"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE = "%Y-%m-%d-%H:%M"
DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE = DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE + "%z"


def schedule_partition_range(
    start,
    end,
    cron_schedule,
    fmt,
    timezone,
    execution_time_to_partition_fn,
    inclusive=False,
):
    check.inst_param(start, "start", datetime.datetime)
    check.opt_inst_param(end, "end", datetime.datetime)
    check.str_param(cron_schedule, "cron_schedule")
    check.str_param(fmt, "fmt")
    check.opt_str_param(timezone, "timezone")
    check.callable_param(execution_time_to_partition_fn, "execution_time_to_partition_fn")
    check.opt_bool_param(inclusive, "inclusive")

    if end and start > end:
        raise DagsterInvariantViolationError(
            'Selected date range start "{start}" is after date range end "{end}'.format(
                start=start.strftime(fmt),
                end=end.strftime(fmt),
            )
        )

    def get_schedule_range_partitions(current_time=None):
        check.opt_inst_param(current_time, "current_time", datetime.datetime)
        tz = timezone if timezone else pendulum.now().timezone.name
        _start = (
            to_timezone(start, tz)
            if isinstance(start, PendulumDateTime)
            else pendulum.instance(start, tz=tz)
        )

        if end:
            _end = end
        elif current_time:
            _end = current_time
        else:
            _end = pendulum.now(tz)

        # coerce to the definition timezone
        if isinstance(_end, PendulumDateTime):
            _end = to_timezone(_end, tz)
        else:
            _end = pendulum.instance(_end, tz=tz)

        end_timestamp = _end.timestamp()

        partitions = []
        for next_time in schedule_execution_time_iterator(_start.timestamp(), cron_schedule, tz):

            partition_time = execution_time_to_partition_fn(next_time)

            if partition_time.timestamp() > end_timestamp:
                break

            if partition_time.timestamp() < _start.timestamp():
                continue

            partitions.append(Partition(value=partition_time, name=partition_time.strftime(fmt)))

        return partitions if inclusive else partitions[:-1]

    return get_schedule_range_partitions


def date_partition_range(
    start,
    end=None,
    delta_range="days",
    fmt=None,
    inclusive=False,
    timezone=None,
):
    """Utility function that returns a partition generating function to be used in creating a
    `PartitionSet` definition.

    Args:
        start (datetime): Datetime capturing the start of the time range.
        end  (Optional(datetime)): Datetime capturing the end of the partition.  By default, the
                                   current time is used.  The range is not inclusive of the end
                                   value.
        delta_range (Optional(str)): string representing the time duration of each partition.
            Must be a valid argument to pendulum.period.range ("days", "hours", "months", etc.).
        fmt (Optional(str)): Format string to represent each partition by its start time
        inclusive (Optional(bool)): By default, the partition set only contains date interval
            partitions for which the end time of the interval is less than current time. In other
            words, the partition set contains date interval partitions that are completely in the
            past. If inclusive is set to True, then the partition set will include all date
            interval partitions for which the start time of the interval is less than the
            current time.
        timezone (Optional(str)): Timezone in which the partition values should be expressed.
    Returns:
        Callable[[], List[Partition]]
    """

    check.inst_param(start, "start", datetime.datetime)
    check.opt_inst_param(end, "end", datetime.datetime)
    check.str_param(delta_range, "delta_range")
    fmt = check.opt_str_param(fmt, "fmt", default=DEFAULT_DATE_FORMAT)
    check.opt_str_param(timezone, "timezone")

    delta_amount = 1

    if end and start > end:
        raise DagsterInvariantViolationError(
            'Selected date range start "{start}" is after date range end "{end}'.format(
                start=start.strftime(fmt),
                end=end.strftime(fmt),
            )
        )

    def get_date_range_partitions(current_time=None):
        check.opt_inst_param(current_time, "current_time", datetime.datetime)
        tz = timezone if timezone else pendulum.now().timezone.name
        _start = (
            to_timezone(start, tz)
            if isinstance(start, PendulumDateTime)
            else pendulum.instance(start, tz=tz)
        )

        if end:
            _end = end
        elif current_time:
            _end = current_time
        else:
            _end = pendulum.now(tz)

        # coerce to the definition timezone
        if isinstance(_end, PendulumDateTime):
            _end = to_timezone(_end, tz)
        else:
            _end = pendulum.instance(_end, tz=tz)

        period = pendulum.period(_start, _end)
        date_names = [
            Partition(value=current, name=current.strftime(fmt))
            for current in period.range(delta_range, delta_amount)
        ]

        # We don't include the last element here by default since we only want
        # fully completed intervals, and the _end time is in the middle of the interval
        # represented by the last element of date_names
        if inclusive:
            return date_names

        return date_names[:-1]

    return get_date_range_partitions


def identity_partition_selector(context, partition_set_def):
    """Utility function for supplying a partition selector when creating a schedule from a
    partition set made of `datetime`s that assumes the schedule always executes at the
    partition time.

    It's important that the cron string passed into `create_schedule_definition` match
    the partition set times. For example, a schedule created from a partition set with partitions for each day at
    midnight would create its partition selector as follows:

    .. code-block:: python

        partition_set = PartitionSetDefinition(
            name='hello_world_partition_set',
            pipeline_name='hello_world_pipeline',
            partition_fn= date_partition_range(
                start=datetime.datetime(2021, 1, 1),
                delta_range="days",
                timezone="US/Central",
            )
            run_config_fn_for_partition=my_run_config_fn,
        )

        schedule_definition = partition_set.create_schedule_definition(
            "hello_world_daily_schedule",
            "0 0 * * *",
            partition_selector=identity_partition_selector,
            execution_timezone="US/Central",
        )
    """

    return create_offset_partition_selector(lambda d: d)(context, partition_set_def)


def create_offset_partition_selector(execution_time_to_partition_fn):
    """Utility function for supplying a partition selector when creating a schedule from a
    partition set made of `datetime`s that assumes a fixed time offset between the partition
    time and the time at which the schedule executes.

    It's important to keep the cron string that's supplied to
    `PartitionSetDefinition.create_schedule_definition` in sync with the offset that's
    supplied to this function. For example, a schedule created from a partition set with
    partitions for each day at midnight that fills in the partition for day N at day N+1 at
    10:00AM would create the partition selector as follows:

    .. code-block:: python

        partition_set = PartitionSetDefinition(
            name='hello_world_partition_set',
            pipeline_name='hello_world_pipeline',
            partition_fn= date_partition_range(
                start=datetime.datetime(2021, 1, 1),
                delta_range="days",
                timezone="US/Central",
            )
            run_config_fn_for_partition=my_run_config_fn,
        )

        schedule_definition = partition_set.create_schedule_definition(
            "daily_10am_schedule",
            "0 10 * * *",
            partition_selector=create_offset_partition_selector(lambda d: d.subtract(hours=10, days=1))
            execution_timezone="US/Central",
        )

    Args:
        execution_time_to_partition_fn (Callable[[datetime.datetime], datetime.datetime]): A
        function that maps the execution time of the schedule to the partition time.
    """

    check.callable_param(execution_time_to_partition_fn, "execution_time_to_partition_fn")

    def offset_partition_selector(context, partition_set_def):
        check.inst_param(context, "context", ScheduleExecutionContext)
        check.inst_param(partition_set_def, "partition_set_def", PartitionSetDefinition)

        if not context.scheduled_execution_time:
            partitions = partition_set_def.get_partitions()
            if not partitions:
                return None
            return partitions[-1]

        partition_time = execution_time_to_partition_fn(context.scheduled_execution_time)

        for partition in reversed(
            partition_set_def.get_partitions(context.scheduled_execution_time)
        ):
            if partition.value.isoformat() == partition_time.isoformat():
                return partition

            if partition.value < partition_time:
                break

        return None

    return offset_partition_selector
