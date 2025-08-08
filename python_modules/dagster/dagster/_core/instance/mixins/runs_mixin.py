"""RunsMixin for DagsterInstance.

This mixin organizes runs-related surface area and API methods for DagsterInstance.
Following the architectural pattern, this mixin contains simple implementations that
primarily delegate to domain objects (run_domain, run_launcher_domain) for complex
business logic.
"""

from collections.abc import Mapping, Sequence, Set
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from dagster._annotations import public
from dagster._core.definitions.events import AssetKey
from dagster._core.storage.dagster_run import (
    DagsterRun,
    DagsterRunStatus,
    JobBucket,
    RunPartitionData,
    RunRecord,
    RunsFilter,
    TagBucket,
)
from dagster._utils import traced

if TYPE_CHECKING:
    from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
    from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.repository_definition.repository_definition import (
        RepositoryLoadData,
    )
    from dagster._core.events import DagsterEvent, DagsterEventType, JobFailureData
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
    from dagster._core.execution.stats import RunStepKeyStatsSnapshot
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.origin import JobPythonOrigin
    from dagster._core.remote_origin import RemoteJobOrigin
    from dagster._core.remote_representation import CodeLocation, RemoteJob
    from dagster._core.snap import ExecutionPlanSnapshot, JobSnap
    from dagster._core.storage.dagster_run import DagsterRunStatsSnapshot
    from dagster._core.storage.event_log import EventLogStorage
    from dagster._core.storage.event_log.base import EventLogConnection
    from dagster._core.storage.runs import RunStorage
    from dagster._core.workspace.context import BaseWorkspaceRequestContext


