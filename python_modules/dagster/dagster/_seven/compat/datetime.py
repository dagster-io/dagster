# pyright: reportMissingImports=none
try:
    # zoneinfo is python >= 3.9
    from zoneinfo import ZoneInfo as _timezone_from_string
except:
    from dateutil.tz import gettz as _timezone_from_string
from datetime import timezone, tzinfo

import dagster._check as check


def timezone_from_string(timezone_name: str) -> tzinfo:
    # Allow case insensitivity for "utc" specifically for back-compat with pendulum 2
    # (plus the fact that some systems can process that timezone and others cannot)
    if timezone_name == "utc" or timezone_name == "UTC":
        return timezone.utc

    return check.not_none(_timezone_from_string(timezone_name))
