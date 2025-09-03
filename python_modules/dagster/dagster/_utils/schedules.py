import calendar
import datetime
import functools
import math
import re
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Optional, Union

import dagster._check as check
from dagster._time import get_current_datetime, get_timezone
from dagster._vendored.croniter import croniter as _croniter
from dagster._vendored.dateutil.relativedelta import relativedelta
from dagster._vendored.dateutil.tz import datetime_ambiguous, datetime_exists

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.schedule_type import ScheduleType

# Monthly schedules with 29-31 won't reliably run every month
MAX_DAY_OF_MONTH_WITH_GUARANTEED_MONTHLY_INTERVAL = 28

CRON_RANGES = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7), (0, 59))
CRON_STEP_SEARCH_REGEX = re.compile(r"^([^-]+)-([^-/]+)(/(\d+))?$")
INT_REGEX = re.compile(r"^\d+$")

# hours in which it is possible that a time might be ambigious or not exist due to daylight savings time
DAYLIGHT_SAVINGS_HOURS = {1, 2, 3}


class CroniterShim(_croniter):
    """Lightweight shim to enable caching certain values that may be calculated many times."""

    @classmethod
    @functools.lru_cache(maxsize=128)
    def expand(cls, *args, **kwargs):  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().expand(*args, **kwargs)


def _is_simple_cron(
    cron_expression: str,
    dt: datetime.datetime,
) -> bool:
    """This function is purely an optimization to see if the provided datetime is already on an obvious boundary
    of the common and easy to detect (daily at midnight and on the hour). The optimization is to avoid calling
    _find_schedule_time to find the next cron boundary.
    """
    if cron_expression == "0 0 * * *":
        return dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.microsecond == 0

    if cron_expression == "0 * * * *":
        return dt.minute == 0 and dt.second == 0 and dt.microsecond == 0

    return False


def is_valid_cron_string(cron_string: str) -> bool:
    if not CroniterShim.is_valid(cron_string):
        return False

    # Croniter < 1.4 returns 2 items
    # Croniter >= 1.4 returns 3 items
    expanded, *_ = CroniterShim.expand(cron_string)

    # dagster only recognizes cron strings that resolve to 5 parts (e.g. not seconds resolution)
    if len(expanded) != 5:
        return False

    if len(expanded[3]) == 1 and expanded[3][0] == 2:  # February
        if len(expanded[2]) == 1 and expanded[2][0] in {30, 31}:  # 30th or 31st of February
            return False

    return True


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


def apply_fold_and_post_transition(date: datetime.datetime) -> datetime.datetime:
    date = apply_post_transition(date)
    return _apply_fold(date)


def _apply_fold(date: datetime.datetime) -> datetime.datetime:
    """For consistency, always choose the latter of the two possible times during a fall DST
    transition when there are two possibilities - match behavior described in the docs:
    https://docs.dagster.io/guides/automate/schedules/customizing-execution-timezone#execution-times-and-daylight-savings-time)

    Never call this with datetimes that could be non-existant. datetime_ambiguous will return true
    but folding them will leave them non-existant.
    """  # noqa: D415
    if date.fold == 0 and date.hour in DAYLIGHT_SAVINGS_HOURS and datetime_ambiguous(date):
        return date.replace(fold=1)
    return date


def apply_post_transition(
    date: datetime.datetime,
) -> datetime.datetime:
    if date.hour in DAYLIGHT_SAVINGS_HOURS and not datetime_exists(date):
        # If we fall on a non-existant time (e.g. between 2 and 3AM during a DST transition)
        # advance to the end of the window, which does exist - match behavior described in the docs:
        # https://docs.dagster.io/guides/automate/schedules/customizing-execution-timezone#execution-times-and-daylight-savings-time)

        # This assumes that all dst offsets are <= to an hour, which is true at time of writing.
        # The date passed to dst needs to be in DST to get the offset for the timezone.
        dst_offset = check.not_none(date.tzinfo).dst(date + datetime.timedelta(hours=1))

        # This assumes that all dst transitions happen on the hour, which is true at time of writing.
        # Rewind time to the start of the transition and then add the offset to get the first time out of the transition.
        start_dst = date.replace(minute=0, second=0, microsecond=0)
        return start_dst + check.not_none(dst_offset)
    return date


def _replace_date_fields(
    date: datetime.datetime,
    hour: int,
    minute: int,
    day: int,
):
    new_date = date.replace(
        day=day,
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )
    return apply_fold_and_post_transition(new_date)


SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60


