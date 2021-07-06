import warnings
from abc import ABC, abstractmethod, abstractproperty
from datetime import datetime
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional, Tuple, Union

from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventLogEntry
from dagster.core.execution.stats import (
    RunStepKeyStatsSnapshot,
    build_run_stats_from_events,
    build_run_step_stats_from_events,
)
from dagster.core.instance import MayHaveInstanceWeakref
from dagster.core.storage.pipeline_run import PipelineRunStatsSnapshot
from dagster.serdes import whitelist_for_serdes


class RunShardedEventsCursor(NamedTuple):
    """Pairs an id-based event log cursor with a timestamp-based run cursor, for improved
    performance on run-sharded event log storages (e.g. the default SqliteEventLogStorage). For
    run-sharded storages, the id field is ignored, since they may not be unique across shards
    """

    id: int
    run_updated_after: datetime


class EventLogRecord(NamedTuple):
    """Internal representation of an event record, as stored in a
    :py:class:`~dagster.core.storage.event_log.EventLogStorage`.
    """

    storage_id: int
    event_log_entry: EventLogEntry


@whitelist_for_serdes
class EventRecordsFilter(
    NamedTuple(
        "_EventRecordsFilter",
        [
            ("event_type", Optional[DagsterEventType]),
            ("asset_key", Optional[AssetKey]),
            ("asset_partitions", Optional[List[str]]),
            ("after_cursor", Optional[Union[int, RunShardedEventsCursor]]),
            ("before_cursor", Optional[Union[int, RunShardedEventsCursor]]),
            ("after_timestamp", Optional[float]),
            ("before_timestamp", Optional[float]),
        ],
    )
):
    """Defines a set of filter fields for fetching a set of event log entries or event log records.

    Args:
        event_type (Optional[DagsterEventType]): Filter argument for dagster event type
        asset_key (Optional[AssetKey]): Asset key for which to get asset materialization event
            entries / records.
        asset_partitions (Optional[List[str]]): Filter parameter such that only asset
            materialization events with a partition value matching one of the provided values.  Only
            valid when the `asset_key` parameter is provided.
        after_cursor (Optional[Union[int, RunShardedEventsCursor]]): Filter parameter such that only
            records with storage_id greater than the provided value are returned. Using a
            run-sharded events cursor will result in a significant performance gain when run against
            a SqliteEventLogStorage implementation (which is run-sharded)
        before_cursor (Optional[Union[int, RunShardedEventsCursor]]): Filter parameter such that
            records with storage_id less than the provided value are returned. Using a run-sharded
            events cursor will result in a significant performance gain when run against
            a SqliteEventLogStorage implementation (which is run-sharded)
        after_timestamp (Optional[float]): Filter parameter such that only event records for
            events with timestamp greater than the provided value are returned.
        before_timestamp (Optional[float]): Filter parameter such that only event records for
            events with timestamp less than the provided value are returned.
    """

    def __new__(
        cls,
        event_type: Optional[DagsterEventType] = None,
        asset_key: Optional[AssetKey] = None,
        asset_partitions: Optional[List[str]] = None,
        after_cursor: Optional[Union[int, RunShardedEventsCursor]] = None,
        before_cursor: Optional[Union[int, RunShardedEventsCursor]] = None,
        after_timestamp: Optional[float] = None,
        before_timestamp: Optional[float] = None,
    ):
        check.opt_list_param(asset_partitions, "asset_partitions", of_type=str)
        return super(EventRecordsFilter, cls).__new__(
            cls,
            event_type=check.opt_inst_param(event_type, "event_type", DagsterEventType),
            asset_key=check.opt_inst_param(asset_key, "asset_key", AssetKey),
            asset_partitions=asset_partitions,
            after_cursor=check.opt_inst_param(
                after_cursor, "after_cursor", (int, RunShardedEventsCursor)
            ),
            before_cursor=check.opt_inst_param(
                before_cursor, "before_cursor", (int, RunShardedEventsCursor)
            ),
            after_timestamp=check.opt_float_param(after_timestamp, "after_timestamp"),
            before_timestamp=check.opt_float_param(before_timestamp, "before_timestamp"),
        )


