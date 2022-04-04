from abc import ABC, abstractproperty
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union

from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.run_request import InstigatorType
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.events.log import EventLogEntry
from dagster.core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster.core.execution.stats import RunStepKeyStatsSnapshot
from dagster.core.instance import MayHaveInstanceWeakref
from dagster.core.scheduler.instigation import InstigatorState, InstigatorTick, TickData, TickStatus
from dagster.core.snap import ExecutionPlanSnapshot, PipelineSnapshot
from dagster.core.storage.event_log.base import EventLogRecord, EventRecordsFilter
from dagster.core.storage.pipeline_run import (
    JobBucket,
    PipelineRun,
    PipelineRunStatsSnapshot,
    RunRecord,
    RunsFilter,
    TagBucket,
)
from dagster.daemon.types import DaemonHeartbeat

from .event_log.base import EventLogStorage
from .runs.base import RunStorage
from .schedules.base import ScheduleStorage


class DagsterStorage(ABC, MayHaveInstanceWeakref):
    """Abstract base class for storing pipeline run history.

    Note that run storages using SQL databases as backing stores should implement
    :py:class:`~dagster.core.storage.runs.SqlRunStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagit`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.
    """

    @abstractproperty
    def event_log_storage(self) -> EventLogStorage:
        raise NotImplementedError()

    @abstractproperty
    def run_storage(self) -> RunStorage:
        raise NotImplementedError()

    @abstractproperty
    def schedule_storage(self) -> ScheduleStorage:
        raise NotImplementedError()

    def add_run(self, pipeline_run: PipelineRun) -> PipelineRun:
        """Add a run to storage.

        If a run already exists with the same ID, raise DagsterRunAlreadyExists
        If the run's snapshot ID does not exist raise DagsterSnapshotDoesNotExist

        Args:
            pipeline_run (PipelineRun): The run to add.
        """

        return self.run_storage.add_run(pipeline_run)

    def handle_run_event(self, run_id: str, event: DagsterEvent):
        """Update run storage in accordance to a pipeline run related DagsterEvent

        Args:
            run_id (str)
            event (DagsterEvent)
        """

        return self.run_storage.handle_run_event(run_id, event)

    def get_runs(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
    ) -> Iterable[PipelineRun]:
        """Return all the runs present in the storage that match the given filters.

        Args:
            filters (Optional[RunsFilter]) -- The
                :py:class:`~dagster.core.storage.pipeline_run.RunsFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            List[PipelineRun]
        """

        return self.run_storage.get_runs(filters, cursor, limit, bucket_by)

    def get_runs_count(self, filters: Optional[RunsFilter] = None) -> int:
        """Return the number of runs present in the storage that match the given filters.

        Args:
            filters (Optional[RunsFilter]) -- The
                :py:class:`~dagster.core.storage.pipeline_run.PipelineRunFilter` by which to filter
                runs

        Returns:
            int: The number of runs that match the given filters.
        """
        return self.run_storage.get_runs_count(filters)

    def get_run_group(self, run_id: str) -> Optional[Tuple[str, Iterable[PipelineRun]]]:
        """Get the run group to which a given run belongs.

        Args:
            run_id (str): If the corresponding run is the descendant of some root run (i.e., there
                is a root_run_id on the :py:class:`PipelineRun`), that root run and all of its
                descendants are returned; otherwise, the group will consist only of the given run
                (a run that does not descend from any root is its own root).

        Returns:
            Optional[Tuple[string, List[PipelineRun]]]: If there is a corresponding run group, tuple
                whose first element is the root_run_id and whose second element is a list of all the
                descendent runs. Otherwise `None`.
        """
        return self.run_storage.get_run_group(run_id)

    def get_run_groups(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Dict[str, Union[Iterable[PipelineRun], int]]]:
        """Return all of the run groups present in the storage that include rows matching the
        given filter.

        Args:
            filter (Optional[RunsFilter]) -- The
                :py:class:`~dagster.core.storage.pipeline_run.RunsFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            Dict[str, Dict[str, Union[List[PipelineRun], int]]]: Specifically, a dict of the form
                ``{'pipeline_run_id': {'runs': [PipelineRun, ...], 'count': int}, ...}``. The
                instances of :py:class:`~dagster.core.pipeline_run.PipelineRun` returned in this
                data structure correspond to all of the runs that would have been returned by
                calling :py:meth:`get_run_groups` with the same arguments, plus their corresponding
                root runs, if any. The keys of this structure are the run_ids of all of the root
                runs (a run with no root is its own root). The integer counts are inclusive of all
                of the root runs' children, including those that would not have been returned by
                calling :py:meth:`get_run_groups` with the same arguments, but exclusive of the root
                run itself; i.e., if a run has no children, the count will be 0.
        """

        return self.run_storage.get_run_groups(filters, cursor, limit)

    def get_run_by_id(self, run_id: str) -> Optional[PipelineRun]:
        """Get a run by its id.

        Args:
            run_id (str): The id of the run

        Returns:
            Optional[PipelineRun]
        """
        return self.run_storage.get_run_by_id(run_id)

    def get_run_records(
        self,
        filters: Optional[RunsFilter] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
        cursor: Optional[str] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
    ) -> List[RunRecord]:
        """Return a list of run records stored in the run storage, sorted by the given column in given order.

        Args:
            filters (Optional[RunsFilter]): the filter by which to filter runs.
            limit (Optional[int]): Number of results to get. Defaults to infinite.
            order_by (Optional[str]): Name of the column to sort by. Defaults to id.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            List[RunRecord]: List of run records stored in the run storage.
        """
        return self.run_storage.get_run_records(
            filters, limit, order_by, ascending, cursor, bucket_by
        )

    def get_run_tags(self) -> List[Tuple[str, Set[str]]]:
        """Get a list of tag keys and the values that have been associated with them.

        Returns:
            List[Tuple[str, Set[str]]]
        """
        return self.run_storage.get_run_tags()

    def add_run_tags(self, run_id: str, new_tags: Dict[str, str]):
        """Add additional tags for a pipeline run.

        Args:
            run_id (str)
            new_tags (Dict[string, string])
        """

        return self.run_storage.add_run_tags(run_id, new_tags)

    def has_run(self, run_id: str) -> bool:
        """Check if the storage contains a run.

        Args:
            run_id (str): The id of the run

        Returns:
            bool
        """
        return self.run_storage.has_run(run_id)

    def add_snapshot(
        self,
        snapshot: Union[PipelineSnapshot, ExecutionPlanSnapshot],
        snapshot_id: Optional[str] = None,
    ):
        """Add a snapshot to the storage.

        Args:
            snapshot (Union[PipelineSnapshot, ExecutionPlanSnapshot])
            snapshot_id (Optional[str]): [Internal] The id of the snapshot. If not provided, the
                snapshot id will be generated from a hash of the snapshot. This should only be used
                in debugging, where we might want to import a historical run whose snapshots were
                calculated using a different hash function than the current code.
        """
        if isinstance(snapshot, PipelineSnapshot):
            return self.add_pipeline_snapshot(snapshot, snapshot_id)
        else:
            return self.add_execution_plan_snapshot(snapshot, snapshot_id)

    def has_snapshot(self, snapshot_id: str):
        return self.has_pipeline_snapshot(snapshot_id) or self.has_execution_plan_snapshot(
            snapshot_id
        )

    def has_pipeline_snapshot(self, pipeline_snapshot_id: str) -> bool:
        """Check to see if storage contains a pipeline snapshot.

        Args:
            pipeline_snapshot_id (str): The id of the run.

        Returns:
            bool
        """
        return self.run_storage.has_pipeline_snapshot(pipeline_snapshot_id)

    def add_pipeline_snapshot(
        self, pipeline_snapshot: PipelineSnapshot, snapshot_id: Optional[str] = None
    ) -> str:
        """Add a pipeline snapshot to the run store.

        Pipeline snapshots are content-addressable, meaning
        that the ID for a snapshot is a hash based on the
        body of the snapshot. This function returns
        that snapshot ID.

        Args:
            pipeline_snapshot (PipelineSnapshot)
            snapshot_id (Optional[str]): [Internal] The id of the snapshot. If not provided, the
                snapshot id will be generated from a hash of the snapshot. This should only be used
                in debugging, where we might want to import a historical run whose snapshots were
                calculated using a different hash function than the current code.

        Return:
            str: The pipeline_snapshot_id
        """
        return self.run_storage.add_pipeline_snapshot(pipeline_snapshot, snapshot_id)

    def get_pipeline_snapshot(self, pipeline_snapshot_id: str) -> PipelineSnapshot:
        """Fetch a snapshot by ID

        Args:
            pipeline_snapshot_id (str)

        Returns:
            PipelineSnapshot
        """
        return self.run_storage.get_pipeline_snapshot(pipeline_snapshot_id)

    def has_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> bool:
        """Check to see if storage contains an execution plan snapshot.

        Args:
            execution_plan_snapshot_id (str): The id of the execution plan.

        Returns:
            bool
        """
        return self.run_storage.has_execution_plan_snapshot(execution_plan_snapshot_id)

    def add_execution_plan_snapshot(
        self, execution_plan_snapshot: ExecutionPlanSnapshot, snapshot_id: Optional[str] = None
    ) -> str:
        """Add an execution plan snapshot to the run store.

        Execution plan snapshots are content-addressable, meaning
        that the ID for a snapshot is a hash based on the
        body of the snapshot. This function returns
        that snapshot ID.

        Args:
            execution_plan_snapshot (ExecutionPlanSnapshot)
            snapshot_id (Optional[str]): [Internal] The id of the snapshot. If not provided, the
                snapshot id will be generated from a hash of the snapshot. This should only be used
                in debugging, where we might want to import a historical run whose snapshots were
                calculated using a different hash function than the current code.

        Return:
            str: The execution_plan_snapshot_id
        """
        return self.run_storage.add_execution_plan_snapshot(execution_plan_snapshot, snapshot_id)

    def get_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> ExecutionPlanSnapshot:
        """Fetch a snapshot by ID

        Args:
            execution_plan_snapshot_id (str)

        Returns:
            ExecutionPlanSnapshot
        """
        return self.run_storage.get_execution_plan_snapshot(execution_plan_snapshot_id)

    def wipe(self):
        """Clears storage."""
        self.run_storage.wipe()
        self.event_log_storage.wipe()
        self.schedule_storage.wipe()

    def delete_run(self, run_id: str):
        """Remove a run from storage"""
        return self.run_storage.delete_run(run_id)

    @property
    def supports_bucket_queries(self):
        return True

    def migrate(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        """Call this method to run any required data migrations"""
        self.run_storage.migrate(print_fn, force_rebuild_all)
        self.event_log_storage.reindex_assets(print_fn, force_rebuild_all)
        self.schedule_storage.migrate(print_fn, force_rebuild_all)

    def optimize(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        """Call this method to run any optional data migrations for optimized reads"""
        self.run_storage.optimize(print_fn, force_rebuild_all)
        self.event_log_storage.reindex_assets(print_fn, force_rebuild_all)
        self.event_log_storage.reindex_events(print_fn, force_rebuild_all)
        self.schedule_storage.optimize(print_fn, force_rebuild_all)

    def dispose(self):
        """Explicit lifecycle management."""
        self.run_storage.dispose()
        self.event_log_storage.dispose()
        self.schedule_storage.dispose()

    def optimize_for_dagit(self, statement_timeout: int):
        """Allows for optimizing database connection / use in the context of a long lived dagit process"""
        self.run_storage.optimize_for_dagit(statement_timeout)
        self.event_log_storage.optimize_for_dagit(statement_timeout)
        self.schedule_storage.optimize_for_dagit(statement_timeout)

    # Daemon Heartbeat Storage
    #
    # Holds heartbeats from the Dagster Daemon so that other system components can alert when it's not
    # alive.
    # This is temporarily placed along with run storage to avoid adding a new instance concept. It
    # should be split out once all metadata storages are configured together.

    def add_daemon_heartbeat(self, daemon_heartbeat: DaemonHeartbeat):
        """Called on a regular interval by the daemon"""
        return self.run_storage.add_daemon_heartbeat(daemon_heartbeat)

    def get_daemon_heartbeats(self) -> Dict[str, DaemonHeartbeat]:
        """Latest heartbeats of all daemon types"""
        return self.run_storage.get_daemon_heartbeats()

    def wipe_daemon_heartbeats(self):
        """Wipe all daemon heartbeats"""
        return self.run_storage.wipe_daemon_heartbeats()

    def get_backfills(
        self,
        status: Optional[BulkActionStatus] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[PartitionBackfill]:
        """Get a list of partition backfills"""
        return self.run_storage.get_backfills(status, cursor, limit)

    def get_backfill(self, backfill_id: str) -> Optional[PartitionBackfill]:
        """Get the partition backfill of the given backfill id."""
        return self.run_storage.get_backfill(backfill_id)

    def add_backfill(self, partition_backfill: PartitionBackfill):
        """Add partition backfill to run storage"""
        return self.run_storage.add_backfill(partition_backfill)

    def update_backfill(self, partition_backfill: PartitionBackfill):
        """Update a partition backfill in run storage"""
        return self.run_storage.update_backfill(partition_backfill)

    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional[InstigatorType] = None,
    ) -> Iterable[InstigatorState]:
        """Return all InstigationStates present in storage

        Args:
            repository_origin_id (Optional[str]): The ExternalRepository target id to scope results to
            instigator_type (Optional[InstigatorType]): The InstigatorType to scope results to
        """
        return self.schedule_storage.all_instigator_state(
            repository_origin_id, repository_selector_id, instigator_type
        )

    def get_instigator_state(self, origin_id: str, selector_id: str) -> InstigatorState:
        """Return the instigator state for the given id

        Args:
            origin_id (str): The unique instigator identifier
        """
        return self.schedule_storage.get_instigator_state(origin_id, selector_id)

    def add_instigator_state(self, state: InstigatorState):
        """Add an instigator state to storage.

        Args:
            state (InstigatorState): The state to add
        """
        return self.schedule_storage.add_instigator_state(state)

    def update_instigator_state(self, state: InstigatorState):
        """Update an instigator state in storage.

        Args:
            state (InstigatorState): The state to update
        """
        return self.schedule_storage.update_instigator_state(state)

    def delete_instigator_state(self, origin_id: str, selector_id: str):
        """Delete a state in storage.

        Args:
            origin_id (str): The id of the instigator target to delete
        """
        return self.schedule_storage.delete_instigator_state(origin_id, selector_id)

    @property
    def supports_batch_queries(self):
        return False

    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence[TickStatus]] = None,
    ) -> Mapping[str, Iterable[InstigatorTick]]:
        raise NotImplementedError()

    def get_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: Optional[float] = None,
        after: Optional[float] = None,
        limit: Optional[int] = None,
        statuses: Optional[List[TickStatus]] = None,
    ) -> Iterable[InstigatorTick]:
        """Get the ticks for a given instigator.

        Args:
            origin_id (str): The id of the instigator target
        """
        return self.schedule_storage.get_ticks(
            origin_id, selector_id, before, after, limit, statuses
        )

    def create_tick(self, tick_data: TickData):
        """Add a tick to storage.

        Args:
            tick_data (TickData): The tick to add
        """
        return self.schedule_storage.create_tick(tick_data)

    def update_tick(self, tick: InstigatorTick):
        """Update a tick already in storage.

        Args:
            tick (InstigatorTick): The tick to update
        """
        return self.schedule_storage.update_tick(tick)

    def purge_ticks(self, origin_id: str, selector_id: str, tick_status: TickStatus, before: float):
        """Wipe ticks for an instigator for a certain status and timestamp.

        Args:
            origin_id (str): The id of the instigator target to delete
            tick_status (TickStatus): The tick status to wipe
            before (datetime): All ticks before this datetime will get purged
        """
        return self.schedule_storage.purge_ticks(origin_id, selector_id, tick_status, before)

    def get_logs_for_run(
        self,
        run_id: str,
        cursor: Optional[int] = -1,
        of_type: Optional[Union[DagsterEventType, Set[DagsterEventType]]] = None,
        limit: Optional[int] = None,
    ) -> Iterable[EventLogEntry]:
        """Get all of the logs corresponding to a run.

        Args:
            run_id (str): The id of the run for which to fetch logs.
            cursor (Optional[int]): Zero-indexed logs will be returned starting from cursor + 1,
                i.e., if cursor is -1, all logs will be returned. (default: -1)
            of_type (Optional[DagsterEventType]): the dagster event type to filter the logs.
        """
        return self.event_log_storage.get_logs_for_run(run_id, cursor, of_type, limit)

    def get_stats_for_run(self, run_id: str) -> PipelineRunStatsSnapshot:
        """Get a summary of events that have ocurred in a run."""
        return self.event_log_storage.get_stats_for_run(run_id)

    def get_step_stats_for_run(self, run_id: str, step_keys=None) -> List[RunStepKeyStatsSnapshot]:
        """Get per-step stats for a pipeline run."""
        return self.event_log_storage.get_step_stats_for_run(run_id, step_keys)

    def store_event(self, event: EventLogEntry):
        """Store an event corresponding to a pipeline run.

        Args:
            event (EventLogEntry): The event to store.
        """
        return self.event_log_storage.store_event(event)

    def delete_events(self, run_id: str):
        """Remove events for a given run id"""
        return self.event_log_storage.delete_events(run_id)

    def watch(self, run_id: str, start_cursor: int, callback: Callable):
        """Call this method to start watching."""
        return self.event_log_storage.watch(run_id, start_cursor, callback)

    def end_watch(self, run_id: str, handler: Callable):
        """Call this method to stop watching."""
        return self.event_log_storage.end_watch(run_id, handler)

    def get_event_records(
        self,
        event_records_filter: Optional[EventRecordsFilter] = None,
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Iterable[EventLogRecord]:
        return self.event_log_storage.get_event_records(event_records_filter, limit, ascending)

    def has_asset_key(self, asset_key: AssetKey) -> bool:
        return self.event_log_storage.has_asset_key(asset_key)

    def all_asset_keys(self) -> Iterable[AssetKey]:
        return self.event_log_storage.all_asset_keys()

    def get_asset_keys(
        self,
        prefix: Optional[List[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Iterable[AssetKey]:
        return self.event_log_storage.get_asset_keys(prefix, limit, cursor)

    def get_latest_materialization_events(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, Optional[EventLogEntry]]:
        return self.event_log_storage.get_latest_materialization_events(asset_keys)

    def get_asset_events(
        self,
        asset_key: AssetKey,
        partitions: Optional[List[str]] = None,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
        limit: Optional[int] = None,
        ascending: bool = False,
        include_cursor: bool = False,
        before_timestamp=None,
        cursor: Optional[int] = None,  # deprecated
    ) -> Union[Iterable[EventLogEntry], Iterable[Tuple[int, EventLogEntry]]]:
        return self.event_log_storage.get_asset_events(
            asset_key,
            partitions,
            before_cursor,
            after_cursor,
            limit,
            ascending,
            include_cursor,
            before_timestamp,
            cursor,
        )

    def get_asset_run_ids(self, asset_key: AssetKey) -> Iterable[str]:
        return self.event_log_storage.get_asset_run_ids(asset_key)

    def wipe_asset(self, asset_key: AssetKey):
        """Remove asset index history from event log for given asset_key"""
        return self.event_log_storage.wipe_asset(asset_key)

    def get_materialization_count_by_partition(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, Mapping[str, int]]:
        return self.event_log_storage.get_materialization_count_by_partition(asset_keys)