def _find_hourly_schedule_time(
    minutes: Sequence[int],
    date: datetime.datetime,
    ascending: bool,
    already_on_boundary: bool,
) -> datetime.datetime:
    if ascending:
        # short-circuit if minutes and seconds are already correct
        if len(minutes) == 1 and (
            already_on_boundary
            or (date.minute == minutes[0] and date.second == 0 and date.microsecond == 0)
        ):
            # switch to utc so that timedelta behaves as expected instead of doing walltime math
            new_date = date.astimezone(datetime.timezone.utc) + datetime.timedelta(hours=1)
            new_date = new_date.astimezone(date.tzinfo)
            return new_date

        # clear microseconds
        new_timestamp = math.ceil(date.timestamp())
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
            if new_timestamp_cand <= date.timestamp():
                new_timestamp_cand = new_timestamp_cand + SECONDS_PER_MINUTE * MINUTES_PER_HOUR

            final_timestamp = (
                new_timestamp_cand
                if not final_timestamp
                else min(final_timestamp, new_timestamp_cand)
            )
    else:
        if len(minutes) == 1 and (
            already_on_boundary
            or (date.minute == minutes[0] and date.second == 0 and date.microsecond == 0)
        ):
            # switch to utc so that timedelta behaves as expected instead of doing walltime math
            new_date = date.astimezone(datetime.timezone.utc) - datetime.timedelta(hours=1)
            new_date = new_date.astimezone(date.tzinfo)
            return new_date

        # clear microseconds
        new_timestamp = math.floor(date.timestamp())
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
            if new_timestamp_cand >= date.timestamp():
                new_timestamp_cand = new_timestamp_cand - SECONDS_PER_MINUTE * MINUTES_PER_HOUR

            final_timestamp = (
                new_timestamp_cand
                if not final_timestamp
                else max(final_timestamp, new_timestamp_cand)
            )

    return datetime.datetime.fromtimestamp(check.not_none(final_timestamp), tz=date.tzinfo)


def _find_daily_schedule_time(
    minute: int,
    hour: int,
    date: datetime.datetime,
    ascending: bool,
    already_on_boundary: bool,
) -> datetime.datetime:
    # First move to the correct time of day today (ignoring whether it is the correct day)
    if not already_on_boundary or (
        date.hour != hour or date.minute != minute or date.second != 0 or date.microsecond != 0
    ):
        new_time = _replace_date_fields(
            date,
            hour,
            minute,
            date.day,
        )
    else:
        new_time = date

    if ascending:
        if already_on_boundary or new_time.timestamp() <= date.timestamp():
            new_time = new_time + datetime.timedelta(days=1)
    else:
        if already_on_boundary or new_time.timestamp() >= date.timestamp():
            new_time = new_time - datetime.timedelta(days=1)

    # If the hour or minute has changed the schedule in cronstring,
    # double-check that it's still correct in case we crossed a DST boundary
    if new_time.hour != hour or new_time.minute != minute:
        new_time = _replace_date_fields(
            new_time,
            hour,
            minute,
            new_time.day,
        )
    return apply_fold_and_post_transition(new_time)


def _get_crontab_day_of_week(dt: datetime.datetime) -> int:
    weekday = dt.isoweekday()
    # crontab has 0-6, sunday - saturday
    # isoweekday is 1-7 monday - sunday
    return weekday if weekday <= 6 else 0


def _find_weekly_schedule_time(
    minute: int,
    hour: int,
    day_of_week: int,
    date: datetime.datetime,
    ascending: bool,
    already_on_boundary: bool,
) -> datetime.datetime:
    # first move to the correct time of day
    if not already_on_boundary:
        new_time = _replace_date_fields(
            date,
            hour,
            minute,
            date.day,
        )
        # Move to the correct day of the week
        current_day_of_week = _get_crontab_day_of_week(new_time)

        if day_of_week != current_day_of_week:
            if ascending:
                new_time = new_time + relativedelta(days=(day_of_week - current_day_of_week) % 7)
            else:
                new_time = new_time - relativedelta(days=(current_day_of_week - day_of_week) % 7)
    else:
        new_time = date

    # Make sure that we've actually moved in the correct direction, advance if we haven't
    if ascending:
        if already_on_boundary or new_time.timestamp() <= date.timestamp():
            new_time = new_time + relativedelta(weeks=1)
    else:
        if already_on_boundary or new_time.timestamp() >= date.timestamp():
            new_time = new_time - relativedelta(weeks=1)

    # If the hour or minute has from the schedule in cronstring,
    # double-check that it's still correct in case we crossed a DST boundary
    if new_time.hour != hour or new_time.minute != minute:
        new_time = _replace_date_fields(
            new_time,
            hour,
            minute,
            new_time.day,
        )
    return apply_fold_and_post_transition(new_time)


