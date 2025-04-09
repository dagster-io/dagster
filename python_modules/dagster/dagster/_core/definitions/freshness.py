from abc import ABC, abstractmethod
from enum import Enum
from typing import NamedTuple, Optional

from dagster._annotations import beta
from dagster._core.definitions.asset_key import AssetKey
from dagster._record import IHaveNew, record_custom
from dagster._serdes import whitelist_for_serdes
from dagster._utils import check


@beta
@whitelist_for_serdes
class FreshnessState(str, Enum):
    PASSING = "PASSING"
    IN_VIOLATION = "IN_VIOLATION"
    NEAR_VIOLATION = "NEAR_VIOLATION"
    UNKNOWN = "UNKNOWN"


@beta
@whitelist_for_serdes
class FreshnessStateEvaluation(
    NamedTuple(
        "_FreshnessStateEvaluation",
        [
            ("asset_key", AssetKey),
            ("freshness_state", FreshnessState),
        ],
    )
):
    def __new__(cls, asset_key: AssetKey, freshness_state: FreshnessState):
        return super().__new__(cls, asset_key=asset_key, freshness_state=freshness_state)


INTERNAL_FRESHNESS_POLICY_METADATA_KEY = "dagster/internal_freshness_policy"


class FreshnessPolicyType(Enum):
    TIME_WINDOW = "time_window"


class InternalFreshnessPolicy(ABC):
    @property
    @abstractmethod
    def policy_type(self) -> FreshnessPolicyType: ...


@whitelist_for_serdes
@record_custom
class TimeWindowFreshnessPolicy(InternalFreshnessPolicy, IHaveNew):
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
