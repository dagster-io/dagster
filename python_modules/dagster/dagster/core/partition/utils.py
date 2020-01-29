import datetime

from dateutil.relativedelta import relativedelta

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError


def date_partition_range(start, end=None, delta=datetime.timedelta(days=1), fmt="%Y-%m-%d"):
    from dagster.core.definitions.partition import Partition

    check.inst_param(start, 'start', datetime.datetime)
    check.opt_inst_param(end, 'end', datetime.datetime)
    check.inst_param(delta, 'timedelta', (datetime.timedelta, relativedelta))
    check.str_param(fmt, 'fmt')

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
        while current < _end:
            date_names.append(Partition(value=current, name=current.strftime(fmt)))
            current = current + delta

        # We don't include the last element here since we only want
        # fully completed intervals, and the _end time is in the middle of the interval
        # represented by the last element of date_names
        return date_names[:-1]

    return get_date_range_partitions
