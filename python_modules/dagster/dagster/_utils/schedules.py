import calendar
import datetime
import functools
import math
import re
from typing import Iterator, Optional, Sequence, Union

import pendulum
from croniter import croniter as _croniter

import dagster._check as check
from dagster._core.definitions.partition import ScheduleType
from dagster._seven.compat.pendulum import (
    POST_TRANSITION,
    PRE_TRANSITION,
    TRANSITION_ERROR,
    PendulumDateTime,
    create_pendulum_time,
    get_crontab_day_of_week,
)

# Monthly schedules with 29-31 won't reliably run every month
MAX_DAY_OF_MONTH_WITH_GUARANTEED_MONTHLY_INTERVAL = 28

CRON_RANGES = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7), (0, 59))
CRON_STEP_SEARCH_REGEX = re.compile(r"^([^-]+)-([^-/]+)(/(\d+))?$")
INT_REGEX = re.compile(r"^\d+$")


class CroniterShim(_croniter):
    """Lightweight shim to enable caching certain values that may be calculated many times."""

    @classmethod
    @functools.lru_cache(maxsize=128)
    def expand(cls, *args, **kwargs):
        return super().expand(*args, **kwargs)


def _exact_match(
    cron_expression: str,
    schedule_type: ScheduleType,
    minutes: Optional[Sequence[int]],
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
            cron_expression,
            minutes,
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


def cron_string_repeats_every_hour(cron_string: str) -> bool:
    """Returns if the given cron schedule repeats every hour."""
    cron_parts, nth_weekday_of_month, *_ = CroniterShim.expand(cron_string)
    return len(cron_parts[1]) == 1 and cron_parts[1][0] == "*"


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
            dst_rule=TRANSITION_ERROR,
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
            dst_rule=TRANSITION_ERROR,
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
            dst_rule=POST_TRANSITION,
        )

    return new_time


SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60


