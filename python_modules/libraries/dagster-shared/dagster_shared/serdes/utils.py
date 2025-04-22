import datetime
import hashlib
from typing import NamedTuple, Optional

from dagster_shared.serdes.serdes import (
    PackableValue,
    WhitelistMap,
    serialize_value,
    whitelist_for_serdes,
)


def create_snapshot_id(
    snapshot: PackableValue, whitelist_map: Optional[WhitelistMap] = None
) -> str:
    kwargs = dict(whitelist_map=whitelist_map) if whitelist_map else {}
    json_rep = serialize_value(snapshot, **kwargs)
    return hash_str(json_rep)


def hash_str(in_str: str) -> str:
    # so that hexdigest is 40, not 64 bytes
    return hashlib.sha1(in_str.encode("utf-8")).hexdigest()


def serialize_pp(value: PackableValue) -> str:
    """Serialize and pretty print."""
    return serialize_value(value, indent=2, separators=(",", ": "))


@whitelist_for_serdes
class SerializableTimeDelta(NamedTuple):
    """A Dagster-serializable version of a datetime.timedelta. The datetime.timedelta class
    internally stores values as an integer number of days, seconds, and microseconds. This class
    handles converting between the in-memory and serializable formats.

    Do not use the `days`, `seconds` or `microseconds` attributes to get the duration of the timedelta.
    Instead, use `total_seconds()` or convert to a `datetime.timedelta` using `to_timedelta()`.
    """

    days: int
    seconds: int
    microseconds: int

    @staticmethod
    def from_timedelta(timedelta: datetime.timedelta) -> "SerializableTimeDelta":
        return SerializableTimeDelta(
            days=timedelta.days, seconds=timedelta.seconds, microseconds=timedelta.microseconds
        )

    def to_timedelta(self) -> datetime.timedelta:
        return datetime.timedelta(
            days=self.days, seconds=self.seconds, microseconds=self.microseconds
        )

    def total_seconds(self) -> float:
        """Returns the total number of seconds in the timedelta.
        Use this to get the total duration of the timedelta, instead of `SerializableTimeDelta.seconds`.
        `SerializableTimeDelta.seconds` is set to 0 for any timedelta greater than or equal to 24 hours.
        """
        return self.to_timedelta().total_seconds()