def _find_monthly_schedule_time(
    minute: int,
    hour: int,
    day: int,
    date: datetime.datetime,
    ascending: bool,
    already_on_boundary: bool,
) -> datetime.datetime:
    # First move to the correct day and time of day
    if not already_on_boundary:
        new_time = _replace_date_fields(
            date,
            check.not_none(hour),
            check.not_none(minute),
            check.not_none(day),
        )
    else:
        new_time = date

    if ascending:
        if already_on_boundary or new_time.timestamp() <= date.timestamp():
            new_time = new_time + relativedelta(months=1)
    else:
        if already_on_boundary or new_time.timestamp() >= date.timestamp():
            # Move back a month if needed
            new_time = new_time - relativedelta(months=1)

    # If the hour or minute has changed from the schedule in cronstring,
    # double-check that it's still correct in case we crossed a DST boundary
    if new_time.hour != hour or new_time.minute != minute:
        new_time = _replace_date_fields(
            new_time,
            check.not_none(hour),
            check.not_none(minute),
            check.not_none(day),
        )

    return apply_fold_and_post_transition(new_time)


def _find_schedule_time(
    minutes: Optional[Sequence[int]],
    hour: Optional[int],
    day_of_month: Optional[int],
    day_of_week: Optional[int],
    schedule_type: "ScheduleType",
    date: datetime.datetime,
    ascending: bool,
    # lets us skip slow work to find the starting point if we know that
    # we are already on the boundary of the cron interval
    already_on_boundary: bool,
) -> datetime.datetime:
    from dagster._core.definitions.partitions.schedule_type import ScheduleType

    if schedule_type == ScheduleType.HOURLY:
        return _find_hourly_schedule_time(
            check.not_none(minutes), date, ascending, already_on_boundary
        )
    elif schedule_type == ScheduleType.DAILY:
        minutes = check.not_none(minutes)
        check.invariant(len(minutes) == 1)
        return _find_daily_schedule_time(
            minutes[0],
            check.not_none(hour),
            date,
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
            date,
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
            date,
            ascending,
            already_on_boundary,
        )
    else:
        raise Exception(f"Unexpected schedule type {schedule_type}")


def _get_dates_to_consider_after_ambigious_time(
    cron_iter: CroniterShim,
    next_date: datetime.datetime,
    repeats_every_hour: bool,
    ascending: bool,
):
    # Return a list of all times that need to be considered when the next date returned by
    # croniter is ambigious (e.g. 2:30 AM during a fall DST transition). This is tricky because
    # we need to make sure that we are emitting times in the correct order, so we return a sorted
    # contiguous sequence of times that include all potentially ambigious times.
    post_transition_time = next_date.replace(fold=1)

    # Most schedules only need to consider the POST_TRANSITION time and can return here.
    if not repeats_every_hour:
        return [post_transition_time]

    # hourly schedules are more complicated - they'll continue firing once an hour no
    # matter what, including both PRE_TRANSITION and POST_TRANSITION times. So we need
    # to make sure that every time in the ambigious timerange has both its PRE_TRANSITION
    # and POST_TRANSITION times considered and returned.
    pre_transition_time = next_date.replace(fold=0)
    dates_to_consider = [post_transition_time, pre_transition_time]

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
        curr_pre_transition_time = datetime.datetime(
            year=next_date.year,
            month=next_date.month,
            day=next_date.day,
            hour=next_date.hour,
            minute=next_date.minute,
            second=next_date.second,
            microsecond=next_date.microsecond,
            fold=0,
            tzinfo=post_transition_time.tzinfo,
        )
        dates_to_consider.append(curr_pre_transition_time)
        curr_post_transition_time = datetime.datetime(
            year=next_date.year,
            month=next_date.month,
            day=next_date.day,
            hour=next_date.hour,
            minute=next_date.minute,
            second=next_date.second,
            microsecond=next_date.microsecond,
            fold=1,
            tzinfo=post_transition_time.tzinfo,
        )
        dates_to_consider.append(curr_post_transition_time)

    return sorted(dates_to_consider, key=lambda d: d.timestamp())