class RunsMixin:
    """Mixin providing runs-related surface area for DagsterInstance."""

    # These attributes are provided by DagsterInstance
    _run_storage: "RunStorage"
    _event_storage: "EventLogStorage"

    # Core Run Retrieval Methods

    @public
    def get_run_by_id(self, run_id: str) -> Optional[DagsterRun]:
        """Get a :py:class:`DagsterRun` matching the provided `run_id`.

        Args:
            run_id (str): The id of the run to retrieve.

        Returns:
            Optional[DagsterRun]: The run corresponding to the given id. If no run matching the id
                is found, return `None`.
        """
        record = self.get_run_record_by_id(run_id)
        if record is None:
            return None
        return record.dagster_run

    @public
    @traced
    def get_run_record_by_id(self, run_id: str) -> Optional[RunRecord]:
        """Get a :py:class:`RunRecord` matching the provided `run_id`.

        Args:
            run_id (str): The id of the run record to retrieve.

        Returns:
            Optional[RunRecord]: The run record corresponding to the given id. If no run matching
                the id is found, return `None`.
        """
        if not run_id:
            return None
        records = self._run_storage.get_run_records(RunsFilter(run_ids=[run_id]), limit=1)
        if not records:
            return None
        return records[0]

    @traced
    def get_run_stats(self, run_id: str) -> "DagsterRunStatsSnapshot":
        return self._event_storage.get_stats_for_run(run_id)

    @traced
    def get_run_step_stats(
        self, run_id: str, step_keys: Optional[Sequence[str]] = None
    ) -> Sequence["RunStepKeyStatsSnapshot"]:
        return self._event_storage.get_step_stats_for_run(run_id, step_keys)

    @traced
    def get_run_tags(
        self,
        tag_keys: Sequence[str],
        value_prefix: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[tuple[str, set[str]]]:
        return self._run_storage.get_run_tags(
            tag_keys=tag_keys, value_prefix=value_prefix, limit=limit
        )

    @traced
    def get_run_tag_keys(self) -> Sequence[str]:
        return self._run_storage.get_run_tag_keys()

    @traced
    def get_run_group(self, run_id: str) -> Optional[tuple[str, Sequence[DagsterRun]]]:
        return self._run_storage.get_run_group(run_id)

    # Run Creation Methods

    def create_run_for_job(
        self,
        job_def: "JobDefinition",
        execution_plan: Optional["ExecutionPlan"] = None,
        run_id: Optional[str] = None,
        run_config: Optional[Mapping[str, object]] = None,
        resolved_op_selection: Optional[Set[str]] = None,
        status: Optional[Union[DagsterRunStatus, str]] = None,
        tags: Optional[Mapping[str, str]] = None,
        root_run_id: Optional[str] = None,
        parent_run_id: Optional[str] = None,
        op_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[Set[AssetKey]] = None,
        remote_job_origin: Optional["RemoteJobOrigin"] = None,
        job_code_origin: Optional["JobPythonOrigin"] = None,
        repository_load_data: Optional["RepositoryLoadData"] = None,
    ) -> DagsterRun:
        """Delegate to run domain."""
        return cast("DagsterInstance", self).run_domain.create_run_for_job(
            job_def=job_def,
            execution_plan=execution_plan,
            run_id=run_id,
            run_config=run_config,
            resolved_op_selection=resolved_op_selection,
            status=DagsterRunStatus(status) if status else None,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            op_selection=op_selection,
            asset_selection=asset_selection,
            remote_job_origin=remote_job_origin,
            job_code_origin=job_code_origin,
            repository_load_data=repository_load_data,
        )

    def create_run(
        self,
        *,
        job_name: str,
        run_id: Optional[str],
        run_config: Optional[Mapping[str, object]],
        status: Optional[DagsterRunStatus],
        tags: Optional[Mapping[str, Any]],
        root_run_id: Optional[str],
        parent_run_id: Optional[str],
        step_keys_to_execute: Optional[Sequence[str]],
        execution_plan_snapshot: Optional["ExecutionPlanSnapshot"],
        job_snapshot: Optional["JobSnap"],
        parent_job_snapshot: Optional["JobSnap"],
        asset_selection: Optional[Set[AssetKey]],
        asset_check_selection: Optional[Set["AssetCheckKey"]],
        resolved_op_selection: Optional[Set[str]],
        op_selection: Optional[Sequence[str]],
        remote_job_origin: Optional["RemoteJobOrigin"],
        job_code_origin: Optional["JobPythonOrigin"],
        asset_graph: "BaseAssetGraph",
    ) -> DagsterRun:
        """Create a run with the given parameters."""
        return cast("DagsterInstance", self).run_domain.create_run(
            job_name=job_name,
            run_id=run_id,
            run_config=run_config,
            status=status,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            step_keys_to_execute=step_keys_to_execute,
            execution_plan_snapshot=execution_plan_snapshot,
            job_snapshot=job_snapshot,
            parent_job_snapshot=parent_job_snapshot,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
            resolved_op_selection=resolved_op_selection,
            op_selection=op_selection,
            remote_job_origin=remote_job_origin,
            job_code_origin=job_code_origin,
            asset_graph=asset_graph,
        )

    def create_reexecuted_run(
        self,
        *,
        parent_run: DagsterRun,
        code_location: "CodeLocation",
        remote_job: "RemoteJob",
        strategy: "ReexecutionStrategy",
        extra_tags: Optional[Mapping[str, Any]] = None,
        run_config: Optional[Mapping[str, Any]] = None,
        use_parent_run_tags: bool = False,
    ) -> DagsterRun:
        return cast("DagsterInstance", self).run_domain.create_reexecuted_run(
            parent_run=parent_run,
            code_location=code_location,
            remote_job=remote_job,
            strategy=strategy,
            extra_tags=extra_tags,
            run_config=run_config,
            use_parent_run_tags=use_parent_run_tags,
        )

    def register_managed_run(
        self,
        job_name: str,
        run_id: str,
        run_config: Optional[Mapping[str, object]],
        resolved_op_selection: Optional[Set[str]],
        step_keys_to_execute: Optional[Sequence[str]],
        tags: Mapping[str, str],
        root_run_id: Optional[str],
        parent_run_id: Optional[str],
        job_snapshot: Optional["JobSnap"],
        execution_plan_snapshot: Optional["ExecutionPlanSnapshot"],
        parent_job_snapshot: Optional["JobSnap"],
        op_selection: Optional[Sequence[str]] = None,
        job_code_origin: Optional["JobPythonOrigin"] = None,
    ) -> DagsterRun:
        return cast("DagsterInstance", self).run_domain.register_managed_run(
            job_name=job_name,
            run_id=run_id,
            run_config=run_config,
            resolved_op_selection=resolved_op_selection,
            step_keys_to_execute=step_keys_to_execute,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot=job_snapshot,
            execution_plan_snapshot=execution_plan_snapshot,
            parent_job_snapshot=parent_job_snapshot,
            op_selection=op_selection,
            job_code_origin=job_code_origin,
        )

    # Run Management Methods

    @traced
    def add_run(self, dagster_run: DagsterRun) -> DagsterRun:
        return self._run_storage.add_run(dagster_run)

    @traced
    def handle_run_event(
        self, run_id: str, event: "DagsterEvent", update_timestamp: Optional[datetime] = None
    ) -> None:
        return self._run_storage.handle_run_event(run_id, event, update_timestamp)

    @traced
    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]) -> None:
        return self._run_storage.add_run_tags(run_id, new_tags)

    @traced
    def has_run(self, run_id: str) -> bool:
        return self._run_storage.has_run(run_id)

    @traced
    def get_runs(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
        ascending: bool = False,
    ) -> Sequence[DagsterRun]:
        return self._run_storage.get_runs(filters, cursor, limit, bucket_by, ascending)

    @traced
    def get_run_ids(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[str]:
        return self._run_storage.get_run_ids(filters, cursor=cursor, limit=limit)

    @traced
    def get_runs_count(self, filters: Optional[RunsFilter] = None) -> int:
        return self._run_storage.get_runs_count(filters)

    @public
    @traced
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
        return self._run_storage.get_run_records(
            filters, limit, order_by, ascending, cursor, bucket_by
        )

    @traced
    def get_run_partition_data(self, runs_filter: RunsFilter) -> Sequence[RunPartitionData]:
        """Get run partition data for a given partitioned job."""
        return self._run_storage.get_run_partition_data(runs_filter)

    @public
    @traced
    def delete_run(self, run_id: str) -> None:
        """Delete a run and all events generated by that from storage.

        Args:
            run_id (str): The id of the run to delete.
        """
        self._run_storage.delete_run(run_id)
        self._event_storage.delete_events(run_id)

    @traced
    def get_records_for_run(
        self,
        run_id: str,
        cursor: Optional[str] = None,
        of_type: Optional[Union["DagsterEventType", set["DagsterEventType"]]] = None,
        limit: Optional[int] = None,
        ascending: bool = True,
    ) -> "EventLogConnection":
        return cast("DagsterInstance", self).event_domain.get_records_for_run(
            run_id, cursor, of_type, limit, ascending
        )

    # State Reporting Methods

    def report_run_canceling(self, run: DagsterRun, message: Optional[str] = None):
        """Report run canceling event."""
        return cast("DagsterInstance", self).event_domain.report_run_canceling(run, message)

    def report_run_canceled(
        self,
        dagster_run: DagsterRun,
        message: Optional[str] = None,
    ) -> "DagsterEvent":
        """Report run canceled event."""
        return cast("DagsterInstance", self).event_domain.report_run_canceled(dagster_run, message)

    def report_run_failed(
        self,
        dagster_run: DagsterRun,
        message: Optional[str] = None,
        job_failure_data: Optional["JobFailureData"] = None,
    ) -> "DagsterEvent":
        """Report run failed event."""
        return cast("DagsterInstance", self).event_domain.report_run_failed(
            dagster_run, message, job_failure_data
        )

    # Run Execution Methods

    def submit_run(self, run_id: str, workspace: "BaseWorkspaceRequestContext") -> DagsterRun:
        """Delegate to run launcher domain."""
        return cast("DagsterInstance", self).run_launcher_domain.submit_run(run_id, workspace)

    def launch_run(self, run_id: str, workspace: "BaseWorkspaceRequestContext") -> DagsterRun:
        """Delegate to run launcher domain."""
        return cast("DagsterInstance", self).run_launcher_domain.launch_run(run_id, workspace)

    def resume_run(
        self, run_id: str, workspace: "BaseWorkspaceRequestContext", attempt_number: int
    ) -> DagsterRun:
        """Delegate to run launcher domain."""
        return cast("DagsterInstance", self).run_launcher_domain.resume_run(
            run_id, workspace, attempt_number
        )

    def count_resume_run_attempts(self, run_id: str) -> int:
        """Delegate to run launcher domain."""
        return cast("DagsterInstance", self).run_launcher_domain.count_resume_run_attempts(run_id)

    def run_will_resume(self, run_id: str) -> bool:
        """Delegate to run launcher domain."""
        return cast("DagsterInstance", self).run_launcher_domain.run_will_resume(run_id)
