from abc import ABC
from collections.abc import Mapping
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from dagster_shared.serdes.utils import SerializableTimeDelta

from dagster._core.definitions.asset_key import AssetKey
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import deserialize_value, whitelist_for_serdes
from dagster._utils import check
from dagster._utils.schedules import is_valid_cron_string


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

    @staticmethod
    def cron(
        deadline_cron: str, lookback_window: timedelta, timezone: str = "UTC"
    ) -> "CronFreshnessPolicy":
        return CronFreshnessPolicy(deadline_cron, lookback_window, timezone)


@whitelist_for_serdes
@record
class TimeWindowFreshnessPolicy(InternalFreshnessPolicy, IHaveNew):
    fail_window: SerializableTimeDelta
    warn_window: Optional[SerializableTimeDelta] = None

    @classmethod
    def from_timedeltas(cls, fail_window: timedelta, warn_window: Optional[timedelta] = None):
        check.invariant(
            fail_window.total_seconds() >= 60,
            "Due to Dagster system constraints, fail_window cannot be less than 1 minute",
        )
        if warn_window:
            check.invariant(
                warn_window.total_seconds() >= 60,
                "Due to Dagster system constraints, warn_window cannot be less than 1 minute",
            )
            check.invariant(warn_window < fail_window, "warn_window must be less than fail_window")

        return cls(
            fail_window=SerializableTimeDelta.from_timedelta(fail_window),
            warn_window=SerializableTimeDelta.from_timedelta(warn_window) if warn_window else None,
        )


@whitelist_for_serdes
@record_custom
class CronFreshnessPolicy(InternalFreshnessPolicy, IHaveNew):
    """Defines a cron schedule on which the asset is expected to materialize.

    Args:
        deadline_cron: a cron string that defines a deadline for the asset to be materialized.
            Seconds resolution in the cron string is not supported.
            Ex: "0 10 * * *" means we expect the asset to be materialized by 10:00 AM every day
        lookback_window: the asset must be materialized within this time window before the deadline.
        timezone: the timezone to use for the cron schedule. IANA time zone database strings are supported. Defaults to UTC.

    Example:
    policy = InternalFreshnessPolicy.cron(
        deadline_cron="0 10 * * *", # 10am daily
        lookback_window=timedelta(hours=1),
    )

    This policy expects the asset to materialize every day between 9:00 AM and 10:00 AM.
    The asset is stale if it materializes outside of this time window.

    Until 9:00 AM, the asset's freshness state will not change.

    If the asset is materialized at 9:30 AM, the asset is fresh
    If the asset is materialized at 9:59 AM, the asset is fresh
    If the asset is not materialized by 10:00 AM, the asset is stale (freshness state is FAIL)
    If the asset is materialized at 10:01AM, the asset is still stale.

    """

    deadline_cron: str
    lookback_window: SerializableTimeDelta
    timezone: str

    def __new__(cls, deadline_cron: str, lookback_window: timedelta, timezone: str = "UTC"):
        check.str_param(deadline_cron, "deadline_cron")
        check.invariant(is_valid_cron_string(deadline_cron), "Invalid cron string.")

        # TODO validate lookback window fits within the cron
        # This will require a method to find the minimum cycle length of the cron schedule

        return super().__new__(
            cls,
            deadline_cron=deadline_cron,
            lookback_window=SerializableTimeDelta.from_timedelta(lookback_window),
            timezone=timezone,
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
