"""Timezone handling utilities for Snowflake integration."""

import re
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    pass


def convert_to_utc(dt: datetime) -> datetime:
    """Convert timezone-aware datetime to UTC.

    Args:
        dt: Datetime object (timezone-aware or naive)

    Returns:
        UTC datetime object (timezone-aware)

    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> est = timezone(timedelta(hours=-5))
        >>> dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=est)
        >>> convert_to_utc(dt)
        datetime.datetime(2024, 1, 1, 17, 0, tzinfo=datetime.timezone.utc)
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def snowflake_timestamp(dt: datetime) -> datetime:
    """Convert Python datetime to Snowflake TIMESTAMP_NTZ compatible format.

    Snowflake TIMESTAMP_NTZ stores timestamps without timezone information.
    This function converts a timezone-aware datetime to UTC and removes timezone info.

    Args:
        dt: Datetime object (timezone-aware or naive)

    Returns:
        Naive datetime in UTC (compatible with TIMESTAMP_NTZ)

    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> est = timezone(timedelta(hours=-5))
        >>> dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=est)
        >>> snowflake_timestamp(dt)
        datetime.datetime(2024, 1, 1, 17, 0)
    """
    utc_dt = convert_to_utc(dt)
    return utc_dt.replace(tzinfo=None)


def handle_pandas_timestamps(series: "pd.Series") -> "pd.Series":
    """Fix Pandas timestamp timezone issues for Snowflake compatibility.

    Pandas timestamps can have timezone information that causes issues with
    Snowflake's Python connector. This function converts to UTC and removes
    timezone info.

    Args:
        series: Pandas Series with datetime/timestamp data

    Returns:
        Series with timezone-naive UTC timestamps

    Examples:
        >>> import pandas as pd
        >>> ts = pd.Timestamp('2024-01-01 12:00:00-0500')
        >>> series = pd.Series([ts])
        >>> handle_pandas_timestamps(series)
        0   2024-01-01 17:00:00
        dtype: datetime64[ns]
    """
    if series.dtype.name.startswith("datetime64"):
        # Convert to UTC if timezone-aware
        # pandas Series with datetime dtype has .dt accessor
        dt_accessor = series.dt
        if dt_accessor.tz is not None:
            series = dt_accessor.tz_convert(timezone.utc)
            series = dt_accessor.tz_localize(None)
        return series
    return series


def parse_relative_time_with_tz(
    time_str: str, base_time: datetime | None = None
) -> datetime:
    """Parse relative time strings with timezone awareness.

    Enhanced version of parse_relative_time that handles timezone-aware parsing.
    Converts result to UTC for Snowflake compatibility.

    Args:
        time_str: Relative time string (e.g., "4 hours ago", "2 days ago")
        base_time: Base time to calculate from (defaults to now in UTC)

    Returns:
        UTC datetime object (timezone-aware)

    Raises:
        ValueError: If time_str cannot be parsed

    Examples:
        >>> parse_relative_time_with_tz("2 hours ago")
        datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
    """
    if not time_str or not isinstance(time_str, str):
        raise ValueError("time_str must be a non-empty string")

    if base_time is None:
        base_time = datetime.now(timezone.utc)
    elif base_time.tzinfo is None:
        base_time = base_time.replace(tzinfo=timezone.utc)

    time_str = time_str.lower().strip()

    patterns = [
        (r"(\d+)\s*minute", lambda m: base_time - timedelta(minutes=int(m.group(1)))),
        (r"(\d+)\s*hour", lambda m: base_time - timedelta(hours=int(m.group(1)))),
        (r"(\d+)\s*day", lambda m: base_time - timedelta(days=int(m.group(1)))),
        (r"(\d+)\s*week", lambda m: base_time - timedelta(weeks=int(m.group(1)))),
        (r"(\d+)\s*month", lambda m: base_time - timedelta(days=int(m.group(1)) * 30)),
    ]

    for pattern, func in patterns:
        match = re.search(pattern, time_str)
        if match:
            result = func(match)
            # Ensure result is timezone-aware
            if result.tzinfo is None:
                result = result.replace(tzinfo=timezone.utc)
            return result

    # Default to base_time if no pattern matches
    return base_time
