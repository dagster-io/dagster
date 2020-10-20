import datetime
import warnings

import pendulum
from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dateutil.relativedelta import relativedelta

DEFAULT_MONTHLY_FORMAT = "%Y-%m"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE = "%Y-%m-%d-%H:%M"
DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE = DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE + "%z"


# Remove this when the 'delta' param to date_partition_range is removed
def _delta_to_delta_range(delta):
    check.opt_inst_param(delta, "delta", (datetime.timedelta, relativedelta))
    if isinstance(delta, relativedelta) and delta.months > 0:
        # Ensure that only months was set
        check.invariant(relativedelta(months=delta.months) == delta)
        return ("months", delta.months)
    elif isinstance(delta, relativedelta) and delta.weeks > 0:
        # Ensure that only weeks was set
        check.invariant(relativedelta(weeks=delta.weeks) == delta)
        return ("weeks", delta.weeks)
    elif delta.days > 0:
        # Ensure that only days was set
        check.invariant(type(delta)(days=delta.days) == delta)
        return ("days", delta.days)
    elif isinstance(delta, relativedelta) and delta.hours > 0:
        # Ensure that only hours was set
        check.invariant(relativedelta(hours=delta.hours) == delta)
        return ("hours", delta.hours)
    elif isinstance(delta, relativedelta) and delta.minutes > 0:
        # Ensure that only minutes was set
        check.invariant(relativedelta(minutes=delta.minutes) == delta)
        return ("minutes", delta.minutes)
    elif delta.seconds > 0:
        check.invariant(type(delta)(seconds=delta.seconds) == delta)
        return ("seconds", delta.seconds)
    else:
        check.failed(
            "Unable to create a partition range with delta {delta}".format(delta=repr(delta))
        )


def date_partition_range(
    start, end=None, delta=None, delta_range="days", fmt=None, inclusive=False, timezone=None,
):
    """ Utility function that returns a partition generating function to be used in creating a
    `PartitionSet` definition.

    Args:
        start (datetime): Datetime capturing the start of the time range.
        end  (Optional(datetime)): Datetime capturing the end of the partition.  By default, the
                                   current time is used.  The range is not inclusive of the end
                                   value.
        delta (Optional(timedelta)): Timedelta representing the time duration of each partition.
            DEPRECATED: use 'delta_range' instead, which handles timezone transitions correctly.
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
    from dagster.core.definitions.partition import Partition

    check.inst_param(start, "start", datetime.datetime)
    check.opt_inst_param(end, "end", datetime.datetime)
    check.opt_str_param(delta_range, "delta_range")
    fmt = check.opt_str_param(fmt, "fmt", default=DEFAULT_DATE_FORMAT)
    check.opt_str_param(timezone, "timezone")

    check.opt_inst_param(delta, "delta", (datetime.timedelta, relativedelta))

    if delta:
        check.invariant(not delta_range, "cannot supply both 'delta' and 'delta_range' parameters")
        warnings.warn(
            "The 'delta' argument to date_partition_range has been deprecated - use 'delta_range' "
            "instead, which has better support for timezones. For example, if you previously "
            "passed in delta=timedelta(days=1), pass in delta_range='days' instead. The 'delta' "
            "argument will be removed in the dagster 0.10.0 release."
        )
        delta_range, delta_amount = _delta_to_delta_range(delta)
    else:
        check.invariant(delta_range, "Must include either a 'delta' or 'delta_range' parameter")
        delta_amount = 1

    if end and start > end:
        raise DagsterInvariantViolationError(
            'Selected date range start "{start}" is after date range end "{end}'.format(
                start=start.strftime(fmt), end=end.strftime(fmt),
            )
        )

    def get_date_range_partitions():
        tz = timezone if timezone else pendulum.now().timezone.name
        _start = (
            start.in_tz(tz)
            if isinstance(start, pendulum.Pendulum)
            else pendulum.instance(start, tz=tz)
        )

        if not end:
            _end = pendulum.now(tz)
        elif isinstance(end, pendulum.Pendulum):
            _end = end.in_tz(tz)
        else:
            _end = pendulum.instance(end, tz=tz)

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
