import datetime
from abc import ABC
from collections.abc import Mapping
from enum import Enum
from typing import Any, Optional

from dagster_shared.serdes.utils import SerializableTimeDelta

from dagster._core.definitions.asset_key import AssetKey
from dagster._record import IHaveNew, record
from dagster._serdes import deserialize_value, whitelist_for_serdes
from dagster._utils import check


@whitelist_for_serdes
class FreshnessState(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@whitelist_for_serdes
@record
class FreshnessStateEvaluation:
    key: AssetKey
    freshness_state: FreshnessState


INTERNAL_FRESHNESS_POLICY_METADATA_KEY = "dagster/internal_freshness_policy"


class InternalFreshnessPolicy(ABC):
    @classmethod
    def from_asset_spec_metadata(
        cls, metadata: Mapping[str, Any]
    ) -> Optional["InternalFreshnessPolicy"]:
        serialized_policy = metadata.get(INTERNAL_FRESHNESS_POLICY_METADATA_KEY)
        if serialized_policy is None:
            return None
        return deserialize_value(serialized_policy.value, cls)  # pyright: ignore

    @staticmethod
    def time_window(
        fail_window: datetime.timedelta, warn_window: Optional[datetime.timedelta] = None
    ) -> "TimeWindowFreshnessPolicy":
        return TimeWindowFreshnessPolicy.from_timedeltas(fail_window, warn_window)


@whitelist_for_serdes
@record
class TimeWindowFreshnessPolicy(InternalFreshnessPolicy, IHaveNew):
    fail_window: SerializableTimeDelta
    warn_window: Optional[SerializableTimeDelta] = None

    @classmethod
    def from_timedeltas(
        cls, fail_window: datetime.timedelta, warn_window: Optional[datetime.timedelta] = None
    ):
        if warn_window:
            check.invariant(warn_window < fail_window, "warn_window must be less than fail_window")

        return cls(
            fail_window=SerializableTimeDelta.from_timedelta(fail_window),
            warn_window=SerializableTimeDelta.from_timedelta(warn_window) if warn_window else None,
        )
