# pyright: reportMissingImports=none
try:
    # zoneinfo is python >= 3.9
    from zoneinfo import ZoneInfo as _timezone_from_string
except:
    from dateutil.tz import gettz as _timezone_from_string
import datetime
from contextlib import contextmanager
from typing import Optional

import freezegun


def timezone_from_string(timezone_name: str) -> Optional[datetime.tzinfo]:
    # Allow case insensitivity for "utc" specifically for back-compat with pendulum 2
    # (plus the fact that some systems can process that timezone and others cannot)
    if timezone_name == "utc":
        timezone_name = "UTC"
    return _timezone_from_string(timezone_name)


class SafeFakeDateTime(freezegun.api.FakeDatetime):
    """Like freezegun's fake datetime class, but without inexplicably overriding
    datetime.fromtimestamp to return an instance of the fake class, which messes up
    the logic in cron_string_iterator.
    """

    @classmethod
    def fromtimestamp(cls, t: float, tz: Optional[datetime.tzinfo] = None):
        return freezegun.api.real_datetime.fromtimestamp(t, tz)


@contextmanager
def safe_freeze_time(*args, **kwargs):
    """Like freezegun.freeze_time, but overrides datetime.datetime to SafeFakeDateTime instead."""
    with freezegun.freeze_time(*args, **kwargs) as return_value:
        datetime.datetime = SafeFakeDateTime
        yield return_value
