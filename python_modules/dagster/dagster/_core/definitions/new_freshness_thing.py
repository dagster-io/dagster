from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from dagster import _check as check
from dagster._record import IHaveNew, record_custom
from dagster._serdes import whitelist_for_serdes


class FreshnessPolicyType(Enum):
    TIME_WINDOW = "time_window"
    CRON = "cron"


class NewFreshnessThing(ABC):
    """A condition that delineates when an asset is considered fresh. The asset can either pass, violate, or warn on this condition.

    `NewFreshnessThing` can be specified as a parameter to `@asset`, `@multi_asset`, or in `AssetSpec`.

    Do not use this class directly. Instead, use one of the subclasses.

    A proper name for this concept is under discussion here:
        https://dagsterlabs.slack.com/archives/C047L6H0LF4/p1743087033186109.

    """

    @property
    @abstractmethod
    def policy_type(self) -> FreshnessPolicyType: ...


@whitelist_for_serdes
@record_custom
class TimeWindowFreshnessThing(NewFreshnessThing, IHaveNew):
    """A freshness condition that considers an asset fresh if it was materialized within a specified time window (time_window_minutes).

    The asset is considered stale if its last materialization is older than time_window_minutes, and in a warning state
    if its last materialization is older than the warning time window but newer than the critical time window.

    Example usage:

    .. code-block:: python

        from dagster import TimeWindowFreshnessThing

        # Asset must be materialized within last 24 hours (1440 minutes)
        @asset(new_freshness_thing=TimeWindowFreshnessThing(time_window_minutes=1440))
        def my_asset():
            ...

        # Asset must be materialized within last 24 hours (1440 minutes), with warning after 12 hours
        @asset(new_freshness_thing=TimeWindowFreshnessThing(time_window_minutes=1440, warning_time_window_minutes=720))
        def my_asset():
            ...

    Args:
        time_window_minutes (int): The maximum age in minutes for an asset to be considered fresh.
            Must be positive.
        warning_time_window_minutes (Optional[int]): If provided, the age in minutes at which to start
            showing warnings about asset freshness. Must be positive and less than time_window_minutes.
    """

    time_window_minutes: int
    warning_time_window_minutes: Optional[int] = None

    @property
    def policy_type(self) -> FreshnessPolicyType:
        return FreshnessPolicyType.TIME_WINDOW

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