def _timezone_aware_cron_iter(
    cron_string, start_datetime: datetime.datetime, ascending: bool
) -> Iterator[datetime.datetime]:
    """Use croniter to determine the next timestamp matching the passed in cron string
    that is past the passed in UTC timestamp. croniter can only be trusted to compute
    non-timezone aware cron intervals, so we first figure out the time corresponding to the
    passed in timestamp without taking any timezones into account, use croniter to
    determine the next time that matches the cron string, translate that back into the passed in
    timezone, and repeat, returning the first time that is later than the passed in timestamp.
    """
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
    start_timestamp = start_datetime.timestamp()
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
        next_date_with_tz = datetime.datetime(
            year=next_date.year,
            month=next_date.month,
            day=next_date.day,
            hour=next_date.hour,
            minute=next_date.minute,
            second=next_date.second,
            microsecond=next_date.microsecond,
            tzinfo=start_datetime.tzinfo,
        )

        dates_to_consider = [next_date_with_tz]
        if not datetime_exists(next_date_with_tz):
            if repeats_every_hour:
                # hourly schedules just move on to the next time
                dates_to_consider = []
            else:
                # other schedules advance to the time at the end of the interval (so that e.g.
                # a daily schedule doesn't miss an entire day)
                dates_to_consider = [apply_post_transition(next_date_with_tz)]
        elif datetime_ambiguous(next_date_with_tz):
            dates_to_consider = _get_dates_to_consider_after_ambigious_time(
                cron_iter=cron_iter,
                next_date=next_date_with_tz,
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
                    r"^\*(\/.+)$",
                    r"%d-%d\1" % (CRON_RANGES[i][0], CRON_RANGES[i][1]),  # noqa: UP031
                    str(expr),
                )
                m = CRON_STEP_SEARCH_REGEX.search(t)
                if not m:
                    # try normalizing "{start}/{step}" to "{start}-{max}/{step}".
                    t = re.sub(r"^(.+)\/(.+)$", r"\1-%d/\2" % (CRON_RANGES[i][1]), str(expr))  # noqa: UP031
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
    from dagster._core.definitions.partitions.schedule_type import ScheduleType

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
    execution_timezone = execution_timezone or "UTC"

    # Croniter < 1.4 returns 2 items
    # Croniter >= 1.4 returns 3 items
    cron_parts, nth_weekday_of_month, *_ = CroniterShim.expand(cron_string)

    is_numeric = [len(part) == 1 and isinstance(part[0], int) for part in cron_parts]
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
            and cron_parts[2][0] <= MAX_DAY_OF_MONTH_WITH_GUARANTEED_MONTHLY_INTERVAL  # pyright: ignore[reportOperatorIssue]
        ):  # monthly
            known_schedule_type = ScheduleType.MONTHLY
        elif all(is_numeric[0:2]) and is_numeric[4] and all(is_wildcard[2:4]):  # weekly
            known_schedule_type = ScheduleType.WEEKLY
        elif all(is_numeric[0:2]) and all(is_wildcard[2:]):  # daily
            known_schedule_type = ScheduleType.DAILY
        elif all_numeric_minutes and all(is_wildcard[1:]):  # hourly
            known_schedule_type = ScheduleType.HOURLY

    if is_numeric[1]:
        expected_hour = cron_parts[1][0]

    if all_numeric_minutes:
        expected_minutes = [cron_part for cron_part in cron_parts[0]]

    if is_numeric[2]:
        expected_day = cron_parts[2][0]

    if is_numeric[4]:
        expected_day_of_week = cron_parts[4][0]

    if known_schedule_type:
        start_datetime = datetime.datetime.fromtimestamp(
            start_timestamp, tz=get_timezone(execution_timezone)
        )

        if start_offset == 0 and _is_simple_cron(cron_string, start_datetime):
            # In simple cases, where you're already on a cron boundary, the below logic is unnecessary
            # and slow
            next_date = start_datetime
            # This is already on a cron boundary, so yield it
            yield start_datetime
        else:
            next_date = _find_schedule_time(
                expected_minutes,  # pyright: ignore[reportArgumentType]
                expected_hour,  # pyright: ignore[reportArgumentType]
                expected_day,  # pyright: ignore[reportArgumentType]
                expected_day_of_week,  # pyright: ignore[reportArgumentType]
                known_schedule_type,
                start_datetime,
                ascending=not ascending,  # Going in the reverse direction
                already_on_boundary=False,
            )
            check.invariant(start_offset <= 0)
            for _ in range(-start_offset):
                next_date = _find_schedule_time(
                    expected_minutes,  # pyright: ignore[reportArgumentType]
                    expected_hour,  # pyright: ignore[reportArgumentType]
                    expected_day,  # pyright: ignore[reportArgumentType]
                    expected_day_of_week,  # pyright: ignore[reportArgumentType]
                    known_schedule_type,
                    next_date,
                    ascending=not ascending,  # Going in the reverse direction
                    already_on_boundary=True,
                )

        while True:
            next_date = _find_schedule_time(
                expected_minutes,  # pyright: ignore[reportArgumentType]
                expected_hour,  # pyright: ignore[reportArgumentType]
                expected_day,  # pyright: ignore[reportArgumentType]
                expected_day_of_week,  # pyright: ignore[reportArgumentType]
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
            start_timestamp, cron_string, execution_timezone, ascending, start_offset
        )


