from abc import ABC, abstractmethod
from typing import Callable, Iterable, Mapping, Optional, Sequence, Set, Tuple, Union

from dagster._core.events import DagsterEvent
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.instance import MayHaveInstanceWeakref
from dagster._core.snap import ExecutionPlanSnapshot, PipelineSnapshot
from dagster._core.storage.pipeline_run import (
    JobBucket,
    PipelineRun,
    RunPartitionData,
    RunRecord,
    RunsFilter,
    TagBucket,
)
from dagster._daemon.types import DaemonHeartbeat


class RunStorage(ABC, MayHaveInstanceWeakref):
    """Abstract base class for storing pipeline run history.

    Note that run storages using SQL databases as backing stores should implement
    :py:class:`~dagster._core.storage.runs.SqlRunStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagit`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.
    """

    @abstractmethod
    def add_run(self, pipeline_run: PipelineRun) -> PipelineRun:
        """Add a run to storage.

        If a run already exists with the same ID, raise DagsterRunAlreadyExists
        If the run's snapshot ID does not exist raise DagsterSnapshotDoesNotExist

        Args:
            pipeline_run (PipelineRun): The run to add.
        """

    @abstractmethod
    def handle_run_event(self, run_id: str, event: DagsterEvent):
        """Update run storage in accordance to a pipeline run related DagsterEvent

        Args:
            run_id (str)
            event (DagsterEvent)
        """

    @abstractmethod
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
                :py:class:`~dagster._core.storage.pipeline_run.RunsFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            List[PipelineRun]
        """

    @abstractmethod
    def get_runs_count(self, filters: Optional[RunsFilter] = None) -> int:
        """Return the number of runs present in the storage that match the given filters.

        Args:
            filters (Optional[RunsFilter]) -- The
                :py:class:`~dagster._core.storage.pipeline_run.PipelineRunFilter` by which to filter
                runs

        Returns:
            int: The number of runs that match the given filters.
        """

    @abstractmethod
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

    @abstractmethod
    def get_run_groups(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Mapping[str, Mapping[str, Union[Iterable[PipelineRun], int]]]:
        """Return all of the run groups present in the storage that include rows matching the
        given filter.

        Args:
            filter (Optional[RunsFilter]) -- The
                :py:class:`~dagster._core.storage.pipeline_run.RunsFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            Dict[str, Dict[str, Union[List[PipelineRun], int]]]: Specifically, a dict of the form
                ``{'pipeline_run_id': {'runs': [PipelineRun, ...], 'count': int}, ...}``. The
                instances of :py:class:`~dagster._core.pipeline_run.PipelineRun` returned in this
                data structure correspond to all of the runs that would have been returned by
                calling :py:meth:`get_run_groups` with the same arguments, plus their corresponding
                root runs, if any. The keys of this structure are the run_ids of all of the root
                runs (a run with no root is its own root). The integer counts are inclusive of all
                of the root runs' children, including those that would not have been returned by
                calling :py:meth:`get_run_groups` with the same arguments, but exclusive of the root
                run itself; i.e., if a run has no children, the count will be 0.
        """

        # Note that we could have made the opposite decision here and filtered for root runs
        # matching a given filter, etc., rather than for child runs; so that asking for the last 5
        # run groups would give the last 5 roots and their descendants, rather than the last 5
        # children and their roots. Consider the case where we have just been retrying runs
        # belonging to a group created long ago; it makes sense to bump these to the top of the
        # interface rather than burying them deeply paginated down. Note also that this query can
        # return no more run groups than there are runs in an equivalent call to get_runs, and no
        # more than 2x total instances of PipelineRun.

    @abstractmethod
    def get_run_by_id(self, run_id: str) -> Optional[PipelineRun]:
        """Get a run by its id.

        Args:
            run_id (str): The id of the run

        Returns:
            Optional[PipelineRun]
        """

    @abstractmethod
    def get_run_records(
        self,
        filters: Optional[RunsFilter] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
        cursor: Optional[str] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
    ) -> Sequence[RunRecord]:
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

    @abstractmethod
    def get_run_tags(self) -> Sequence[Tuple[str, Set[str]]]:
        """Get a list of tag keys and the values that have been associated with them.

        Returns:
            List[Tuple[str, Set[str]]]
        """

    @abstractmethod
    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]):
        """Add additional tags for a pipeline run.

        Args:
            run_id (str)
            new_tags (Dict[string, string])
        """

    @abstractmethod
    def has_run(self, run_id: str) -> bool:
        """Check if the storage contains a run.

        Args:
            run_id (str): The id of the run

        Returns:
            bool
        """

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
            self.add_pipeline_snapshot(snapshot, snapshot_id)
        else:
            self.add_execution_plan_snapshot(snapshot, snapshot_id)

    def has_snapshot(self, snapshot_id: str):
        return self.has_pipeline_snapshot(snapshot_id) or self.has_execution_plan_snapshot(
            snapshot_id
        )

    @abstractmethod
    def has_pipeline_snapshot(self, pipeline_snapshot_id: str) -> bool:
        """Check to see if storage contains a pipeline snapshot.

        Args:
            pipeline_snapshot_id (str): The id of the run.

        Returns:
            bool
        """

    @abstractmethod
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

    @abstractmethod
    def get_pipeline_snapshot(self, pipeline_snapshot_id: str) -> PipelineSnapshot:
        """Fetch a snapshot by ID

        Args:
            pipeline_snapshot_id (str)

        Returns:
            PipelineSnapshot
        """

    @abstractmethod
    def has_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> bool:
        """Check to see if storage contains an execution plan snapshot.

        Args:
            execution_plan_snapshot_id (str): The id of the execution plan.

        Returns:
            bool
        """

    @abstractmethod
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

    @abstractmethod
    def get_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> ExecutionPlanSnapshot:
        """Fetch a snapshot by ID

        Args:
            execution_plan_snapshot_id (str)

        Returns:
            ExecutionPlanSnapshot
        """

    @abstractmethod
    def wipe(self):
        """Clears the run storage."""

    @abstractmethod
    def delete_run(self, run_id: str):
        """Remove a run from storage"""

    @property
    def supports_bucket_queries(self):
        return True

    @abstractmethod
    def get_run_partition_data(self, runs_filter: RunsFilter) -> Sequence[RunPartitionData]:
        """Get run partition data for a given partitioned job."""

    def migrate(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        """Call this method to run any required data migrations"""

    def optimize(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        """Call this method to run any optional data migrations for optimized reads"""

    def dispose(self):
        """Explicit lifecycle management."""

    def optimize_for_dagit(self, statement_timeout: int, pool_recycle: int):
        """Allows for optimizing database connection / use in the context of a long lived dagit process"""

    # Daemon Heartbeat Storage
    #
    # Holds heartbeats from the Dagster Daemon so that other system components can alert when it's not
    # alive.
    # This is temporarily placed along with run storage to avoid adding a new instance concept. It
    # should be split out once all metadata storages are configured together.

    @abstractmethod
    def add_daemon_heartbeat(self, daemon_heartbeat: DaemonHeartbeat):
        """Called on a regular interval by the daemon"""

    @abstractmethod
    def get_daemon_heartbeats(self) -> Mapping[str, DaemonHeartbeat]:
        """Latest heartbeats of all daemon types"""

    @abstractmethod
    def wipe_daemon_heartbeats(self):
        """Wipe all daemon heartbeats"""

    # Backfill storage
    @abstractmethod
    def get_backfills(
        self,
        status: Optional[BulkActionStatus] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[PartitionBackfill]:
        """Get a list of partition backfills"""

    @abstractmethod
    def get_backfill(self, backfill_id: str) -> Optional[PartitionBackfill]:
        """Get the partition backfill of the given backfill id."""

    @abstractmethod
    def add_backfill(self, partition_backfill: PartitionBackfill):
        """Add partition backfill to run storage"""

    @abstractmethod
    def update_backfill(self, partition_backfill: PartitionBackfill):
        """Update a partition backfill in run storage"""

    def alembic_version(self):
        return None

    # Key Value Storage
    #
    # Stores arbitrary key-value pairs. Currently used for the cursor for the auto-reexecution
    # deamon. Bundled into run storage for convenience.

    def supports_kvs(self):
        return True

    @abstractmethod
    def kvs_get(self, keys: Set[str]) -> Mapping[str, str]:
        """Retrieve the value for a given key in the current deployment."""

    @abstractmethod
    def kvs_set(self, pairs: Mapping[str, str]) -> None:
        """Set the value for a given key in the current deployment."""
