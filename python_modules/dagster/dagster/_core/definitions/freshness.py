from abc import ABC
from collections.abc import Mapping
from datetime import datetime, timedelta
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
    NOT_APPLICABLE = "NOT_APPLICABLE"


@whitelist_for_serdes
@record
class FreshnessStateEvaluation:
    key: AssetKey
    freshness_state: FreshnessState


@whitelist_for_serdes
@record
class FreshnessStateChange:
    """Event that is emitted when the freshness state of an asset changes."""

    key: AssetKey
    new_state: FreshnessState
    previous_state: FreshnessState
    state_change_timestamp: float


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
        fail_window: timedelta, warn_window: Optional[timedelta] = None
    ) -> "TimeWindowFreshnessPolicy":
        return TimeWindowFreshnessPolicy.from_timedeltas(fail_window, warn_window)


@whitelist_for_serdes
@record
class TimeWindowFreshnessPolicy(InternalFreshnessPolicy, IHaveNew):
    fail_window: SerializableTimeDelta
    warn_window: Optional[SerializableTimeDelta] = None

    @classmethod
    def from_timedeltas(cls, fail_window: timedelta, warn_window: Optional[timedelta] = None):
        if warn_window:
            check.invariant(warn_window < fail_window, "warn_window must be less than fail_window")

        return cls(
            fail_window=SerializableTimeDelta.from_timedelta(fail_window),
            warn_window=SerializableTimeDelta.from_timedelta(warn_window) if warn_window else None,
        )


@whitelist_for_serdes
@record
class FreshnessStateRecordBody:
    """Store serialized metadata about the freshness state for an entity.

    Left blank for now, a few examples of what we might want to store here:
    - Source timestamp for external assets / freshness checks
    - Snapshot of the freshness policy at the time of record creation
    """

    metadata: Optional[dict[str, Any]]


@record
class FreshnessStateRecord:
    entity_key: AssetKey
    freshness_state: FreshnessState
    updated_at: datetime
    record_body: FreshnessStateRecordBody

    @staticmethod
    def from_db_row(db_row):
        return FreshnessStateRecord(
            entity_key=check.not_none(AssetKey.from_db_string(db_row[0])),
            freshness_state=FreshnessState(db_row[3]),
            record_body=deserialize_value(db_row[4], FreshnessStateRecordBody),
            updated_at=db_row[5],
        )
