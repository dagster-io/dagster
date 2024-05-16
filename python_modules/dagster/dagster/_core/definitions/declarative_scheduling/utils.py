import datetime
from typing import TYPE_CHECKING, NamedTuple

from dagster._serdes.serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
    from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
        SchedulingCondition,
    )


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


def as_amp(scheduling_condition: "SchedulingCondition") -> "AutoMaterializePolicy":
    return scheduling_condition.as_auto_materialize_policy()
