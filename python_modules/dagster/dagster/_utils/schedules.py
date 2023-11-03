import calendar
import datetime
import functools
import math
from typing import Iterator, Optional, Sequence, Union

import pendulum
import pytz
from croniter import croniter as _croniter

import dagster._check as check
from dagster._core.definitions.partition import ScheduleType
from dagster._seven.compat.pendulum import PendulumDateTime, create_pendulum_time, to_timezone

# Monthly schedules with 29-31 won't reliably run every month
MAX_DAY_OF_MONTH_WITH_GUARANTEED_MONTHLY_INTERVAL = 28


class CroniterShim(_croniter):
    """Lightweight shim to enable caching certain values that may be calculated many times."""

    @classmethod
    @functools.lru_cache(maxsize=128)
    def expand(cls, *args, **kwargs):
        return super().expand(*args, **kwargs)


def _exact_match(
    cron_expression: str,
    schedule_type: ScheduleType,
    minute: Optional[int],
    hour: Optional[int],
    day: Optional[int],
    day_of_week: Optional[int],
    dt: PendulumDateTime,
) -> bool:
    """The default croniter match function only checks that the given datetime is within 60 seconds
    of a cron schedule tick. This function checks that the given datetime is exactly on a cron tick.
    """
    if cron_expression == "0 0 * * *":
        return dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.microsecond == 0

    if cron_expression == "0 * * * *":
        return dt.minute == 0 and dt.second == 0 and dt.microsecond == 0

    return (
        dt.timestamp()
        == _find_schedule_time(
            minute,
            hour,
            day,
            day_of_week,
            schedule_type,
            dt.add(seconds=1),
            ascending=False,
            already_on_boundary=False,
        ).timestamp()
    )


def is_valid_cron_string(cron_string: str) -> bool:
    if not CroniterShim.is_valid(cron_string):
        return False
    # Croniter < 1.4 returns 2 items
    # Croniter >= 1.4 returns 3 items
    expanded, *_ = CroniterShim.expand(cron_string)
    # dagster only recognizes cron strings that resolve to 5 parts (e.g. not seconds resolution)
    return len(expanded) == 5


def is_valid_cron_schedule(cron_schedule: Union[str, Sequence[str]]) -> bool:
    return (
        is_valid_cron_string(cron_schedule)
        if isinstance(cron_schedule, str)
        else len(cron_schedule) > 0
        and all(is_valid_cron_string(cron_string) for cron_string in cron_schedule)
    )


def _replace_date_fields(
    pendulum_date: PendulumDateTime,
    hour: int,
    minute: int,
    day: int,
):
    try:
        new_time = create_pendulum_time(
            pendulum_date.year,
            pendulum_date.month,
            day,
            hour,
            minute,
            0,
            0,
            tz=pendulum_date.timezone_name,
            dst_rule=pendulum.TRANSITION_ERROR,
        )
    except pendulum.tz.exceptions.NonExistingTime:  # type: ignore
        # If we fall on a non-existant time (e.g. between 2 and 3AM during a DST transition)
        # advance to the end of the window, which does exist - match behavior described in the docs:
        # https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules#execution-time-and-daylight-savings-time)
        new_time = create_pendulum_time(
            pendulum_date.year,
            pendulum_date.month,
            day,
            hour + 1,
            0,
            0,
            0,
            tz=pendulum_date.timezone_name,
            dst_rule=pendulum.TRANSITION_ERROR,
        )
    except pendulum.tz.exceptions.AmbiguousTime:  # type: ignore
        # For consistency, always choose the latter of the two possible times during a fall DST
        # transition when there are two possibilities - match behavior described in the docs:
        # https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules#execution-time-and-daylight-savings-time)
        new_time = create_pendulum_time(
            pendulum_date.year,
            pendulum_date.month,
            day,
            hour,
            minute,
            0,
            0,
            tz=pendulum_date.timezone_name,
            dst_rule=pendulum.POST_TRANSITION,
        )

    return new_time


SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60


