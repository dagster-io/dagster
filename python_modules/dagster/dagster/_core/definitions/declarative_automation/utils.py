import datetime
from typing import NamedTuple

from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
class SerializableTimeDelta(NamedTuple):
    """A Dagster-serializable version of a datetime.timedelta. The datetime.timedelta class
    internally stores values as an integer number of days, seconds, and microseconds. This class
    handles converting between the in-memory and serializable formats.
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
