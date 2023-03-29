import datetime
from typing import Iterator, Optional, Sequence, Union

import pendulum
import pytz
from croniter import croniter

import dagster._check as check
from dagster._seven.compat.pendulum import to_timezone


def is_valid_cron_string(cron_string: str) -> bool:
    if not croniter.is_valid(cron_string):
        return False
    expanded, _ = croniter.expand(cron_string)
    # dagster only recognizes cron strings that resolve to 5 parts (e.g. not seconds resolution)
    return len(expanded) == 5


def is_valid_cron_schedule(cron_schedule: Union[str, Sequence[str]]) -> bool:
    return (
        is_valid_cron_string(cron_schedule)
        if isinstance(cron_schedule, str)
        else len(cron_schedule) > 0
        and all(is_valid_cron_string(cron_string) for cron_string in cron_schedule)
    )


def cron_string_iterator(
    start_timestamp: float,
    cron_string: str,
    execution_timezone: Optional[str],
    start_offset: int = 0,
) -> Iterator[datetime.datetime]:
    """Generator of datetimes >= start_timestamp for the given cron string."""
    timezone_str = execution_timezone if execution_timezone else "UTC"

    utc_datetime = pytz.utc.localize(datetime.datetime.utcfromtimestamp(start_timestamp))
    start_datetime = utc_datetime.astimezone(pytz.timezone(timezone_str))

    date_iter = croniter(cron_string, start_datetime)

    next_date = start_datetime

    for _ in range(-start_offset):
        next_date = date_iter.get_prev(datetime.datetime)

    # Special-case hourly intervals where croniter struggles, particularly over DST
    cron_parts, nth_weekday_of_month = croniter.expand(cron_string)
    is_numeric = [len(part) == 1 and part[0] != "*" for part in cron_parts]
    is_wildcard = [len(part) == 1 and part[0] == "*" for part in cron_parts]

    if not nth_weekday_of_month and is_numeric[0] and all(is_wildcard[1:]):
        next_date = date_iter.get_prev(datetime.datetime)

        next_date = to_timezone(pendulum.instance(next_date), timezone_str)
        while True:
            next_date = next_date.add(hours=1)
            yield next_date
    else:
        if next_date.second == 0 and croniter.match(cron_string, next_date):
            yield to_timezone(pendulum.instance(next_date), timezone_str)
        while True:
            next_date = to_timezone(
                pendulum.instance(date_iter.get_next(datetime.datetime)), timezone_str
            )

            yield next_date


def reverse_cron_string_iterator(
    end_timestamp: float, cron_string: str, execution_timezone: Optional[str]
) -> Iterator[datetime.datetime]:
    """Generator of datetimes < end_timestamp for the given cron string."""
    timezone_str = execution_timezone if execution_timezone else "UTC"

    utc_datetime = pytz.utc.localize(datetime.datetime.utcfromtimestamp(end_timestamp))
    end_datetime = utc_datetime.astimezone(pytz.timezone(timezone_str))

    date_iter = croniter(cron_string, end_datetime)

    cron_parts, nth_weekday_of_month = croniter.expand(cron_string)
    is_numeric = [len(part) == 1 and part[0] != "*" for part in cron_parts]
    is_wildcard = [len(part) == 1 and part[0] == "*" for part in cron_parts]
    if not nth_weekday_of_month and is_numeric[0] and all(is_wildcard[1:]):
        next_date = date_iter.get_next(datetime.datetime)
        next_date = to_timezone(pendulum.instance(next_date), timezone_str)
        while True:
            next_date = next_date.subtract(hours=1)
            yield next_date
    else:
        if end_datetime.second == 0 and croniter.match(cron_string, end_datetime):
            yield to_timezone(pendulum.instance(end_datetime), timezone_str)

        while True:
            next_date = to_timezone(
                pendulum.instance(date_iter.get_prev(datetime.datetime)), timezone_str
            )

            yield next_date


def schedule_execution_time_iterator(
    start_timestamp: float,
    cron_schedule: Union[str, Sequence[str]],
    execution_timezone: Optional[str],
    ascending: bool = True,
) -> Iterator[datetime.datetime]:
    """Generator of execution datetimes >= start_timestamp for the given schedule.

    Here cron_schedule is either a cron string or a sequence of cron strings. In the latter case,
    the next execution datetime is obtained by computing the next cron datetime
    after the current execution datetime for each cron string in the sequence, and then choosing
    the earliest among them.
    """
    check.invariant(is_valid_cron_schedule(cron_schedule))

    if isinstance(cron_schedule, str):
        yield from cron_string_iterator(
            start_timestamp, cron_schedule, execution_timezone
        ) if ascending else reverse_cron_string_iterator(
            start_timestamp, cron_schedule, execution_timezone
        )
    else:
        iterators = [
            cron_string_iterator(start_timestamp, cron_string, execution_timezone)
            if ascending
            else reverse_cron_string_iterator(start_timestamp, cron_string, execution_timezone)
            for cron_string in cron_schedule
        ]
        next_dates = [next(it) for it in iterators]
        while True:
            # Choose earliest out of all subsequent datetimes.
            earliest_next_date = min(next_dates)
            yield earliest_next_date
            # Increment all iterators that generated the earliest subsequent datetime.
            for i, next_date in enumerate(next_dates):
                if next_date == earliest_next_date:
                    next_dates[i] = next(iterators[i])
