from abc import ABC
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union

from dagster_shared.serdes.utils import SerializableTimeDelta

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.loader import LoadableBy, LoadingContext
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import deserialize_value, whitelist_for_serdes
from dagster._time import datetime_from_timestamp, get_timezone
from dagster._utils import check
from dagster._utils.schedules import get_smallest_cron_interval, is_valid_cron_string

if TYPE_CHECKING:
    from dagster._core.events.log import EventLogEntry


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
    """Base class for all freshness policies.
    The "internal" prefix is a temporary measure to distinguish these policies from an existing, deprecated freshness policy model
    which has since been renamed to `LegacyFreshnessPolicy`.
    Expect the name of this class to change to `FreshnessPolicy` in a future release.

    """

    @classmethod
    def from_asset_spec_metadata(
        cls, metadata: Mapping[str, Any]
    ) -> Optional["InternalFreshnessPolicy"]:
        serialized_policy = metadata.get(INTERNAL_FRESHNESS_POLICY_METADATA_KEY)

        # We had a few asset spec metadatas with internal freshness policies set to literal "null" string,
        # need special handling for those cases.
        # https://github.com/dagster-io/dagster/pull/30615
        if serialized_policy is None or serialized_policy.value == "null":
            return None
        return deserialize_value(serialized_policy.value, cls)  # pyright: ignore

    @staticmethod
    def time_window(
        fail_window: timedelta, warn_window: Optional[timedelta] = None
    ) -> "TimeWindowFreshnessPolicy":
        return TimeWindowFreshnessPolicy.from_timedeltas(fail_window, warn_window)

    @staticmethod
    def cron(
        deadline_cron: str, lower_bound_delta: timedelta, timezone: str = "UTC"
    ) -> "CronFreshnessPolicy":
        return CronFreshnessPolicy(
            deadline_cron=deadline_cron, lower_bound_delta=lower_bound_delta, timezone=timezone
        )


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
@record_custom(
    field_to_new_mapping={
        "serializable_lower_bound_delta": "lower_bound_delta",
    }
)
class CronFreshnessPolicy(InternalFreshnessPolicy, IHaveNew):
    """Defines freshness with reference to a predetermined cron schedule.

    Args:
        deadline_cron: a cron string that defines a deadline for the asset to be materialized.
        lower_bound_delta: a timedelta that defines the lower bound for when the asset could have been materialized.
        If a deadline cron tick has passed and the most recent materialization is older than (deadline cron tick timestamp - lower bound delta), the asset is considered stale until it materializes again.
        timezone: optionally provide a timezone for cron evaluation. IANA time zone strings are supported. If not provided, defaults to UTC.

    Example:
    policy = InternalFreshnessPolicy.cron(
        deadline_cron="0 10 * * *", # 10am daily
        lower_bound_delta=timedelta(hours=1),
    )

    This policy expects the asset to materialize every day between 9:00 AM and 10:00 AM.

    If the asset is materialized at 9:30 AM, the asset is fresh, and will continue to be fresh until at least the deadline next day (10AM)
    If the asset is materialized at 9:59 AM, the asset is fresh, and will continue to be fresh until at least the deadline next day (10AM)
    If the asset is not materialized by 10:00 AM, the asset is stale, and will continue to be stale until it is materialized.
    If the asset is then materialized at 10:30AM, it becomes fresh again until at least the deadline the next day (10AM).

    Keep in mind that the policy will always look at the last completed cron tick.
    So in the example above, if asset freshness is evaluated at 9:59 AM, the policy will still consider the previous day's 9-10AM window.
    """

    deadline_cron: str
    serializable_lower_bound_delta: SerializableTimeDelta
    timezone: str

    def __new__(
        cls,
        deadline_cron: str,
        lower_bound_delta: Union[timedelta, SerializableTimeDelta],
        timezone: str = "UTC",
    ):
        check.str_param(deadline_cron, "deadline_cron")
        check.invariant(is_valid_cron_string(deadline_cron), "Invalid cron string.")

        # Handle both construction (with timedelta) and deserialization (with SerializableTimeDelta)
        if isinstance(lower_bound_delta, SerializableTimeDelta):
            # During deserialization, we already have a SerializableTimeDelta
            serializable_lower_bound_delta = lower_bound_delta
            actual_lower_bound_delta = lower_bound_delta.to_timedelta()
        else:
            # During normal construction, we have a timedelta and need to convert it
            actual_lower_bound_delta = lower_bound_delta
            serializable_lower_bound_delta = SerializableTimeDelta.from_timedelta(lower_bound_delta)

        check.invariant(
            actual_lower_bound_delta >= timedelta(minutes=1),
            f"lower_bound_delta must be greater than or equal to 1 minute, was {actual_lower_bound_delta.total_seconds()} seconds",
        )
        smallest_cron_interval = get_smallest_cron_interval(deadline_cron)
        check.invariant(
            actual_lower_bound_delta <= smallest_cron_interval,
            f"lower_bound_delta must be less than or equal to the smallest cron interval of ({smallest_cron_interval.total_seconds()} seconds for deadline_cron {deadline_cron}). Provided lower_bound_delta is {actual_lower_bound_delta.total_seconds()} seconds",
        )

        try:
            get_timezone(timezone)
        # Would be better to catch a specific exception type here,
        # but it's more complicated because we use different timezone libraries
        # depending on the Python version.
        except Exception:
            raise check.CheckError(f"Invalid IANA timezone: {timezone}")
        return super().__new__(
            cls,
            deadline_cron=deadline_cron,
            serializable_lower_bound_delta=serializable_lower_bound_delta,
            timezone=timezone,
        )

    @property
    def lower_bound_delta(self) -> timedelta:
        """Returns the lower bound delta as a timedelta.
        Use this instead of accessing the serializable_lower_bound_delta directly.
        """
        return SerializableTimeDelta.to_timedelta(self.serializable_lower_bound_delta)


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
class FreshnessStateRecord(LoadableBy[AssetKey]):
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

    @staticmethod
    def from_event_log_entry(entry: "EventLogEntry") -> "FreshnessStateRecord":
        dagster_event = check.not_none(entry.dagster_event)
        event_data = check.inst(dagster_event.event_specific_data, FreshnessStateChange)
        return FreshnessStateRecord(
            entity_key=event_data.key,
            freshness_state=event_data.new_state,
            updated_at=datetime_from_timestamp(event_data.state_change_timestamp),
            # note: metadata is not currently stored in the event log
            record_body=FreshnessStateRecordBody(metadata={}),
        )

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[AssetKey], context: LoadingContext
    ) -> Iterable[Optional["FreshnessStateRecord"]]:
        keys = list(keys)
        state_records = context.instance.get_freshness_state_records(keys)
        return [state_records.get(key) for key in keys]