def _croniter_string_iterator(
    start_timestamp: float,
    cron_string: str,
    timezone_str: str,
    ascending: bool = True,
    start_offset: int = 0,
):
    start_datetime = datetime.datetime.fromtimestamp(start_timestamp, get_timezone(timezone_str))
    reverse_cron = _timezone_aware_cron_iter(cron_string, start_datetime, ascending=not ascending)
    next_date = None
    check.invariant(start_offset <= 0)
    for _ in range(-start_offset + 1):
        next_date = next(reverse_cron)
    next_date = check.not_none(next_date).astimezone(start_datetime.tzinfo)
    forward_cron = _timezone_aware_cron_iter(cron_string, next_date, ascending=ascending)
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
    end_timestamp: float,
    cron_string: str,
    execution_timezone: Optional[str],
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
    cron_string: str,
    current_time: datetime.datetime,
    timezone: Optional[str],
) -> datetime.datetime:
    cron_iter = reverse_cron_string_iterator(
        end_timestamp=current_time.timestamp(),
        cron_string=cron_string,
        execution_timezone=timezone,
    )
    return next(cron_iter)


def get_next_cron_tick(
    cron_string: str,
    current_time: datetime.datetime,
    timezone: Optional[str],
) -> datetime.datetime:
    cron_iter = cron_string_iterator(
        start_timestamp=current_time.timestamp(),
        cron_string=cron_string,
        execution_timezone=timezone,
    )
    return next(cron_iter)


def get_smallest_cron_interval(
    cron_string: str,
    execution_timezone: Optional[str] = None,
) -> datetime.timedelta:
    """Find the smallest interval between cron ticks for a given cron schedule.

    Uses a sampling-based approach to find the minimum interval by generating
    consecutive cron ticks and measuring the gaps between them. Sampling stops
    early if either of these limits is reached:
      - A maximum of 1000 generated ticks
      - A time horizon of 20 years past the sampling start

    Args:
        cron_string: A cron string
        execution_timezone: Timezone to use for cron evaluation (defaults to UTC)

    Returns:
        The smallest timedelta between any two consecutive cron ticks

    Raises:
        CheckError: If the cron string is invalid or not recognized by Dagster
    """
    check.invariant(
        is_valid_cron_string(cron_string), desc=f"{cron_string} must be a valid cron string"
    )

    execution_timezone = execution_timezone or "UTC"

    # Always start at current time in the specified timezone
    start_time = get_current_datetime(tz=execution_timezone)

    # Start sampling from a year ago to capture seasonal variations (DST, leap years)
    sampling_start = start_time - datetime.timedelta(days=365)
    # Cap the lookahead horizon to avoid extremely distant datetimes (e.g., year ~3000 on Windows)
    horizon_deadline = sampling_start + relativedelta(years=20)

    # Generate consecutive cron ticks
    cron_iter = schedule_execution_time_iterator(
        start_timestamp=sampling_start.timestamp(),
        cron_schedule=cron_string,
        execution_timezone=execution_timezone,
        ascending=True,
    )

    # Collect the first tick
    prev_tick = next(cron_iter)
    min_interval = None

    # Sample up to 1000 ticks, but also stop at the 20-year horizon
    for _ in range(999):
        try:
            current_tick = next(cron_iter)
            # Stop if we've gone beyond our lookahead horizon
            if current_tick > horizon_deadline:
                break
            interval = current_tick - prev_tick

            # Update minimum interval
            if min_interval is None or interval < min_interval:
                min_interval = interval

            prev_tick = current_tick

        except StopIteration:
            # This shouldn't happen with cron iterators, but handle gracefully
            break

    if min_interval is None:
        # Fallback - should not happen with valid cron schedules
        raise ValueError("Could not determine minimum interval from cron schedule")

    return min_interval
