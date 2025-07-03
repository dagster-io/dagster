import time
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Union, cast

import dagster._check as check
from dagster._vendored.dateutil import parser

try:
    # zoneinfo is python >= 3.9
    from zoneinfo import ZoneInfo as _timezone_from_string
except:
    from dagster._vendored.dateutil.tz import gettz as _timezone_from_string


def _mockable_get_current_datetime() -> datetime:
    # Can be mocked in tests by freeze_time()
    return datetime.now(tz=timezone.utc)


def get_current_datetime(tz="UTC") -> datetime:
    """Return the current datetime. Will always have a timezone
    (defaults to UTC if none is specified). Value can be mocked
    via dagster._core.test_utils.freeze_time.
    """
    utc_datetime = _mockable_get_current_datetime()

    if tz == "utc" or tz == "UTC":
        return utc_datetime

    return utc_datetime.astimezone(get_timezone(tz))


def _mockable_get_current_timestamp() -> float:
    return time.time()


def get_current_datetime_midnight(tz="UTC") -> datetime:
    """Return the current date at midnight as a datetime object. Will always have a timezone
    (defaults to UTC if none is specified). Value can be mocked via dagster._core.test_utils.freeze_time.
    """
    return get_current_datetime(tz).replace(hour=0, minute=0, second=0, microsecond=0)


def get_current_timestamp() -> float:
    """Return the current unix timestamp. Value can be mocked
    via dagster._core.test_utils.freeze_time.
    """
    # Like time.time() but can be mocked in tests by freeze_time()
    return _mockable_get_current_timestamp()


def get_timezone(timezone_name: str) -> tzinfo:
    """Creates a tzinfo object with the given IANA timezone name."""
    if timezone_name == "utc" or timezone_name == "UTC":
        return timezone.utc

    return check.not_none(_timezone_from_string(timezone_name))


def create_datetime(year, month, day, *args, **kwargs):
    """Creates a datetime object. Same arguments as datetime.datetime
    constructor, but will always have a timezone (defaults to UTC if none is specified).
    """
    tz = kwargs.pop("tz", "UTC")
    if isinstance(tz, str):
        tz = get_timezone(tz)
    return datetime(year, month, day, *args, **kwargs, tzinfo=tz)


def datetime_from_timestamp(timestamp: float, tz: Union[str, tzinfo] = timezone.utc) -> datetime:
    """Creates a datetime object from a unix timestamp. Will always have a timezone
    (defaults to UTC if none is specified).
    """
    if not tz:
        tzinfo = timezone.utc
    elif isinstance(tz, str):
        tzinfo = get_timezone(tz)
    else:
        tzinfo = tz

    return datetime.fromtimestamp(timestamp, tz=tzinfo)


def utc_datetime_from_naive(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc)


def add_absolute_time(
    dt: datetime,
    *,
    hours=0,
    minutes=0,
    seconds=0,
    milliseconds=0,
    microseconds=0,
):
    """Behaves like adding a time using a timedelta, but handles fall DST transitions correctly
    without skipping an hour ahead.
    """
    return (
        dt.astimezone(timezone.utc)
        + timedelta(
            seconds=seconds,
            microseconds=microseconds,
            milliseconds=milliseconds,
            minutes=minutes,
            hours=hours,
        )
    ).astimezone(dt.tzinfo)


def parse_time_string(datetime_str) -> datetime:
    """Like dateutil.parser.parse, but always includes a timezone (defaults to UTC if
    no timezone is included in the timezone string).
    """
    dt = parser.parse(datetime_str)

    if not dt.tzinfo:  # pyright: ignore[reportAttributeAccessIssue]
        dt = dt.replace(tzinfo=timezone.utc)  # pyright: ignore[reportAttributeAccessIssue]

    return dt  # pyright: ignore[reportReturnType]


def is_second_ambiguous_time(dt: datetime, tz: str):
    """Returns if a datetime is the second instance of an ambiguous time in the given timezone due
    to DST transitions. Assumes that dt is alraedy in the specified timezone.
    """
    # UTC is never ambiguous
    if tz.upper() == "UTC":
        return False

    # Ensure that the datetime is in the correct timezone
    tzinfo = check.not_none(dt.tzinfo)

    # Only interested in the second instance of an ambiguous time
    if dt.fold == 0:
        return False

    offset_before = cast(
        "timedelta",
        (tzinfo.utcoffset(dt.replace(fold=0)) if dt.fold else tzinfo.utcoffset(dt)),
    )
    offset_after = cast(
        "timedelta",
        (tzinfo.utcoffset(dt) if dt.fold else tzinfo.utcoffset(dt.replace(fold=1))),
    )
    return offset_before > offset_after


def dst_safe_fmt(fmt: str) -> str:
    """Adds UTC offset information to a datetime format string to disambiguate timestamps around DST
    transitions.
    """
    if "%z" in fmt:
        return fmt
    return fmt + "%z"


def dst_safe_strftime(dt: datetime, tz: str, fmt: str, cron_schedule: str) -> str:
    """A method for converting a datetime to a string which will append a suffix in cases where
    the resulting timestamp would be ambiguous due to DST transitions.

    Assumes that dt is already in the specified timezone.
    """
    from dagster._utils.schedules import cron_string_repeats_every_hour

    # if the format already includes a UTC offset, then we don't need to do anything
    if "%z" in fmt:
        return dt.strftime(fmt)

    # only need to handle ambiguous times for cron schedules which repeat every hour
    if not cron_string_repeats_every_hour(cron_schedule):
        return dt.strftime(fmt)

    # if the datetime is the second instance of an ambiguous time, then we append the UTC offset
    if is_second_ambiguous_time(dt, tz):
        return dt.strftime(dst_safe_fmt(fmt))
    return dt.strftime(fmt)


def dst_safe_strptime(date_string: str, tz: str, fmt: str) -> datetime:
    """A method for parsing a datetime created with the dst_safe_strftime() method."""
    try:
        # first, try to parse the datetime in the normal format
        dt = datetime.strptime(date_string, fmt)
    except ValueError:
        # if this fails, try to parse the datetime with a UTC offset added
        dt = datetime.strptime(date_string, dst_safe_fmt(fmt))

    # the datetime object may have timezone information on it, depending on the format used. If it
    # does, we simply ensure that this timestamp is in the correct timezone.
    if dt.tzinfo:
        return datetime.fromtimestamp(dt.timestamp(), tz=get_timezone(tz))
    # otherwise, ensure that we assume the pre-transition timezone
    else:
        return create_datetime(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            microsecond=dt.microsecond,
            tz=get_timezone(tz),
            fold=0,
        )