class EventLogStorage(ABC, MayHaveInstanceWeakref):
    """Abstract base class for storing structured event logs from pipeline runs.

    Note that event log storages using SQL databases as backing stores should implement
    :py:class:`~dagster.core.storage.event_log.SqlEventLogStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagit`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.
    """

    @abstractmethod
    def get_logs_for_run(
        self,
        run_id: str,
        cursor: Optional[int] = -1,
        of_type: Optional[DagsterEventType] = None,
    ) -> Iterable[EventLogEntry]:
        """Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[int]): Zero-indexed logs will be returned starting from cursor + 1,
                i.e., if cursor is -1, all logs will be returned. (default: -1)
            of_type (Optional[DagsterEventType]): the dagster event type to filter the logs.
        """

    def get_stats_for_run(self, run_id: str) -> PipelineRunStatsSnapshot:
        """Get a summary of events that have ocurred in a run."""
        return build_run_stats_from_events(run_id, self.get_logs_for_run(run_id))

    def get_step_stats_for_run(self, run_id: str, step_keys=None) -> List[RunStepKeyStatsSnapshot]:
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
    def store_event(self, event: EventLogEntry):
        """Store an event corresponding to a pipeline run.

        Args:
            event (EventLogEntry): The event to store.
        """

    @abstractmethod
    def delete_events(self, run_id: str):
        """Remove events for a given run id"""

    @abstractmethod
    def upgrade(self):
        """This method should perform any schema migrations necessary to bring an
        out-of-date instance of the storage up to date.
        """

    @abstractmethod
    def reindex_events(self, print_fn: Callable = lambda _: None, force: bool = False):
        """Call this method to run any data migrations across the event_log tables."""

    @abstractmethod
    def reindex_assets(self, print_fn: Callable = lambda _: None, force: bool = False):
        """Call this method to run any data migrations across the asset tables."""

    @abstractmethod
    def wipe(self):
        """Clear the log storage."""

    @abstractmethod
    def watch(self, run_id: str, start_cursor: int, callback: Callable):
        """Call this method to start watching."""

    @abstractmethod
    def end_watch(self, run_id: str, handler: Callable):
        """Call this method to stop watching."""

    @abstractproperty
    def is_persistent(self) -> bool:
        """bool: Whether the storage is persistent."""

    def dispose(self):
        """Explicit lifecycle management."""

    def optimize_for_dagit(self, statement_timeout: int):
        """Allows for optimizing database connection / use in the context of a long lived dagit process"""

    @abstractmethod
    def get_event_records(
        self,
        event_records_filter: Optional[EventRecordsFilter] = None,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Iterable[EventLogRecord]:
        pass

    @abstractmethod
    def has_asset_key(self, asset_key: AssetKey) -> bool:
        pass

    @abstractmethod
    def all_asset_keys(self) -> Iterable[AssetKey]:
        pass

    @abstractmethod
    def all_asset_tags(self) -> Dict[AssetKey, Dict[str, str]]:
        pass

    @abstractmethod
    def get_asset_tags(self, asset_key: AssetKey) -> Dict[str, str]:
        pass

    @abstractmethod
    def get_asset_events(
        self,
        asset_key: AssetKey,
        partitions: List[str] = None,
        before_cursor: int = None,
        after_cursor: int = None,
        limit: int = None,
        ascending: bool = False,
        include_cursor: bool = False,
        before_timestamp=None,
        cursor: int = None,  # deprecated
    ) -> Union[Iterable[EventLogEntry], Iterable[Tuple[int, EventLogEntry]]]:
        pass

    @abstractmethod
    def get_asset_run_ids(self, asset_key: AssetKey) -> Iterable[str]:
        pass

    @abstractmethod
    def wipe_asset(self, asset_key: AssetKey):
        """Remove asset index history from event log for given asset_key"""


def extract_asset_events_cursor(cursor, before_cursor, after_cursor, ascending):
    if cursor:
        warnings.warn(
            "Parameter `cursor` is a deprecated for `get_asset_events`. Use `before_cursor` or `after_cursor` instead"
        )
        if ascending and after_cursor is None:
            after_cursor = cursor
        if not ascending and before_cursor is None:
            before_cursor = cursor

    if after_cursor is not None:
        try:
            after_cursor = int(after_cursor)
        except ValueError:
            after_cursor = None

    if before_cursor is not None:
        try:
            before_cursor = int(before_cursor)
        except ValueError:
            before_cursor = None

    return before_cursor, after_cursor
