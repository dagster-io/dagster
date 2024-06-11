from typing import NamedTuple

from dagster._serdes import whitelist_for_serdes


# TimestampWithTimezone is used to preserve IANA timezone information when serializing.
# Serializing with the UTC offset (i.e. via datetime.isoformat) is insufficient because offsets vary
# depending on daylight savings time. This causes timedelta operations to be inexact, since the
# exact timezone is not preserved. To prevent any lossy serialization, ths implementation
# serializes both the datetime float and the IANA timezone.
@whitelist_for_serdes
class TimestampWithTimezone(NamedTuple):
    timestamp: float  # Seconds since the Unix epoch
    timezone: str