def _find_hourly_schedule_time(
    minute: int,
    pendulum_date: PendulumDateTime,
    ascending: bool,
    already_on_boundary: bool,
) -> PendulumDateTime:
    if ascending:
        # short-circuit if minutes and seconds are already correct
        if already_on_boundary or (
            pendulum_date.minute == minute
            and pendulum_date.second == 0
            and pendulum_date.microsecond == 0
        ):
            return pendulum_date.add(hours=1)

        # clear microseconds
        new_timestamp = math.ceil(pendulum_date.timestamp())
        # clear seconds
        new_timestamp = (
            new_timestamp
            + (SECONDS_PER_MINUTE - new_timestamp % SECONDS_PER_MINUTE) % SECONDS_PER_MINUTE
        )

        # advance minutes to correct place
        current_minute = (new_timestamp // SECONDS_PER_MINUTE) % SECONDS_PER_MINUTE

        new_timestamp = new_timestamp + SECONDS_PER_MINUTE * (
            (minute - current_minute) % MINUTES_PER_HOUR
        )

        # move forward an hour if we haven't moved forwards yet
        if new_timestamp <= pendulum_date.timestamp():
            new_timestamp = new_timestamp + SECONDS_PER_MINUTE * MINUTES_PER_HOUR
    else:
        if already_on_boundary or (
            pendulum_date.minute == minute
            and pendulum_date.second == 0
            and pendulum_date.microsecond == 0
        ):
            return pendulum_date.subtract(hours=1)

        # clear microseconds
        new_timestamp = math.floor(pendulum_date.timestamp())
        # clear seconds
        new_timestamp = new_timestamp - new_timestamp % SECONDS_PER_MINUTE

        # move minutes back to correct place
        current_minute = (new_timestamp // SECONDS_PER_MINUTE) % SECONDS_PER_MINUTE

        new_timestamp = new_timestamp - SECONDS_PER_MINUTE * (
            (current_minute - minute) % MINUTES_PER_HOUR
        )

        # move back an hour if we haven't moved backwards yet
        if new_timestamp >= pendulum_date.timestamp():
            new_timestamp = new_timestamp - SECONDS_PER_MINUTE * MINUTES_PER_HOUR

    return pendulum.from_timestamp(new_timestamp, tz=pendulum_date.timezone_name)


def _find_daily_schedule_time(
    minute: int,
    hour: int,
    pendulum_date: PendulumDateTime,
    ascending: bool,
    already_on_boundary: bool,
) -> PendulumDateTime:
    # First move to the correct time of day today (ignoring whether it is the correct day)

    if not already_on_boundary and (
        pendulum_date.hour != hour
        or pendulum_date.minute != minute
        or pendulum_date.second != 0
        or pendulum_date.microsecond != 0
    ):
        new_time = _replace_date_fields(
            pendulum_date,
            hour,
            minute,
            pendulum_date.day,
        )
    else:
        new_time = pendulum_date

    new_hour = new_time.hour

    if ascending:
        if already_on_boundary or new_time.timestamp() <= pendulum_date.timestamp():
            new_time = new_time.add(days=1)
    else:
        if already_on_boundary or new_time.timestamp() >= pendulum_date.timestamp():
            # Move back a day if needed
            new_time = new_time.subtract(days=1)

    # If the hour has changed from either what it was before or the hour on the cronstring,
    # double-check that it's still correct in case we crossed a DST boundary
    if new_time.hour != new_hour or new_time.hour != hour:
        new_time = _replace_date_fields(
            new_time,
            hour,
            minute,
            new_time.day,
        )

    return new_time


def _find_weekly_schedule_time(
    minute: int,
    hour: int,
    day_of_week: int,
    pendulum_date: PendulumDateTime,
    ascending: bool,
    already_on_boundary: bool,
) -> PendulumDateTime:
    # first move to the correct time of day
    if not already_on_boundary:
        new_time = _replace_date_fields(
            pendulum_date,
            hour,
            minute,
            pendulum_date.day,
        )

        # Move to the correct day of the week
        current_day_of_week = new_time.day_of_week
        if day_of_week != current_day_of_week:
            if ascending:
                new_time = new_time.add(days=(day_of_week - current_day_of_week) % 7)
            else:
                new_time = new_time.subtract(days=(current_day_of_week - day_of_week) % 7)

    else:
        new_time = pendulum_date

    new_hour = new_time.hour

    # Make sure that we've actually moved in the correct direction, advance if we haven't
    if ascending:
        if already_on_boundary or new_time.timestamp() <= pendulum_date.timestamp():
            new_time = new_time.add(weeks=1)
    else:
        if already_on_boundary or new_time.timestamp() >= pendulum_date.timestamp():
            new_time = new_time.subtract(weeks=1)

    # If the hour has changed from either what it was before or the hour on the cronstring,
    # double-check that it's still correct in case we crossed a DST boundary
    if new_time.hour != new_hour or new_time.hour != hour:
        new_time = _replace_date_fields(
            new_time,
            hour,
            minute,
            new_time.day,
        )

    return new_time


def _find_monthly_schedule_time(
    minute: int,
    hour: int,
    day: int,
    pendulum_date: PendulumDateTime,
    ascending: bool,
    already_on_boundary: bool,
) -> PendulumDateTime:
    # First move to the correct day and time of day
    if not already_on_boundary:
        new_time = _replace_date_fields(
            pendulum_date,
            check.not_none(hour),
            check.not_none(minute),
            check.not_none(day),
        )
    else:
        new_time = pendulum_date

    new_hour = new_time.hour

    if ascending:
        if already_on_boundary or new_time.timestamp() <= pendulum_date.timestamp():
            new_time = new_time.add(months=1)
    else:
        if already_on_boundary or new_time.timestamp() >= pendulum_date.timestamp():
            # Move back a month if needed
            new_time = new_time.subtract(months=1)

    if new_time.hour != new_hour or new_time.hour != hour:
        # Doing so may have adjusted the hour again if we crossed a DST boundary,
        # so make sure it's still correct
        new_time = _replace_date_fields(
            new_time,
            check.not_none(hour),
            check.not_none(minute),
            check.not_none(day),
        )

    return new_time


def _find_schedule_time(
    minute: Optional[int],
    hour: Optional[int],
    day_of_month: Optional[int],
    day_of_week: Optional[int],
    schedule_type: ScheduleType,
    pendulum_date: PendulumDateTime,
    ascending: bool,
    # lets us skip slow work to find the starting point if we know that
    # we are already on the boundary of the cron interval
    already_on_boundary: bool,
) -> PendulumDateTime:
    if schedule_type == ScheduleType.HOURLY:
        return _find_hourly_schedule_time(
            check.not_none(minute), pendulum_date, ascending, already_on_boundary
        )
    elif schedule_type == ScheduleType.DAILY:
        return _find_daily_schedule_time(
            check.not_none(minute),
            check.not_none(hour),
            pendulum_date,
            ascending,
            already_on_boundary,
        )
    elif schedule_type == ScheduleType.WEEKLY:
        return _find_weekly_schedule_time(
            check.not_none(minute),
            check.not_none(hour),
            check.not_none(day_of_week),
            pendulum_date,
            ascending,
            already_on_boundary,
        )
    elif schedule_type == ScheduleType.MONTHLY:
        return _find_monthly_schedule_time(
            check.not_none(minute),
            check.not_none(hour),
            check.not_none(day_of_month),
            pendulum_date,
            ascending,
            already_on_boundary,
        )
    else:
        raise Exception(f"Unexpected schedule type {schedule_type}")


def cron_string_iterator(
    start_timestamp: float,
    cron_string: str,
    execution_timezone: Optional[str],
    ascending: bool = True,
    start_offset: int = 0,
) -> Iterator[datetime.datetime]:
    """Generator of datetimes >= start_timestamp for the given cron string."""
    # leap day special casing
    if cron_string.endswith(" 29 2 *"):
        min_hour, _ = cron_string.split(" 29 2 *")
        day_before = f"{min_hour} 28 2 *"
        # run the iterator for Feb 28th
        for dt in cron_string_iterator(
            start_timestamp=start_timestamp,
            cron_string=day_before,
            execution_timezone=execution_timezone,
            ascending=ascending,
            start_offset=start_offset,
        ):
            # only return on leap years
            if calendar.isleap(dt.year):
                # shift 28th back to 29th
                shifted_dt = dt + datetime.timedelta(days=1)
                yield shifted_dt
        return

    timezone_str = execution_timezone if execution_timezone else "UTC"

    # Croniter < 1.4 returns 2 items
    # Croniter >= 1.4 returns 3 items
    cron_parts, nth_weekday_of_month, *_ = CroniterShim.expand(cron_string)

    is_numeric = [len(part) == 1 and part[0] != "*" for part in cron_parts]
    is_wildcard = [len(part) == 1 and part[0] == "*" for part in cron_parts]

    known_schedule_type: Optional[ScheduleType] = None

    expected_hour = None
    expected_minute = None
    expected_day = None
    expected_day_of_week = None

    # Special-case common intervals (hourly/daily/weekly/monthly) since croniter iteration can be
    # much slower and has correctness issues on DST boundaries
    if not nth_weekday_of_month:
        if (
            all(is_numeric[0:3])
            and all(is_wildcard[3:])
            and int(cron_parts[2][0]) <= MAX_DAY_OF_MONTH_WITH_GUARANTEED_MONTHLY_INTERVAL
        ):  # monthly
            known_schedule_type = ScheduleType.MONTHLY
        elif all(is_numeric[0:2]) and is_numeric[4] and all(is_wildcard[2:4]):  # weekly
            known_schedule_type = ScheduleType.WEEKLY
        elif all(is_numeric[0:2]) and all(is_wildcard[2:]):  # daily
            known_schedule_type = ScheduleType.DAILY
        elif is_numeric[0] and all(is_wildcard[1:]):  # hourly
            known_schedule_type = ScheduleType.HOURLY

    if is_numeric[1]:
        expected_hour = int(cron_parts[1][0])

    if is_numeric[0]:
        expected_minute = int(cron_parts[0][0])

    if is_numeric[2]:
        expected_day = int(cron_parts[2][0])

    if is_numeric[4]:
        expected_day_of_week = int(cron_parts[4][0])

    if known_schedule_type:
        start_datetime = pendulum.from_timestamp(start_timestamp, tz=timezone_str)

        if start_offset == 0 and _exact_match(
            cron_string,
            known_schedule_type,
            expected_minute,
            expected_hour,
            expected_day,
            expected_day_of_week,
            start_datetime,
        ):
            # In simple cases, where you're already on a cron boundary, the below logic is unnecessary
            # and slow
            next_date = start_datetime
            # This is already on a cron boundary, so yield it
            yield start_datetime
        else:
            next_date = _find_schedule_time(
                expected_minute,
                expected_hour,
                expected_day,
                expected_day_of_week,
                known_schedule_type,
                start_datetime,
                ascending=not ascending,  # Going in the reverse direction
                already_on_boundary=False,
            )
            check.invariant(start_offset <= 0)
            for _ in range(-start_offset):
                next_date = _find_schedule_time(
                    expected_minute,
                    expected_hour,
                    expected_day,
                    expected_day_of_week,
                    known_schedule_type,
                    next_date,
                    ascending=not ascending,  # Going in the reverse direction
                    already_on_boundary=True,
                )

        while True:
            next_date = _find_schedule_time(
                expected_minute,
                expected_hour,
                expected_day,
                expected_day_of_week,
                known_schedule_type,
                next_date,
                ascending=ascending,
                already_on_boundary=True,
            )

            if start_offset == 0:
                if ascending:
                    # Guard against _find_schedule_time returning unexpected results
                    check.invariant(next_date.timestamp() >= start_timestamp)
                else:
                    check.invariant(next_date.timestamp() <= start_timestamp)

            yield next_date
    else:
        # Croniter doesn't behave nicely with pendulum timezones
        utc_datetime = pytz.utc.localize(datetime.datetime.utcfromtimestamp(start_timestamp))
        start_datetime = utc_datetime.astimezone(pytz.timezone(timezone_str))

        date_iter = CroniterShim(cron_string, start_datetime)
        # Go back one iteration so that the next iteration is the first time that is >= start_datetime
        # and matches the cron schedule
        next_date = (
            date_iter.get_prev(datetime.datetime)
            if ascending
            else date_iter.get_next(datetime.datetime)
        )

        if not CroniterShim.match(cron_string, next_date):
            # Workaround for upstream croniter bug where get_prev sometimes overshoots to a time
            # that doesn't actually match the cron string (e.g. 3AM on Spring DST day
            # goes back to 1AM on the previous day) - when this happens, advance to the correct
            # time that actually matches the cronstring
            next_date = (
                date_iter.get_next(datetime.datetime)
                if ascending
                else date_iter.get_prev(datetime.datetime)
            )

        check.invariant(start_offset <= 0)
        for _ in range(-start_offset):
            next_date = (
                date_iter.get_prev(datetime.datetime)
                if ascending
                else date_iter.get_next(datetime.datetime)
            )

        while True:
            next_date = to_timezone(
                pendulum.instance(
                    date_iter.get_next(datetime.datetime)
                    if ascending
                    else date_iter.get_prev(datetime.datetime)
                ),
                timezone_str,
            )

            if start_offset == 0:
                if ascending and next_date.timestamp() < start_timestamp:
                    # Guard against edge cases where croniter get_prev() returns unexpected
                    # results that would cause us to get stuck
                    continue

                if not ascending and next_date.timestamp() > start_timestamp:
                    continue

            yield next_date


def reverse_cron_string_iterator(
    end_timestamp: float, cron_string: str, execution_timezone: Optional[str]
) -> Iterator[datetime.datetime]:
    yield from cron_string_iterator(end_timestamp, cron_string, execution_timezone, ascending=False)


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
        yield from (
            cron_string_iterator(start_timestamp, cron_schedule, execution_timezone)
            if ascending
            else reverse_cron_string_iterator(start_timestamp, cron_schedule, execution_timezone)
        )
    else:
        iterators = [
            (
                cron_string_iterator(start_timestamp, cron_string, execution_timezone)
                if ascending
                else reverse_cron_string_iterator(start_timestamp, cron_string, execution_timezone)
            )
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
