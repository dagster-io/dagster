import base64
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import dagster._check as check
from dagster._core.assets import AssetDetails
from dagster._core.definitions.events import AssetKey
from dagster._core.event_api import EventHandlerFn, EventLogRecord, EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.execution.stats import (
    RunStepKeyStatsSnapshot,
    build_run_stats_from_events,
    build_run_step_stats_from_events,
)
from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance
from dagster._core.storage.dagster_run import DagsterRunStatsSnapshot
from dagster._core.storage.sql import AlembicVersion
from dagster._seven import json
from dagster._utils import PrintFn
from dagster._utils.concurrency import ConcurrencyClaimStatus, ConcurrencyKeyInfo

if TYPE_CHECKING:
    from dagster._core.events.log import EventLogEntry
    from dagster._core.storage.partition_status_cache import AssetStatusCacheValue


class EventLogConnection(NamedTuple):
    records: Sequence[EventLogRecord]
    cursor: str
    has_more: bool


class EventLogCursorType(Enum):
    OFFSET = "OFFSET"
    STORAGE_ID = "STORAGE_ID"


class EventLogCursor(NamedTuple):
    """Representation of an event record cursor, keeping track of the log query state."""

    cursor_type: EventLogCursorType
    value: int

    def is_offset_cursor(self) -> bool:
        return self.cursor_type == EventLogCursorType.OFFSET

    def is_id_cursor(self) -> bool:
        return self.cursor_type == EventLogCursorType.STORAGE_ID

    def offset(self) -> int:
        check.invariant(self.cursor_type == EventLogCursorType.OFFSET)
        return max(0, int(self.value))

    def storage_id(self) -> int:
        check.invariant(self.cursor_type == EventLogCursorType.STORAGE_ID)
        return int(self.value)

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        raw = json.dumps({"type": self.cursor_type.value, "value": self.value})
        return base64.b64encode(bytes(raw, encoding="utf-8")).decode("utf-8")

    @staticmethod
    def parse(cursor_str: str) -> "EventLogCursor":
        raw = json.loads(base64.b64decode(cursor_str).decode("utf-8"))
        return EventLogCursor(EventLogCursorType(raw["type"]), raw["value"])

    @staticmethod
    def from_offset(offset: int) -> "EventLogCursor":
        return EventLogCursor(EventLogCursorType.OFFSET, offset)

    @staticmethod
    def from_storage_id(storage_id: int) -> "EventLogCursor":
        return EventLogCursor(EventLogCursorType.STORAGE_ID, storage_id)


class AssetEntry(
    NamedTuple(
        "_AssetEntry",
        [
            ("asset_key", AssetKey),
            ("last_materialization_record", Optional[EventLogRecord]),
            ("last_run_id", Optional[str]),
            ("asset_details", Optional[AssetDetails]),
            ("cached_status", Optional["AssetStatusCacheValue"]),
        ],
    )
):
    def __new__(
        cls,
        asset_key: AssetKey,
        last_materialization_record: Optional[EventLogRecord] = None,
        last_run_id: Optional[str] = None,
        asset_details: Optional[AssetDetails] = None,
        cached_status: Optional["AssetStatusCacheValue"] = None,
    ):
        from dagster._core.storage.partition_status_cache import AssetStatusCacheValue

        return super(AssetEntry, cls).__new__(
            cls,
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            last_materialization_record=check.opt_inst_param(
                last_materialization_record, "last_materialization_record", EventLogRecord
            ),
            last_run_id=check.opt_str_param(last_run_id, "last_run_id"),
            asset_details=check.opt_inst_param(asset_details, "asset_details", AssetDetails),
            cached_status=check.opt_inst_param(
                cached_status, "cached_status", AssetStatusCacheValue
            ),
        )

    @property
    def last_materialization(self) -> Optional["EventLogEntry"]:
        if self.last_materialization_record is None:
            return None
        return self.last_materialization_record.event_log_entry

    @property
    def last_materialization_storage_id(self) -> Optional[int]:
        if self.last_materialization_record is None:
            return None
        return self.last_materialization_record.storage_id


class AssetRecord(NamedTuple):
    """Internal representation of an asset record, as stored in a :py:class:`~dagster._core.storage.event_log.EventLogStorage`.

    Users should not invoke this class directly.
    """

    storage_id: int
    asset_entry: AssetEntry


class EventLogStorage(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    """Abstract base class for storing structured event logs from pipeline runs.

    Note that event log storages using SQL databases as backing stores should implement
    :py:class:`~dagster._core.storage.event_log.SqlEventLogStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagster-webserver`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.
    """

    def get_logs_for_run(
        self,
        run_id: str,
        cursor: Optional[Union[str, int]] = None,
        of_type: Optional[Union[DagsterEventType, Set[DagsterEventType]]] = None,
        limit: Optional[int] = None,
        ascending: bool = True,
    ) -> Sequence["EventLogEntry"]:
        """Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[Union[str, int]]): Cursor value to track paginated queries.  Legacy
                support for integer offset cursors.
            of_type (Optional[DagsterEventType]): the dagster event type to filter the logs.
            limit (Optional[int]): Max number of records to return.
        """
        if isinstance(cursor, int):
            cursor = EventLogCursor.from_offset(cursor + 1).to_string()
        records = self.get_records_for_run(
            run_id, cursor, of_type, limit, ascending=ascending
        ).records
        return [record.event_log_entry for record in records]

    @abstractmethod
    def get_records_for_run(
        self,
        run_id: str,
        cursor: Optional[str] = None,
        of_type: Optional[Union[DagsterEventType, Set[DagsterEventType]]] = None,
        limit: Optional[int] = None,
        ascending: bool = True,
    ) -> EventLogConnection:
        """Get all of the event log records corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[str]): Cursor value to track paginated queries.
            of_type (Optional[DagsterEventType]): the dagster event type to filter the logs.
            limit (Optional[int]): Max number of records to return.
        """

    def get_stats_for_run(self, run_id: str) -> DagsterRunStatsSnapshot:
        """Get a summary of events that have ocurred in a run."""
        return build_run_stats_from_events(run_id, self.get_logs_for_run(run_id))

    def get_step_stats_for_run(
        self, run_id: str, step_keys: Optional[Sequence[str]] = None
    ) -> Sequence[RunStepKeyStatsSnapshot]:
        """Get per-step stats for a pipeline run."""
        logs = self.get_logs_for_run(run_id)
        if step_keys:
            logs = [
                event
                for event in logs
                if event.is_dagster_event and event.get_dagster_event().step_key in step_keys
            ]

        return build_run_step_stats_from_events(run_id, logs)

    @abstractmethod
    def store_event(self, event: "EventLogEntry") -> None:
        """Store an event corresponding to a pipeline run.

        Args:
            event (EventLogEntry): The event to store.
        """

    @abstractmethod
    def delete_events(self, run_id: str) -> None:
        """Remove events for a given run id."""

    @abstractmethod
    def upgrade(self) -> None:
        """This method should perform any schema migrations necessary to bring an
        out-of-date instance of the storage up to date.
        """

    @abstractmethod
    def reindex_events(self, print_fn: Optional[PrintFn] = None, force: bool = False) -> None:
        """Call this method to run any data migrations across the event_log tables."""

    @abstractmethod
    def reindex_assets(self, print_fn: Optional[PrintFn] = None, force: bool = False) -> None:
        """Call this method to run any data migrations across the asset tables."""

    @abstractmethod
    def wipe(self) -> None:
        """Clear the log storage."""

    @abstractmethod
    def watch(self, run_id: str, cursor: Optional[str], callback: EventHandlerFn) -> None:
        """Call this method to start watching."""

    @abstractmethod
    def end_watch(self, run_id: str, handler: EventHandlerFn) -> None:
        """Call this method to stop watching."""

    @property
    @abstractmethod
    def is_persistent(self) -> bool:
        """bool: Whether the storage is persistent."""

    def dispose(self) -> None:
        """Explicit lifecycle management."""

    def optimize_for_webserver(self, statement_timeout: int, pool_recycle: int) -> None:
        """Allows for optimizing database connection / use in the context of a long lived webserver process.
        """

    @abstractmethod
    def get_event_records(
        self,
        event_records_filter: EventRecordsFilter,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Sequence[EventLogRecord]:
        pass

    def supports_event_consumer_queries(self) -> bool:
        return False

    def get_logs_for_all_runs_by_log_id(
        self,
        after_cursor: int = -1,
        dagster_event_type: Optional[Union[DagsterEventType, Set[DagsterEventType]]] = None,
        limit: Optional[int] = None,
    ) -> Mapping[int, "EventLogEntry"]:
        """Get event records across all runs. Only supported for non sharded sql storage."""
        raise NotImplementedError()

    def get_maximum_record_id(self) -> Optional[int]:
        """Get the current greatest record id in the event log. Only supported for non sharded sql storage.
        """
        raise NotImplementedError()

    @abstractmethod
    def can_cache_asset_status_data(self) -> bool:
        pass

    @abstractmethod
    def wipe_asset_cached_status(self, asset_key: AssetKey) -> None:
        pass

    @abstractmethod
    def get_asset_records(
        self, asset_keys: Optional[Sequence[AssetKey]] = None
    ) -> Sequence[AssetRecord]:
        pass

    @abstractmethod
    def has_asset_key(self, asset_key: AssetKey) -> bool:
        pass

    @abstractmethod
    def all_asset_keys(self) -> Sequence[AssetKey]:
        pass

    @abstractmethod
    def update_asset_cached_status_data(
        self, asset_key: AssetKey, cache_values: "AssetStatusCacheValue"
    ) -> None:
        pass

    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence[AssetKey]:
        # base implementation of get_asset_keys, using the existing `all_asset_keys` and doing the
        # filtering in-memory
        asset_keys = sorted(self.all_asset_keys(), key=str)
        if prefix:
            asset_keys = [
                asset_key for asset_key in asset_keys if asset_key.path[: len(prefix)] == prefix
            ]
        if cursor:
            cursor_asset = AssetKey.from_db_string(cursor)
            if cursor_asset and cursor_asset in asset_keys:
                idx = asset_keys.index(cursor_asset)
                asset_keys = asset_keys[idx + 1 :]
        if limit:
            asset_keys = asset_keys[:limit]
        return asset_keys

    @abstractmethod
    def get_latest_materialization_events(
        self, asset_keys: Iterable[AssetKey]
    ) -> Mapping[AssetKey, Optional["EventLogEntry"]]:
        pass

    def supports_add_asset_event_tags(self) -> bool:
        return False

    def add_asset_event_tags(
        self,
        event_id: int,
        event_timestamp: float,
        asset_key: AssetKey,
        new_tags: Mapping[str, str],
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_event_tags_for_asset(
        self,
        asset_key: AssetKey,
        filter_tags: Optional[Mapping[str, str]] = None,
        filter_event_id: Optional[int] = None,
    ) -> Sequence[Mapping[str, str]]:
        pass

    @abstractmethod
    def get_asset_run_ids(self, asset_key: AssetKey) -> Sequence[str]:
        pass

    @abstractmethod
    def wipe_asset(self, asset_key: AssetKey) -> None:
        """Remove asset index history from event log for given asset_key."""

    @abstractmethod
    def get_materialization_count_by_partition(
        self, asset_keys: Sequence[AssetKey], after_cursor: Optional[int] = None
    ) -> Mapping[AssetKey, Mapping[str, int]]:
        pass

    @abstractmethod
    def get_latest_storage_id_by_partition(
        self, asset_key: AssetKey, event_type: DagsterEventType
    ) -> Mapping[str, int]:
        pass

    @abstractmethod
    def get_latest_tags_by_partition(
        self,
        asset_key: AssetKey,
        event_type: DagsterEventType,
        tag_keys: Sequence[str],
        asset_partitions: Optional[Sequence[str]] = None,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> Mapping[str, Mapping[str, str]]:
        pass

    @abstractmethod
    def get_latest_asset_partition_materialization_attempts_without_materializations(
        self, asset_key: AssetKey
    ) -> Mapping[str, Tuple[str, int]]:
        pass

    @abstractmethod
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Get the list of partition keys for a dynamic partitions definition."""
        raise NotImplementedError()

    @abstractmethod
    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        """Check if a dynamic partition exists."""
        raise NotImplementedError()

    @abstractmethod
    def add_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> None:
        """Add a partition for the specified dynamic partitions definition."""
        raise NotImplementedError()

    @abstractmethod
    def delete_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> None:
        """Delete a partition for the specified dynamic partitions definition."""
        raise NotImplementedError()

    def alembic_version(self) -> Optional[AlembicVersion]:
        return None

    @property
    def is_run_sharded(self) -> bool:
        """Indicates that the EventLogStoarge is sharded."""
        return False

    @property
    def supports_global_concurrency_limits(self) -> bool:
        """Indicates that the EventLogStorage supports global concurrency limits."""
        return False

    @abstractmethod
    def set_concurrency_slots(self, concurrency_key: str, num: int) -> None:
        """Allocate concurrency slots for the given concurrency key."""
        raise NotImplementedError()

    @abstractmethod
    def get_concurrency_keys(self) -> Set[str]:
        """Get the set of concurrency limited keys."""
        raise NotImplementedError()

    @abstractmethod
    def get_concurrency_info(self, concurrency_key: str) -> ConcurrencyKeyInfo:
        """Get concurrency info for key."""
        raise NotImplementedError()

    @abstractmethod
    def claim_concurrency_slot(
        self, concurrency_key: str, run_id: str, step_key: str, priority: Optional[int] = None
    ) -> ConcurrencyClaimStatus:
        """Claim concurrency slots for step."""
        raise NotImplementedError()

    @abstractmethod
    def check_concurrency_claim(
        self, concurrency_key: str, run_id: str, step_key: str
    ) -> ConcurrencyClaimStatus:
        """Claim concurrency slots for step."""
        raise NotImplementedError()

    @abstractmethod
    def get_concurrency_run_ids(self) -> Set[str]:
        """Get a list of run_ids that are occupying or waiting for a concurrency key slot."""
        raise NotImplementedError()

    @abstractmethod
    def free_concurrency_slots_for_run(self, run_id: str) -> None:
        """Frees concurrency slots for a given run."""
        raise NotImplementedError()

    @abstractmethod
    def free_concurrency_slot_for_step(self, run_id: str, step_key: str) -> None:
        """Frees concurrency slots for a given run/step."""
        raise NotImplementedError()
