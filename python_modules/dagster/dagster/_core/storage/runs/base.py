from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Union

from typing_extensions import TypedDict

from dagster._core.events import DagsterEvent
from dagster._core.execution.backfill import BulkActionsFilter, BulkActionStatus, PartitionBackfill
from dagster._core.execution.telemetry import RunTelemetryData
from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance
from dagster._core.snap import ExecutionPlanSnapshot, JobSnap
from dagster._core.storage.daemon_cursor import DaemonCursorStorage
from dagster._core.storage.dagster_run import (
    DagsterRun,
    JobBucket,
    RunPartitionData,
    RunRecord,
    RunsFilter,
    TagBucket,
)
from dagster._core.storage.sql import AlembicVersion
from dagster._daemon.types import DaemonHeartbeat
from dagster._utils import PrintFn

if TYPE_CHECKING:
    from dagster._core.remote_representation.origin import RemoteJobOrigin


class RunGroupInfo(TypedDict):
    count: int
    runs: Sequence[DagsterRun]


class RunStorage(ABC, MayHaveInstanceWeakref[T_DagsterInstance], DaemonCursorStorage):
    """Abstract base class for storing pipeline run history.

    Note that run storages using SQL databases as backing stores should implement
    :py:class:`~dagster._core.storage.runs.SqlRunStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagster-webserver`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.
    """

    @abstractmethod
    def add_run(self, dagster_run: DagsterRun) -> DagsterRun:
        """Add a run to storage.

        If a run already exists with the same ID, raise DagsterRunAlreadyExists
        If the run's snapshot ID does not exist raise DagsterSnapshotDoesNotExist

        Args:
            dagster_run (DagsterRun): The run to add.
        """

    @abstractmethod
    def handle_run_event(self, run_id: str, event: DagsterEvent) -> None:
        """Update run storage in accordance to a pipeline run related DagsterEvent.

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
        ascending: bool = False,
    ) -> Sequence[DagsterRun]:
        """Return all the runs present in the storage that match the given filters.

        Args:
            filters (Optional[RunsFilter]) -- The
                :py:class:`~dagster._core.storage.pipeline_run.RunsFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.
            ascending (bool): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            List[PipelineRun]
        """

    @abstractmethod
    def get_run_ids(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[str]:
        """Return all the run IDs for runs present in the storage that match the given filters.

        Args:
            filters (Optional[RunsFilter]) -- The
                :py:class:`~dagster._core.storage.pipeline_run.RunsFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            Sequence[str]
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
    def get_run_group(self, run_id: str) -> Optional[tuple[str, Sequence[DagsterRun]]]:
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
    def get_run_tags(
        self,
        tag_keys: Sequence[str],
        value_prefix: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[tuple[str, set[str]]]:
        """Get a list of tag keys and the values that have been associated with them.

        Args:
            tag_keys (Sequence[str]): tag keys to filter by.

        Returns:
            List[Tuple[str, Set[str]]]
        """

    @abstractmethod
    def get_run_tag_keys(self) -> Sequence[str]:
        """Get a list of tag keys.

        Returns:
            List[str]
        """

    @abstractmethod
    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]) -> None:
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
        snapshot: Union[JobSnap, ExecutionPlanSnapshot],
        snapshot_id: Optional[str] = None,
    ) -> None:
        """Add a snapshot to the storage.

        Args:
            snapshot (Union[PipelineSnapshot, ExecutionPlanSnapshot])
            snapshot_id (Optional[str]): [Internal] The id of the snapshot. If not provided, the
                snapshot id will be generated from a hash of the snapshot. This should only be used
                in debugging, where we might want to import a historical run whose snapshots were
                calculated using a different hash function than the current code.
        """
        if isinstance(snapshot, JobSnap):
            self.add_job_snapshot(snapshot, snapshot_id)
        else:
            self.add_execution_plan_snapshot(snapshot, snapshot_id)

    def has_snapshot(self, snapshot_id: str):
        return self.has_job_snapshot(snapshot_id) or self.has_execution_plan_snapshot(snapshot_id)

    @abstractmethod
    def has_job_snapshot(self, job_snapshot_id: str) -> bool:
        """Check to see if storage contains a pipeline snapshot.

        Args:
            pipeline_snapshot_id (str): The id of the run.

        Returns:
            bool
        """

    @abstractmethod
    def add_job_snapshot(self, job_snapshot: JobSnap, snapshot_id: Optional[str] = None) -> str:
        """Add a pipeline snapshot to the run store.

        Pipeline snapshots are content-addressable, meaning
        that the ID for a snapshot is a hash based on the
        body of the snapshot. This function returns
        that snapshot ID.

        Args:
            job_snapshot (PipelineSnapshot)
            snapshot_id (Optional[str]): [Internal] The id of the snapshot. If not provided, the
                snapshot id will be generated from a hash of the snapshot. This should only be used
                in debugging, where we might want to import a historical run whose snapshots were
                calculated using a different hash function than the current code.

        Return:
            str: The job_snapshot_id
        """

    @abstractmethod
    def get_job_snapshot(self, job_snapshot_id: str) -> JobSnap:
        """Fetch a snapshot by ID.

        Args:
            job_snapshot_id (str)

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
        """Fetch a snapshot by ID.

        Args:
            execution_plan_snapshot_id (str)

        Returns:
            ExecutionPlanSnapshot
        """

    @abstractmethod
    def wipe(self) -> None:
        """Clears the run storage."""

    @abstractmethod
    def delete_run(self, run_id: str) -> None:
        """Remove a run from storage."""

    @property
    def supports_bucket_queries(self) -> bool:
        return False

    @abstractmethod
    def get_run_partition_data(self, runs_filter: RunsFilter) -> Sequence[RunPartitionData]:
        """Get run partition data for a given partitioned job."""

    def migrate(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        """Call this method to run any required data migrations."""

    def optimize(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        """Call this method to run any optional data migrations for optimized reads."""

    def dispose(self) -> None:
        """Explicit lifecycle management."""

    def optimize_for_webserver(self, statement_timeout: int, pool_recycle: int) -> None:
        """Allows for optimizing database connection / use in the context of a long lived webserver process."""

    # Daemon Heartbeat Storage
    #
    # Holds heartbeats from the Dagster Daemon so that other system components can alert when it's not
    # alive.
    # This is temporarily placed along with run storage to avoid adding a new instance concept. It
    # should be split out once all metadata storages are configured together.

    @abstractmethod
    def add_daemon_heartbeat(self, daemon_heartbeat: DaemonHeartbeat) -> None:
        """Called on a regular interval by the daemon."""

    @abstractmethod
    def get_daemon_heartbeats(self) -> Mapping[str, DaemonHeartbeat]:
        """Latest heartbeats of all daemon types."""

    def supports_run_telemetry(self) -> bool:
        """Whether the storage supports run telemetry."""
        return False

    def add_run_telemetry(
        self,
        run_telemetry: RunTelemetryData,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """Not implemented in base class. Should be implemented in subclasses that support telemetry."""
        pass

    @abstractmethod
    def wipe_daemon_heartbeats(self) -> None:
        """Wipe all daemon heartbeats."""

    # Backfill storage
    @abstractmethod
    def get_backfills(
        self,
        filters: Optional[BulkActionsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        status: Optional[BulkActionStatus] = None,
    ) -> Sequence[PartitionBackfill]:
        """Get a list of partition backfills."""

    @abstractmethod
    def get_backfills_count(self, filters: Optional[BulkActionsFilter] = None) -> int:
        """Return the number of backfills present in the storage that match the given filters.

        Args:
            filters (Optional[BulkActionsFilter]) -- The filter by which to filter backfills

        Returns:
            int: The number of backfills that match the given filters.
        """

    @abstractmethod
    def get_backfill(self, backfill_id: str) -> Optional[PartitionBackfill]:
        """Get the partition backfill of the given backfill id."""

    @abstractmethod
    def add_backfill(self, partition_backfill: PartitionBackfill):
        """Add partition backfill to run storage."""

    @abstractmethod
    def update_backfill(self, partition_backfill: PartitionBackfill):
        """Update a partition backfill in run storage."""

    def alembic_version(self) -> Optional[AlembicVersion]:
        return None

    @abstractmethod
    def replace_job_origin(self, run: "DagsterRun", job_origin: "RemoteJobOrigin") -> None: ...