def _find_hourly_schedule_time(
    minutes: Sequence[int],
    pendulum_date: PendulumDateTime,
    ascending: bool,
    already_on_boundary: bool,
) -> PendulumDateTime:
    if ascending:
        # short-circuit if minutes and seconds are already correct
        if len(minutes) == 1 and (
            already_on_boundary
            or (
                pendulum_date.minute == minutes[0]
                and pendulum_date.second == 0
                and pendulum_date.microsecond == 0
            )
        ):
            return pendulum_date.add(hours=1)

        # clear microseconds
        new_timestamp = math.ceil(pendulum_date.timestamp())
        # clear seconds
        new_timestamp = (
            new_timestamp
            + (SECONDS_PER_MINUTE - new_timestamp % SECONDS_PER_MINUTE) % SECONDS_PER_MINUTE
        )

        current_minute = (new_timestamp // SECONDS_PER_MINUTE) % SECONDS_PER_MINUTE

        final_timestamp = None

        for minute in minutes:
            new_timestamp_cand = new_timestamp + SECONDS_PER_MINUTE * (
                (minute - current_minute) % MINUTES_PER_HOUR
            )

            # move forward an hour if we haven't moved forwards yet
            if new_timestamp_cand <= pendulum_date.timestamp():
                new_timestamp_cand = new_timestamp_cand + SECONDS_PER_MINUTE * MINUTES_PER_HOUR

            final_timestamp = (
                new_timestamp_cand
                if not final_timestamp
                else min(final_timestamp, new_timestamp_cand)
            )

    else:
        if len(minutes) == 1 and (
            already_on_boundary
            or (
                pendulum_date.minute == minutes[0]
                and pendulum_date.second == 0
                and pendulum_date.microsecond == 0
            )
        ):
            return pendulum_date.subtract(hours=1)

        # clear microseconds
        new_timestamp = math.floor(pendulum_date.timestamp())
        # clear seconds
        new_timestamp = new_timestamp - new_timestamp % SECONDS_PER_MINUTE

        # move minutes back to correct place
        current_minute = (new_timestamp // SECONDS_PER_MINUTE) % SECONDS_PER_MINUTE

        final_timestamp = None

        for minute in minutes:
            new_timestamp_cand = new_timestamp - SECONDS_PER_MINUTE * (
                (current_minute - minute) % MINUTES_PER_HOUR
            )

            # move back an hour if we haven't moved backwards yet
            if new_timestamp_cand >= pendulum_date.timestamp():
                new_timestamp_cand = new_timestamp_cand - SECONDS_PER_MINUTE * MINUTES_PER_HOUR

            final_timestamp = (
                new_timestamp_cand
                if not final_timestamp
                else max(final_timestamp, new_timestamp_cand)
            )

    return pendulum.from_timestamp(final_timestamp, tz=pendulum_date.timezone_name)


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
        current_day_of_week = get_crontab_day_of_week(new_time)

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
    cron_string: str,
    minutes: Optional[Sequence[int]],
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
            check.not_none(minutes), pendulum_date, ascending, already_on_boundary
        )
    elif schedule_type == ScheduleType.DAILY:
        minutes = check.not_none(minutes)
        check.invariant(len(minutes) == 1)
        return _find_daily_schedule_time(
            minutes[0],
            check.not_none(hour),
            pendulum_date,
            ascending,
            already_on_boundary,
        )
    elif schedule_type == ScheduleType.WEEKLY:
        minutes = check.not_none(minutes)
        check.invariant(len(minutes) == 1)
        return _find_weekly_schedule_time(
            minutes[0],
            check.not_none(hour),
            check.not_none(day_of_week),
            pendulum_date,
            ascending,
            already_on_boundary,
        )
    elif schedule_type == ScheduleType.MONTHLY:
        minutes = check.not_none(minutes)
        check.invariant(len(minutes) == 1)
        return _find_monthly_schedule_time(
            minutes[0],
            check.not_none(hour),
            check.not_none(day_of_month),
            pendulum_date,
            ascending,
            already_on_boundary,
        )
    else:
        raise Exception(f"Unexpected schedule type {schedule_type}")


def _get_dates_to_consider_after_ambigious_time(
    cron_iter: CroniterShim,
    next_date: datetime.datetime,
    timezone_str: str,
    repeats_every_hour: bool,
    ascending: bool,
):
    # Return a list of all times that need to be considered when the next date returned by
    # croniter is ambigious (e.g. 2:30 AM during a fall DST transition). This is tricky because
    # we need to make sure that we are emitting times in the correct order, so we return a sorted
    # contiguous sequence of times that include all potentially ambigious times.
    post_transition_time = create_pendulum_time(
        next_date.year,
        next_date.month,
        next_date.day,
        next_date.hour,
        next_date.minute,
        next_date.second,
        next_date.microsecond,
        tz=timezone_str,
        dst_rule=POST_TRANSITION,
    )

    dates_to_consider = [post_transition_time]

    # Most schedules only need to consider the POST_TRANSITION time and can return here.
    if not repeats_every_hour:
        return [post_transition_time]

    # hourly schedules are more complicated - they'll continue firing once an hour no
    # matter what, including both PRE_TRANSITION and POST_TRANSITION times. So we need
    # to make sure that every time in the ambigious timerange has both its PRE_TRANSITION
    # and POST_TRANSITION times considered and returned.
    pre_transition_time = create_pendulum_time(
        next_date.year,
        next_date.month,
        next_date.day,
        next_date.hour,
        next_date.minute,
        next_date.second,
        next_date.microsecond,
        tz=timezone_str,
        dst_rule=PRE_TRANSITION,
    )
    dates_to_consider.append(pre_transition_time)

    # fill in any gaps between pre-transition time and post-transition time
    curr_pre_transition_time = pre_transition_time
    curr_post_transition_time = post_transition_time
    while True:
        if ascending:
            # Time always advances because get_next() is called, so we will eventually break
            # Stop once the current PRE_TRANSITION time exceeds the original POST_TRANSITION time
            # (so we know we have moved forward across the whole range)
            if curr_pre_transition_time.timestamp() >= post_transition_time.timestamp():
                break
            next_date = cron_iter.get_next(datetime.datetime)
        else:
            # Time always decreases because get_prev() is called, so we will eventually break
            # Stop once the current POST_TRANSITION time has gone past the original PRE_TRANSITION
            # time (so we know we have moved backward across the whole range)
            if curr_post_transition_time.timestamp() <= pre_transition_time.timestamp():
                break
            next_date = cron_iter.get_prev(datetime.datetime)

        # Make sure we add both the PRE_TRANSITION and POST_TRANSITION times to the
        # list of dates to consider so every time emitted by the
        # croniter instance is considered and returned from the calling iterator
        curr_pre_transition_time = create_pendulum_time(
            next_date.year,
            next_date.month,
            next_date.day,
            next_date.hour,
            next_date.minute,
            next_date.second,
            next_date.microsecond,
            tz=timezone_str,
            dst_rule=PRE_TRANSITION,
        )
        dates_to_consider.append(curr_pre_transition_time)

        curr_post_transition_time = create_pendulum_time(
            next_date.year,
            next_date.month,
            next_date.day,
            next_date.hour,
            next_date.minute,
            next_date.second,
            next_date.microsecond,
            tz=timezone_str,
            dst_rule=POST_TRANSITION,
        )
        dates_to_consider.append(curr_post_transition_time)

    return sorted(dates_to_consider, key=lambda d: d.timestamp())


def _timezone_aware_cron_iter(
    cron_string, timezone_str: str, start_timestamp: float, ascending: bool
) -> Iterator[PendulumDateTime]:
    """Use croniter to determine the next timestamp matching the passed in cron string
    that is past the passed in UTC timestamp. croniter can only be trusted to compute
    non-timezone aware cron intervals, so we first figure out the time corresponding to the
    passed in timestamp without taking any timezones into account, use croniter to
    determine the next time that matches the cron string, translate that back into the passed in
    timezone, and repeat, returning the first time that is later than the passed in timestamp.
    """
    start_datetime = pendulum.from_timestamp(start_timestamp, tz=timezone_str)

    # Create a naive (timezone-free) datetime to pass into croniter
    naive_time = datetime.datetime(
        year=start_datetime.year,
        month=start_datetime.month,
        day=start_datetime.day,
        hour=start_datetime.hour,
        minute=start_datetime.minute,
        second=start_datetime.second,
        microsecond=start_datetime.microsecond,
    )

    # Go back an hour to ensure that we consider the full set of possible candidates (otherwise
    # we might fail to properly consider a time that happens twice during a fall DST transition).
    # 1 hour is sufficient because that's the maximum amount of time that can be offset during a
    # DST transition.
    if ascending:
        naive_time = naive_time - datetime.timedelta(hours=1)
    else:
        naive_time = naive_time + datetime.timedelta(hours=1)

    cron_iter = CroniterShim(cron_string, naive_time)

    # hourly schedules handle DST transitions differently: they skip times that don't exist
    # entirely and just move on to the next matching time (instead of returning
    # the end time of the non-existant interval), and when there are two times that match the cron
    # string, they return both instead of picking the latter time.
    repeats_every_hour = cron_string_repeats_every_hour(cron_string)

    # Chronological order of dates to return
    dates_to_consider = []

    while True:
        # Work through everything currently in dates_to_consider
        if ascending:
            for next_date_with_tz in dates_to_consider:
                next_timestamp = next_date_with_tz.timestamp()
                if next_timestamp > start_timestamp:
                    start_timestamp = next_timestamp
                    yield next_date_with_tz
        else:
            for next_date_with_tz in reversed(dates_to_consider):
                next_timestamp = next_date_with_tz.timestamp()
                if next_timestamp < start_timestamp:
                    start_timestamp = next_timestamp
                    yield next_date_with_tz

        # Clear the list and generate new candidates using croniter
        dates_to_consider = []

        if ascending:
            next_date = cron_iter.get_next(datetime.datetime)
        else:
            next_date = cron_iter.get_prev(datetime.datetime)

        try:
            dates_to_consider = [
                create_pendulum_time(
                    next_date.year,
                    next_date.month,
                    next_date.day,
                    next_date.hour,
                    next_date.minute,
                    next_date.second,
                    next_date.microsecond,
                    tz=timezone_str,
                    dst_rule=TRANSITION_ERROR,
                )
            ]
        except pendulum.tz.exceptions.NonExistingTime:  # type:ignore
            if repeats_every_hour:
                # hourly schedules just move on to the next time
                dates_to_consider = []
            else:
                # other schedules advance to the time at the end of the interval (so that e.g.
                # a daily schedule doesn't miss an entire day)
                dates_to_consider = [
                    create_pendulum_time(
                        next_date.year,
                        next_date.month,
                        next_date.day,
                        next_date.hour + 1,
                        0,
                        0,
                        0,
                        tz=timezone_str,
                        dst_rule=TRANSITION_ERROR,
                    )
                ]
        except pendulum.tz.exceptions.AmbiguousTime:  # type: ignore
            dates_to_consider = _get_dates_to_consider_after_ambigious_time(
                cron_iter=cron_iter,
                next_date=next_date,
                timezone_str=timezone_str,
                repeats_every_hour=repeats_every_hour,
                ascending=ascending,
            )


def _has_out_of_range_cron_interval_str(cron_string: str):
    assert CroniterShim.is_valid(cron_string)
    try:
        for i, cron_part in enumerate(cron_string.lower().split()):
            expr_parts = cron_part.split(",")
            while len(expr_parts) > 0:
                expr = expr_parts.pop()
                t = re.sub(
                    r"^\*(\/.+)$", r"%d-%d\1" % (CRON_RANGES[i][0], CRON_RANGES[i][1]), str(expr)
                )
                m = CRON_STEP_SEARCH_REGEX.search(t)
                if not m:
                    # try normalizing "{start}/{step}" to "{start}-{max}/{step}".
                    t = re.sub(r"^(.+)\/(.+)$", r"\1-%d/\2" % (CRON_RANGES[i][1]), str(expr))
                    m = CRON_STEP_SEARCH_REGEX.search(t)
                if m:
                    (low, high, step) = m.group(1), m.group(2), m.group(4) or 1
                    if i == 2 and high == "l":
                        high = "31"
                    if not INT_REGEX.search(low) or not INT_REGEX.search(high):
                        continue
                    low, high, step = map(int, [low, high, step])
                    if step > high:
                        return True
    except:
        pass
    return False


def has_out_of_range_cron_interval(cron_schedule: Union[str, Sequence[str]]):
    """Utility function to detect cron schedules like '*/90 * * * *', which are valid cron schedules
    but which evaluate to once every hour, not once every 90 minutes as might be expected.  This is
    useful to detect so that we can issue warnings or some other kind of feedback to the user.  This
    function does not detect cases where the step does not divide cleanly in the range, which is
    another case that might cause some surprising behavior (e.g. '*/7 * * * *').
    """
    return (
        _has_out_of_range_cron_interval_str(cron_schedule)
        if isinstance(cron_schedule, str)
        else any(_has_out_of_range_cron_interval_str(s) for s in cron_schedule)
    )


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

    all_numeric_minutes = len(cron_parts[0]) > 0 and all(
        cron_part != "*" for cron_part in cron_parts[0]
    )

    known_schedule_type: Optional[ScheduleType] = None

    expected_hour = None
    expected_minutes = None
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
        elif all_numeric_minutes and all(is_wildcard[1:]):  # hourly
            known_schedule_type = ScheduleType.HOURLY

    if is_numeric[1]:
        expected_hour = int(cron_parts[1][0])

    if all_numeric_minutes:
        expected_minutes = [int(cron_part) for cron_part in cron_parts[0]]

    if is_numeric[2]:
        expected_day = int(cron_parts[2][0])

    if is_numeric[4]:
        expected_day_of_week = int(cron_parts[4][0])

    if known_schedule_type:
        start_datetime = pendulum.from_timestamp(start_timestamp, tz=timezone_str)

        if start_offset == 0 and _exact_match(
            cron_string,
            known_schedule_type,
            expected_minutes,
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
                cron_string,
                expected_minutes,
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
                    cron_string,
                    expected_minutes,
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
                cron_string,
                expected_minutes,
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
        yield from _croniter_string_iterator(
            start_timestamp, cron_string, timezone_str, ascending, start_offset
        )


def _croniter_string_iterator(
    start_timestamp: float,
    cron_string: str,
    timezone_str: str,
    ascending: bool = True,
    start_offset: int = 0,
):
    reverse_cron = _timezone_aware_cron_iter(
        cron_string, timezone_str, start_timestamp, ascending=not ascending
    )
    next_date = None
    check.invariant(start_offset <= 0)
    for _ in range(-start_offset + 1):
        next_date = next(reverse_cron)

    forward_cron = _timezone_aware_cron_iter(
        cron_string, timezone_str, check.not_none(next_date).timestamp(), ascending=ascending
    )
    while True:
        next_date = next(forward_cron)

        if start_offset == 0:
            if ascending:
                # Guard against _find_schedule_time returning unexpected results
                check.invariant(next_date.timestamp() >= start_timestamp)
            else:
                check.invariant(next_date.timestamp() <= start_timestamp)

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


def get_latest_completed_cron_tick(
    freshness_cron: Optional[str], current_time: datetime.datetime, timezone: Optional[str]
) -> Optional[datetime.datetime]:
    if not freshness_cron:
        return None

    cron_iter = reverse_cron_string_iterator(
        end_timestamp=current_time.timestamp(),
        cron_string=freshness_cron,
        execution_timezone=timezone,
    )
    return pendulum.instance(next(cron_iter))
