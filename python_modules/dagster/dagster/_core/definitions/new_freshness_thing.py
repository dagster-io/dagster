from abc import ABC
from typing import Optional

from dagster import _check as check
from dagster._record import IHaveNew, record_custom
from dagster._serdes import whitelist_for_serdes


class NewFreshnessThing(ABC):
    """A thing that describes how to check the freshness of an asset."""


@whitelist_for_serdes
@record_custom
class TimeWindowFreshnessThing(NewFreshnessThing, IHaveNew):
    """Consider an asset fresh if the last successful materialization was within a time window of max_lag_minutes."""

    time_window_minutes: int
    warning_time_window_minutes: Optional[int] = None

    def __new__(cls, time_window_minutes: int, warning_time_window_minutes: Optional[int] = None):
        time_window_minutes = check.int_param(time_window_minutes, "time_window_minutes")
        check.invariant(
            time_window_minutes > 0, f"time_window_minutes ({time_window_minutes}) must be positive"
        )

        if warning_time_window_minutes is not None:
            warning_time_window_minutes = check.int_param(
                warning_time_window_minutes, "warning_time_window_minutes"
            )
            check.invariant(
                warning_time_window_minutes > 0,
                f"warning_time_window_minutes ({warning_time_window_minutes}) must be positive",
            )
            check.invariant(
                warning_time_window_minutes < time_window_minutes,
                f"warning_time_window_minutes ({warning_time_window_minutes}) must be less than time_window_minutes ({time_window_minutes})",
            )

        return super().__new__(
            cls,
            time_window_minutes=time_window_minutes,
            warning_time_window_minutes=warning_time_window_minutes,
        )


# TODO this will become a type union once we add more freshness things
# TODO would prefer this to be an abstract base class, but can't figure out how to make it work with serdes and record

# from typing import Union

# NewFreshnessThing = Union[TimeWindowFreshnessThing]
