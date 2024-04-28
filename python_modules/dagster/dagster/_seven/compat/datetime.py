# pyright: reportMissingImports=none
try:
    # zoneinfo is python >= 3.9
    from zoneinfo import ZoneInfo as _timezone_from_string
except:
    from dateutil.tz import gettz as _timezone_from_string
from datetime import datetime, tzinfo
from typing import Optional


def timezone_from_string(timezone_name: str) -> Optional[tzinfo]:
    return _timezone_from_string(timezone_name)


def timezone_to_string(datetime: datetime) -> Optional[str]:
    """There's no consistent way to get an IANA timezone (America/Los_Angeles vs PST) from
    a tzinfo object. `dt.tzname` returns abbreviations that are inspecific (PST vs PDT). This
    method attempts to pull the IANA timezone off of either a pendulum tzinfo or a ZoneInfo.
    """
    if getattr(datetime, "timezone", None):
        # pendulum 1,2,3 provides the timezone attribute
        return datetime.timezone.name  # type: ignore
    elif getattr(datetime.tzinfo, "key", None):
        # dateutil / zoneinfo provides the key attribute
        return datetime.tzinfo.key  # type: ignore
    # you might be tempted by datetime.tzname() but that's the abbreviation and no good here.
    return None
