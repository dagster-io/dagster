import datetime

from dateutil.relativedelta import relativedelta

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


def date_partition_range(
    start, end=None, delta=datetime.timedelta(days=1), fmt=None, inclusive=False
):
    """ Utility function that returns a partition generating function to be used in creating a
    `PartitionSet` definition.

    Args:
        start (datetime): Datetime capturing the start of the time range.
        end  (Optional(datetime)): Datetime capturing the end of the partition.  By default, the
                                   current time is used.  The range is not inclusive of the end
                                   value.
        delta (Optional(timedelta)): Timedelta representing the time duration of each partition.
        fmt (Optional(str)): Format string to represent each partition by its start time
        inclusive (Optional(bool)): By default, the partition set only contains date interval
            partitions for which the end time of the interval is less than current time. In other
            words, the partition set contains date interval partitions that are completely in the
            past. If inclusive is set to True, then the partition set will include all date
            interval partitions for which the start time of the interval is less than the
            current time.

    Returns:
        Callable[[], List[Partition]]
    """
    from dagster.core.definitions.partition import Partition

    check.inst_param(start, "start", datetime.datetime)
    check.opt_inst_param(end, "end", datetime.datetime)
    check.inst_param(delta, "timedelta", (datetime.timedelta, relativedelta))
    fmt = check.opt_str_param(fmt, "fmt", default=DEFAULT_DATE_FORMAT)

    if end and start > end:
        raise DagsterInvariantViolationError(
            'Selected date range start "{start}" is after date range end "{end}'.format(
                start=start.strftime(fmt), end=end.strftime(fmt)
            )
        )

    def get_date_range_partitions():
        current = start

        _end = end or datetime.datetime.now()

        date_names = []
        while current <= _end:
            date_names.append(Partition(value=current, name=current.strftime(fmt)))
            current = current + delta

        # We don't include the last element here by default since we only want
        # fully completed intervals, and the _end time is in the middle of the interval
        # represented by the last element of date_names
        if inclusive:
            return date_names

        return date_names[:-1]

    return get_date_range_partitions
