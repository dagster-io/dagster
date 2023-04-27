import datetime
import functools
from typing import Iterator, Optional, Sequence, Union

import pendulum
import pytz
from croniter import croniter as _croniter

import dagster._check as check
from dagster._seven.compat.pendulum import to_timezone


class CroniterShim(_croniter):
    """Lightweight shim to enable caching certain values that may be calculated many times."""

    @classmethod
    @functools.lru_cache(maxsize=128)
    def expand(cls, *args, **kwargs):
        return super().expand(*args, **kwargs)


def _exact_match(cron_expression: str, dt: datetime.datetime) -> bool:
    """The default croniter match function only checks that the given datetime is within 60 seconds
    of a cron schedule tick. This function checks that the given datetime is exactly on a cron tick.
    """
    cron = CroniterShim(
        cron_expression, dt + datetime.timedelta(microseconds=1), ret_type=datetime.datetime
    )
    return dt == cron.get_prev()


def is_valid_cron_string(cron_string: str) -> bool:
    if not CroniterShim.is_valid(cron_string):
        return False
    expanded, _ = CroniterShim.expand(cron_string)
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

    cron_parts, nth_weekday_of_month = CroniterShim.expand(cron_string)

    is_numeric = [len(part) == 1 and part[0] != "*" for part in cron_parts]
    is_wildcard = [len(part) == 1 and part[0] == "*" for part in cron_parts]

    delta_fn = None
    should_hour_change = False
    expected_hour = None

    # Special-case common intervals (hourly/daily/weekly/monthly) since croniter iteration can be
    # much slower than adding a fixed interval
    if not nth_weekday_of_month:
        if all(is_numeric[0:3]) and all(is_wildcard[3:]):  # monthly
            delta_fn = lambda d, num: d.add(months=num)
            should_hour_change = False
        elif all(is_numeric[0:2]) and is_numeric[4] and all(is_wildcard[2:4]):  # weekly
            delta_fn = lambda d, num: d.add(weeks=num)
            should_hour_change = False
        elif all(is_numeric[0:2]) and all(is_wildcard[2:]):  # daily
            delta_fn = lambda d, num: d.add(days=num)
            should_hour_change = False
        elif is_numeric[0] and all(is_wildcard[1:]):  # hourly
            delta_fn = lambda d, num: d.add(hours=num)
            should_hour_change = True

    if is_numeric[1]:
        expected_hour = int(cron_parts[1][0])

    date_iter = CroniterShim(cron_string, start_datetime)
    if delta_fn is not None and start_offset == 0 and _exact_match(cron_string, start_datetime):
        # In simple cases, where you're already on a cron boundary, the below logic is unnecessary
        # and slow
        next_date = start_datetime
        # This is already on a cron boundary, so yield it
        yield to_timezone(pendulum.instance(next_date), timezone_str)
    else:
        # Go back one iteration so that the next iteration is the first time that is >= start_datetime
        # and matches the cron schedule
        next_date = date_iter.get_prev(datetime.datetime)

        if not CroniterShim.match(cron_string, next_date):
            # Workaround for upstream croniter bug where get_prev sometimes overshoots to a time
            # that doesn't actually match the cron string (e.g. 3AM on Spring DST day
            # goes back to 1AM on the previous day) - when this happens, advance to the correct
            # time that actually matches the cronstring
            next_date = date_iter.get_next(datetime.datetime)

        check.invariant(start_offset <= 0)
        for _ in range(-start_offset):
            next_date = date_iter.get_prev(datetime.datetime)

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
            elif expected_hour is not None and new_hour != expected_hour:
                # hour should only be different than expected if the timezone has just changed -
                # if it hasn't, it means we are moving from e.g. 3AM on spring DST day back to
                # 2AM on the next day and need to reset back to the expected hour
                if next_date_cand.utcoffset() == next_date.utcoffset():
                    next_date_cand = next_date_cand.set(hour=expected_hour)

            next_date = next_date_cand

            if start_offset == 0 and next_date.timestamp() < start_timestamp:
                # Guard against edge cases where croniter get_prev() returns unexpected
                # results that cause us to get stuck
                continue

            yield next_date
    else:
        # Otherwise fall back to croniter
        while True:
            next_date = to_timezone(
                pendulum.instance(date_iter.get_next(datetime.datetime)), timezone_str
            )

            if start_offset == 0 and next_date.timestamp() < start_timestamp:
                # Guard against edge cases where croniter get_prev() returns unexpected
                # results that cause us to get stuck
                continue

            yield next_date


def reverse_cron_string_iterator(
    end_timestamp: float, cron_string: str, execution_timezone: Optional[str]
) -> Iterator[datetime.datetime]:
    """Generator of datetimes < end_timestamp for the given cron string."""
    timezone_str = execution_timezone if execution_timezone else "UTC"

    utc_datetime = pytz.utc.localize(datetime.datetime.utcfromtimestamp(end_timestamp))
    end_datetime = utc_datetime.astimezone(pytz.timezone(timezone_str))

    date_iter = CroniterShim(cron_string, end_datetime)

    # Go forward one iteration so that the next iteration is the first time that is < end_datetime
    # and matches the cron schedule
    next_date = date_iter.get_next(datetime.datetime)

    cron_parts, _ = CroniterShim.expand(cron_string)

    is_numeric = [len(part) == 1 and part[0] != "*" for part in cron_parts]
    is_wildcard = [len(part) == 1 and part[0] == "*" for part in cron_parts]

    # Special-case common intervals (hourly/daily/weekly/monthly) since croniter iteration can be
    # much slower than adding a fixed interval
    if all(is_numeric[0:3]) and all(is_wildcard[3:]):  # monthly
        delta_fn = lambda d, num: d.subtract(months=num)
        should_hour_change = False
    elif all(is_numeric[0:2]) and is_numeric[4] and all(is_wildcard[2:4]):  # weekly
        delta_fn = lambda d, num: d.subtract(weeks=num)
        should_hour_change = False
    elif all(is_numeric[0:2]) and all(is_wildcard[2:]):  # daily
        delta_fn = lambda d, num: d.subtract(days=num)
        should_hour_change = False
    elif is_numeric[0] and all(is_wildcard[1:]):  # hourly
        delta_fn = lambda d, num: d.subtract(hours=num)
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

            if next_date.timestamp() > end_timestamp:
                # Guard against edge cases where croniter get_next() returns unexpected
                # results that cause us to get stuck
                continue

            yield next_date
    else:
        # Otherwise fall back to croniter
        while True:
            next_date = to_timezone(
                pendulum.instance(date_iter.get_prev(datetime.datetime)), timezone_str
            )

            if next_date.timestamp() > end_timestamp:
                # Guard against edge cases where croniter get_next() returns unexpected
                # results that cause us to get stuck
                continue

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
    check.invariant(
        is_valid_cron_schedule(cron_schedule), desc=f"{cron_schedule} must be a valid cron schedule"
    )

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
