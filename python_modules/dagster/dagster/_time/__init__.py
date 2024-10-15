import time
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Union

import dagster._check as check
from dagster._vendored.dateutil import parser

try:
    # zoneinfo is python >= 3.9
    from zoneinfo import ZoneInfo as _timezone_from_string  # type: ignore
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

    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt
