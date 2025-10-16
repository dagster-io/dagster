import os
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, AbstractSet, NamedTuple, Optional, Union  # noqa: UP035

import dagster._check as check
from dagster._annotations import public
from dagster._core.assets import AssetDetails
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.data_version import DATA_VERSION_TAG
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness import FreshnessStateRecord
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.event_api import (
    AssetRecordsFilter,
    EventHandlerFn,
    EventLogCursor,
    EventLogRecord,
    EventRecordsFilter,
    EventRecordsResult,
    RunStatusChangeRecordsFilter,
)
from dagster._core.events import DagsterEventType
from dagster._core.execution.stats import (
    RUN_STATS_EVENT_TYPES,
    STEP_STATS_EVENT_TYPES,
    RunStepKeyStatsSnapshot,
    build_run_stats_from_events,
    build_run_step_stats_from_events,
)
from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance
from dagster._core.instance.config import PoolConfig
from dagster._core.loader import LoadableBy, LoadingContext
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
)
from dagster._core.storage.dagster_run import DagsterRunStatsSnapshot
from dagster._core.storage.partition_status_cache import get_and_update_asset_status_cache_value
from dagster._core.storage.sql import AlembicVersion
from dagster._core.storage.tags import MULTIDIMENSIONAL_PARTITION_PREFIX
from dagster._core.types.pagination import PaginatedResults
from dagster._record import record
from dagster._utils import PrintFn
from dagster._utils.concurrency import ConcurrencyClaimStatus, ConcurrencyKeyInfo
from dagster._utils.tags import get_boolean_tag_value
from dagster._utils.warnings import deprecation_warning

if TYPE_CHECKING:
    from dagster._core.events.log import EventLogEntry
    from dagster._core.storage.partition_status_cache import AssetStatusCacheValue


class EventLogConnection(NamedTuple):
    records: Sequence[EventLogRecord]
    cursor: str
    has_more: bool


class AssetEntry(
    NamedTuple(
        "_AssetEntry",
        [
            ("asset_key", AssetKey),
            ("last_materialization_record", Optional[EventLogRecord]),
            ("last_run_id", Optional[str]),
            ("asset_details", Optional[AssetDetails]),
            ("cached_status", Optional["AssetStatusCacheValue"]),
            # Below are optional fields which can be used for more performant
            # queries if the underlying storage supports it
            ("last_observation_record", Optional[EventLogRecord]),
            ("last_planned_materialization_storage_id", Optional[int]),
            ("last_planned_materialization_run_id", Optional[str]),
            ("last_failed_to_materialize_record", Optional[EventLogRecord]),
            ("is_writing_failures", bool),
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
        last_observation_record: Optional[EventLogRecord] = None,
        last_planned_materialization_storage_id: Optional[int] = None,
        last_planned_materialization_run_id: Optional[str] = None,
        last_failed_to_materialize_record: Optional[EventLogRecord] = None,
        is_writing_failures: bool = False,
    ):
        from dagster._core.storage.partition_status_cache import AssetStatusCacheValue

        return super().__new__(
            cls,
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            last_materialization_record=check.opt_inst_param(
                last_materialization_record,
                "last_materialization_record",
                EventLogRecord,
            ),
            last_run_id=check.opt_str_param(last_run_id, "last_run_id"),
            asset_details=check.opt_inst_param(asset_details, "asset_details", AssetDetails),
            cached_status=check.opt_inst_param(
                cached_status, "cached_status", AssetStatusCacheValue
            ),
            last_observation_record=check.opt_inst_param(
                last_observation_record, "last_observation_record", EventLogRecord
            ),
            last_planned_materialization_storage_id=check.opt_int_param(
                last_planned_materialization_storage_id,
                "last_planned_materialization_storage_id",
            ),
            last_planned_materialization_run_id=check.opt_str_param(
                last_planned_materialization_run_id,
                "last_planned_materialization_run_id",
            ),
            last_failed_to_materialize_record=check.opt_inst_param(
                last_failed_to_materialize_record,
                "last_failed_to_materialize_record",
                EventLogRecord,
            ),
            is_writing_failures=check.bool_param(is_writing_failures, "is_writing_failures"),
        )

    @property
    def last_materialization(self) -> Optional["EventLogEntry"]:
        if self.last_materialization_record is None:
            return None
        return self.last_materialization_record.event_log_entry

    @property
    def last_observation(self) -> Optional["EventLogEntry"]:
        if self.last_observation_record is None:
            return None
        return self.last_observation_record.event_log_entry

    @property
    def last_observation_storage_id(self) -> Optional[int]:
        if self.last_observation_record is None:
            return None
        return self.last_observation_record.storage_id

    @property
    def last_materialization_storage_id(self) -> Optional[int]:
        if self.last_materialization_record is None:
            return None
        return self.last_materialization_record.storage_id

    @property
    def last_failed_to_materialize_entry(self) -> Optional["EventLogEntry"]:
        if self.last_failed_to_materialize_record is None:
            return None
        return self.last_failed_to_materialize_record.event_log_entry

    @property
    def last_failed_to_materialize_storage_id(self) -> Optional[int]:
        if self.last_failed_to_materialize_record is None:
            return None
        return self.last_failed_to_materialize_record.storage_id

    @property
    def last_event_storage_id(self) -> Optional[int]:
        """Get the storage id of the latest event for this asset."""
        event_ids = [
            self.last_materialization_storage_id,
            self.last_observation_storage_id,
            self.last_failed_to_materialize_storage_id,
            self.last_planned_materialization_storage_id,
        ]
        event_ids = [event_id for event_id in event_ids if event_id is not None]
        return max(event_ids) if event_ids else None


@public
class AssetRecord(
    NamedTuple("_NamedTuple", [("storage_id", int), ("asset_entry", AssetEntry)]),
    LoadableBy[AssetKey],
):
    """Internal representation of an asset record, as stored in a :py:class:`~dagster._core.storage.event_log.EventLogStorage`.

    Users should not invoke this class directly.
    """

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[AssetKey], context: LoadingContext
    ) -> Iterable[Optional["AssetRecord"]]:
        records_by_key = {
            record.asset_entry.asset_key: record
            for record in context.instance.get_asset_records(list(keys))
        }
        return [records_by_key.get(key) for key in keys]


class AssetCheckSummaryRecord(
    NamedTuple(
        "_AssetCheckSummaryRecord",
        [
            ("asset_check_key", AssetCheckKey),
            ("last_check_execution_record", Optional[AssetCheckExecutionRecord]),
            ("last_run_id", Optional[str]),
            ("last_completed_check_execution_record", Optional[AssetCheckExecutionRecord]),
        ],
    ),
    LoadableBy[AssetCheckKey],
):
    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[AssetCheckKey], context: LoadingContext
    ) -> Iterable[Optional["AssetCheckSummaryRecord"]]:
        records_by_key = context.instance.event_log_storage.get_asset_check_summary_records(
            list(keys)
        )
        return [records_by_key[key] for key in keys]

    @property
    def last_completed_run_id(self) -> Optional[str]:
        return (
            self.last_completed_check_execution_record.run_id
            if self.last_completed_check_execution_record
            else None
        )


class PlannedMaterializationInfo(NamedTuple):
    """Internal representation of an planned materialization event, containing storage_id / run_id.

    Users should not invoke this class directly.
    """

    storage_id: int
    run_id: str


@record
class PoolLimit:
    name: str
    limit: int
    from_default: bool


@public
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
        of_type: Optional[Union[DagsterEventType, set[DagsterEventType]]] = None,
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
            deprecation_warning(
                "Integer cursor values in `get_logs_for_run`",
                "1.8.0",
                "You can instead construct a storage_id-based string cursor e.g. `cursor = EventLogCursor.from_storage_id(storage_id).to_string()`",
            )
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
        of_type: Optional[Union[DagsterEventType, set[DagsterEventType]]] = None,
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
        return build_run_stats_from_events(
            run_id, self.get_logs_for_run(run_id, of_type=RUN_STATS_EVENT_TYPES)
        )

    def get_step_stats_for_run(
        self, run_id: str, step_keys: Optional[Sequence[str]] = None
    ) -> Sequence[RunStepKeyStatsSnapshot]:
        """Get per-step stats for a pipeline run."""
        logs = self.get_logs_for_run(run_id, of_type=STEP_STATS_EVENT_TYPES)
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

    def store_event_batch(self, events: Sequence["EventLogEntry"]) -> None:
        for event in events:
            self.store_event(event)

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

    def optimize_for_webserver(
        self, statement_timeout: int, pool_recycle: int, max_overflow: int
    ) -> None:
        """Allows for optimizing database connection / use in the context of a long lived webserver process."""

    @abstractmethod
    def get_event_records(
        self,
        event_records_filter: EventRecordsFilter,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Sequence[EventLogRecord]:
        pass

    def get_logs_for_all_runs_by_log_id(
        self,
        after_cursor: int = -1,
        dagster_event_type: Optional[Union[DagsterEventType, set[DagsterEventType]]] = None,
        limit: Optional[int] = None,
    ) -> Mapping[int, "EventLogEntry"]:
        """Get event records across all runs. Only supported for non sharded sql storage."""
        raise NotImplementedError()

    def get_maximum_record_id(self) -> Optional[int]:
        """Get the current greatest record id in the event log. Only supported for non sharded sql storage."""
        raise NotImplementedError()

    @abstractmethod
    def can_read_asset_status_cache(self) -> bool:
        """Whether the storage can access cached status information for each asset."""
        pass

    @abstractmethod
    def can_write_asset_status_cache(self) -> bool:
        """Whether the storage is able to write to that cache."""

    @abstractmethod
    def wipe_asset_cached_status(self, asset_key: AssetKey) -> None:
        pass

    @abstractmethod
    def get_asset_records(
        self, asset_keys: Optional[Sequence[AssetKey]] = None
    ) -> Sequence[AssetRecord]:
        pass

    @abstractmethod
    def get_freshness_state_records(
        self, keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, FreshnessStateRecord]:
        pass

    @abstractmethod
    def get_asset_check_summary_records(
        self, asset_check_keys: Sequence[AssetCheckKey]
    ) -> Mapping[AssetCheckKey, AssetCheckSummaryRecord]:
        pass

    @property
    def asset_records_have_last_planned_and_failed_materializations(self) -> bool:
        return False

    @property
    def can_store_asset_failure_events(self) -> bool:
        return False

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
        asset_keys = sorted(self.all_asset_keys(), key=lambda k: k.to_string())
        if prefix:
            asset_keys = [
                asset_key for asset_key in asset_keys if asset_key.path[: len(prefix)] == prefix
            ]
        if cursor:
            cursor_asset = AssetKey.from_db_string(cursor)

            if not cursor_asset:
                raise Exception(f"Invalid cursor string {cursor}")

            cursor_asset_str = cursor_asset.to_string()

            idx = len(asset_keys)
            for i in range(len(asset_keys)):
                if asset_keys[i].to_string() > cursor_asset_str:
                    idx = i
                    break

            asset_keys = asset_keys[idx:]

        if limit:
            asset_keys = asset_keys[:limit]
        return asset_keys

    @abstractmethod
    def get_latest_materialization_events(
        self, asset_keys: Iterable[AssetKey]
    ) -> Mapping[AssetKey, Optional["EventLogEntry"]]:
        pass

    @abstractmethod
    def get_event_tags_for_asset(
        self,
        asset_key: AssetKey,
        filter_tags: Optional[Mapping[str, str]] = None,
        filter_event_id: Optional[int] = None,
    ) -> Sequence[Mapping[str, str]]:
        pass

    def get_asset_tags_to_index(self, tag_keys: set[str]) -> set[str]:
        # make sure we update the list of tested tags in test_asset_tags_to_insert to match
        return {
            key
            for key in tag_keys
            if key == DATA_VERSION_TAG or key.startswith(MULTIDIMENSIONAL_PARTITION_PREFIX)
        }

    @abstractmethod
    def wipe_asset(self, asset_key: AssetKey) -> None:
        """Remove asset index history from event log for given asset_key."""

    @abstractmethod
    def wipe_asset_partitions(self, asset_key: AssetKey, partition_keys: Sequence[str]) -> None:
        """Remove asset index history from event log for given asset partitions."""

    @abstractmethod
    def get_materialized_partitions(
        self,
        asset_key: AssetKey,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> set[str]:
        pass

    @abstractmethod
    def get_latest_storage_id_by_partition(
        self,
        asset_key: AssetKey,
        event_type: DagsterEventType,
        partitions: Optional[set[str]] = None,
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
        self, asset_key: AssetKey, after_storage_id: Optional[int] = None
    ) -> Mapping[str, tuple[str, int]]:
        pass

    @abstractmethod
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Get the list of partition keys for a dynamic partitions definition."""
        raise NotImplementedError()

    @abstractmethod
    def get_paginated_dynamic_partitions(
        self, partitions_def_name: str, limit: int, ascending: bool, cursor: Optional[str] = None
    ) -> PaginatedResults[str]:
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

    @property
    def supports_partition_subset_in_asset_materialization_planned_events(self) -> bool:
        # Setting this environment variable will cause a single planned event to be emitted for
        # each asset for a run with a single run backfill, instead of one per partition
        # (but will also cause partitions to not be marked as failed if the run fails
        return get_boolean_tag_value(os.getenv("DAGSTER_EMIT_PARTITION_SUBSET_IN_PLANNED_EVENTS"))

    @property
    def asset_records_have_last_observation(self) -> bool:
        return False

    @abstractmethod
    def initialize_concurrency_limit_to_default(self, concurrency_key: str) -> bool:
        """Initialize a concurrency limit to the instance default value.  Is a no-op for concurrency
        keys that are already configured with a limit.
        """
        raise NotImplementedError()

    @abstractmethod
    def set_concurrency_slots(self, concurrency_key: str, num: int) -> None:
        """Allocate concurrency slots for the given concurrency key."""
        raise NotImplementedError()

    @abstractmethod
    def delete_concurrency_limit(self, concurrency_key: str) -> None:
        """Delete concurrency limits and slots for the given concurrency key."""
        raise NotImplementedError()

    @abstractmethod
    def get_concurrency_keys(self) -> set[str]:
        """Get the set of concurrency limited keys."""
        raise NotImplementedError()

    @abstractmethod
    def get_concurrency_info(self, concurrency_key: str) -> ConcurrencyKeyInfo:
        """Get concurrency info for key."""
        raise NotImplementedError()

    @abstractmethod
    def get_pool_limits(self) -> Sequence[PoolLimit]:
        """Get the set of concurrency limited keys and limits."""
        raise NotImplementedError()

    @abstractmethod
    def claim_concurrency_slot(
        self,
        concurrency_key: str,
        run_id: str,
        step_key: str,
        priority: Optional[int] = None,
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
    def get_concurrency_run_ids(self) -> set[str]:
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

    @property
    def supports_asset_checks(self):
        return True

    @abstractmethod
    def get_asset_check_execution_history(
        self,
        check_key: AssetCheckKey,
        limit: int,
        cursor: Optional[int] = None,
        status: Optional[AbstractSet[AssetCheckExecutionRecordStatus]] = None,
    ) -> Sequence[AssetCheckExecutionRecord]:
        """Get executions for one asset check, sorted by recency."""
        pass

    @abstractmethod
    def get_latest_asset_check_execution_by_key(
        self, check_keys: Sequence[AssetCheckKey]
    ) -> Mapping[AssetCheckKey, AssetCheckExecutionRecord]:
        """Get the latest executions for a list of asset checks."""
        pass

    @abstractmethod
    def fetch_materializations(
        self,
        records_filter: Union[AssetKey, AssetRecordsFilter],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        raise NotImplementedError()

    @abstractmethod
    def fetch_failed_materializations(
        self,
        records_filter: Union[AssetKey, AssetRecordsFilter],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        raise NotImplementedError()

    @abstractmethod
    def fetch_observations(
        self,
        records_filter: Union[AssetKey, AssetRecordsFilter],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        raise NotImplementedError()

    @property
    def supports_run_status_change_job_name_filter(self) -> bool:
        return False

    @abstractmethod
    def fetch_run_status_changes(
        self,
        records_filter: Union[DagsterEventType, RunStatusChangeRecordsFilter],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        raise NotImplementedError()

    @abstractmethod
    def get_latest_planned_materialization_info(
        self,
        asset_key: AssetKey,
        partition: Optional[str] = None,
    ) -> Optional[PlannedMaterializationInfo]:
        raise NotImplementedError()

    @abstractmethod
    def get_updated_data_version_partitions(
        self, asset_key: AssetKey, partitions: Iterable[str], since_storage_id: int
    ) -> set[str]:
        raise NotImplementedError()

    @property
    def handles_run_events_in_store_event(self) -> bool:
        return False

    def default_run_scoped_event_tailer_offset(self) -> int:
        return 0

    def get_asset_status_cache_values(
        self,
        partitions_defs_by_key: Iterable[tuple[AssetKey, Optional[PartitionsDefinition]]],
        context: LoadingContext,
    ) -> Sequence[Optional["AssetStatusCacheValue"]]:
        """Get the cached status information for each asset."""
        from dagster._core.workspace.context import BaseWorkspaceRequestContext

        values = []

        if isinstance(context, BaseWorkspaceRequestContext):
            dynamic_partitions_loader = context.dynamic_partitions_loader
        else:
            dynamic_partitions_loader = None

        for asset_key, partitions_def in partitions_defs_by_key:
            values.append(
                get_and_update_asset_status_cache_value(
                    self._instance,
                    asset_key,
                    partitions_def,
                    dynamic_partitions_loader=dynamic_partitions_loader,
                    loading_context=context,
                )
            )
        return values

    def get_pool_config(self) -> PoolConfig:
        # Base implementation of fetching pool config.  To be overriden for remote storage
        # implementations where the local instance might not match the remote instance.
        return self._instance.get_concurrency_config().pool_config
