import datetime
from typing import Callable, Iterator, Optional, Sequence, Union

import pytz
from croniter import croniter
from typing_extensions import Literal

import dagster._check as check
import dagster._seven.compat.pendulum as pendulum
from dagster._seven.compat.pendulum import PendulumDateTime, to_timezone


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

    # Go back one iteration so that the next iteration is the first time that is >= start_datetime
    # and matches the cron schedule
    next_date = date_iter.get_prev(datetime.datetime)

    check.invariant(start_offset <= 0)
    for _ in range(-start_offset):
        next_date = date_iter.get_prev(datetime.datetime)

    cron_parts, _ = croniter.expand(cron_string)

    is_numeric = [len(part) == 1 and part[0] != "*" for part in cron_parts]
    is_wildcard = [len(part) == 1 and part[0] == "*" for part in cron_parts]

    # Special-case common intervals (hourly/daily/weekly/monthly) since croniter iteration can be
    # much slower than adding a fixed interval
    delta_fn: Optional[Callable[[PendulumDateTime, int], PendulumDateTime]] = None
    if all(is_numeric[0:3]) and all(is_wildcard[3:]):  # monthly
        delta_fn = _make_delta_fn("add", "months")
        should_hour_change = False
    elif all(is_numeric[0:2]) and is_numeric[4] and all(is_wildcard[2:4]):  # weekly
        delta_fn = _make_delta_fn("add", "weeks")
        should_hour_change = False
    elif all(is_numeric[0:2]) and all(is_wildcard[2:]):  # daily
        delta_fn = _make_delta_fn("add", "days")
        should_hour_change = False
    elif is_numeric[0] and all(is_wildcard[1:]):  # hourly
        delta_fn = _make_delta_fn("add", "hours")
        should_hour_change = True
    else:
        delta_fn = None
        should_hour_change = False

    if delta_fn is not None:
        # Use pendulums for intervals when possible
        next_date = to_timezone(pendulum.instance(next_date), timezone_str)
        while True:
            curr_hour = next_date.hour

            next_date_cand = delta_fn(next_date, 1)
            new_hour = next_date_cand.hour

            if not should_hour_change and new_hour != curr_hour:
                # If the hour changes during a daily/weekly/monthly schedule, it
                # indicates that the time shifted due to falling in a time that doesn't
                # exist due to a DST transition (for example, 2:30AM CST on 3/10/2019).
                # Instead, execute at the first time that does exist (the start of the hour),
                # but return to the original hour for all subsequent executions so that the
                # hour doesn't stay different permanently.

                check.invariant(new_hour == curr_hour + 1)
                yield next_date_cand.replace(minute=0)

                next_date_cand = delta_fn(next_date, 2)
                check.invariant(next_date_cand.hour == curr_hour)

            next_date = next_date_cand
            yield next_date
    else:
        # Otherwise fall back to croniter
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

    # Go forward one iteration so that the next iteration is the first time that is < end_datetime
    # and matches the cron schedule
    next_date = pendulum.instance(date_iter.get_next(datetime.datetime))

    cron_parts, _ = croniter.expand(cron_string)

    is_numeric = [len(part) == 1 and part[0] != "*" for part in cron_parts]
    is_wildcard = [len(part) == 1 and part[0] == "*" for part in cron_parts]

    # Special-case common intervals (hourly/daily/weekly/monthly) since croniter iteration can be
    # much slower than adding a fixed interval
    if all(is_numeric[0:3]) and all(is_wildcard[3:]):  # monthly
        delta_fn = _make_delta_fn("subtract", "months")
        should_hour_change = False
    elif all(is_numeric[0:2]) and is_numeric[4] and all(is_wildcard[2:4]):  # weekly
        delta_fn = _make_delta_fn("subtract", "weeks")
        should_hour_change = False
    elif all(is_numeric[0:2]) and all(is_wildcard[2:]):  # daily
        delta_fn = _make_delta_fn("subtract", "days")
        should_hour_change = False
    elif is_numeric[0] and all(is_wildcard[1:]):  # hourly
        delta_fn = _make_delta_fn("subtract", "hours")
        should_hour_change = True
    else:
        delta_fn = None
        should_hour_change = False

    if delta_fn is not None:
        # Use pendulums for intervals when possible
        next_date = to_timezone(pendulum.instance(next_date), timezone_str)  # type: ignore  # fmt: skip
        while True:
            curr_hour = next_date.hour

            next_date_cand = delta_fn(next_date, 1)  # type: ignore  # fmt: skip
            new_hour = next_date_cand.hour

            if not should_hour_change and new_hour != curr_hour:
                # If the hour changes during a daily/weekly/monthly schedule, it
                # indicates that the time shifted due to falling in a time that doesn't
                # exist due to a DST transition (for example, 2:30AM CST on 3/10/2019).
                # Instead, execute at the first time that does exist (the start of the hour),
                # but return to the original hour for all subsequent executions so that the
                # hour doesn't stay different permanently.

                check.invariant(new_hour == curr_hour + 1)
                yield next_date_cand.replace(minute=0)

                next_date_cand = delta_fn(next_date, 2)  # type: ignore  # fmt: skip
                check.invariant(next_date_cand.hour == curr_hour)

            next_date = next_date_cand  # type: ignore  # fmt: skip
            yield next_date
    else:
        # Otherwise fall back to croniter
        while True:
            next_date = to_timezone(  # type: ignore  # fmt: skip
                pendulum.instance(date_iter.get_prev(datetime.datetime)), timezone_str
            )

            yield next_date


def _make_delta_fn(
    direction: Literal["add", "subtract"], period: str
) -> Callable[[PendulumDateTime, int], PendulumDateTime]:
    if direction == "add":

        def delta_fn(d: PendulumDateTime, num: int) -> PendulumDateTime:
            return d.add(**{period: num})

    elif direction == "subtract":

        def delta_fn(d: PendulumDateTime, num: int) -> PendulumDateTime:
            return d.subtract(**{period: num})

    return delta_fn


def schedule_execution_time_iterator(
    start_timestamp: float,
    cron_schedule: Union[str, Sequence[str]],
    execution_timezone: Optional[str],
) -> Iterator[datetime.datetime]:
    """Generator of execution datetimes >= start_timestamp for the given schedule.

    Here cron_schedule is either a cron string or a sequence of cron strings. In the latter case,
    the next execution datetime is obtained by computing the next cron datetime
    after the current execution datetime for each cron string in the sequence, and then choosing
    the earliest among them.
    """
    check.invariant(is_valid_cron_schedule(cron_schedule))

    if isinstance(cron_schedule, str):
        yield from cron_string_iterator(start_timestamp, cron_schedule, execution_timezone)
    else:
        iterators = [
            cron_string_iterator(start_timestamp, cron_string, execution_timezone)
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
