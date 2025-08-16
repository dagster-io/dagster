"""Run methods implementation - consolidated from RunsMixin and RunDomain."""

from collections.abc import Mapping, Sequence, Set
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional, Union

from dagster._core.definitions.events import AssetKey
from dagster._core.storage.dagster_run import (
    DagsterRun,
    DagsterRunStatus,
    JobBucket,
    RunPartitionData,
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
    from dagster._core.events import DagsterEvent
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
    from dagster._core.execution.stats import RunStepKeyStatsSnapshot
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.instance.runs.run_domain import RunDomain
    from dagster._core.origin import JobPythonOrigin
    from dagster._core.remote_origin import RemoteJobOrigin
    from dagster._core.remote_representation.code_location import CodeLocation
    from dagster._core.remote_representation.external import RemoteJob
    from dagster._core.snap import ExecutionPlanSnapshot, JobSnap
    from dagster._core.storage.dagster_run import DagsterRunStatsSnapshot
    from dagster._core.storage.event_log import EventLogStorage
    from dagster._core.storage.runs import RunStorage


class RunMethods:
    """Mixin class containing run-related functionality for DagsterInstance.

    This class consolidates run operations from RunsMixin and provides the run_domain
    property previously in DomainsMixin.
    """

    @property
    def _instance(self) -> "DagsterInstance":
        """Cast self to DagsterInstance for type-safe access to instance methods and properties."""
        import dagster._check as check
        from dagster._core.instance.instance import DagsterInstance

        return check.inst(self, DagsterInstance)

    # Private member access wrappers
    @property
    def _run_storage_impl(self) -> "RunStorage":
        """Access to run storage."""
        return self._instance._run_storage  # noqa: SLF001

    @property
    def _event_storage_impl(self) -> "EventLogStorage":
        """Access to event storage."""
        return self._instance._event_storage  # noqa: SLF001

    # Domain property - moved from DomainsMixin

    @cached_property
    def run_domain(self) -> "RunDomain":
        """Get run domain for complex business logic."""
        from dagster._core.instance.runs.run_domain import RunDomain

        return RunDomain(self._instance)

    # Core Run Retrieval Methods - moved from RunsMixin

    @traced
    def get_run_stats(self, run_id: str) -> "DagsterRunStatsSnapshot":
        return self._event_storage_impl.get_stats_for_run(run_id)

    @traced
    def get_run_step_stats(
        self, run_id: str, step_keys: Optional[Sequence[str]] = None
    ) -> Sequence["RunStepKeyStatsSnapshot"]:
        return self._event_storage_impl.get_step_stats_for_run(run_id, step_keys)

    @traced
    def get_run_tags(
        self,
        tag_keys: Sequence[str],
        value_prefix: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[tuple[str, set[str]]]:
        return self._run_storage_impl.get_run_tags(
            tag_keys=tag_keys, value_prefix=value_prefix, limit=limit
        )

    @traced
    def get_run_tag_keys(self) -> Sequence[str]:
        return self._run_storage_impl.get_run_tag_keys()

    @traced
    def get_run_group(self, run_id: str) -> Optional[tuple[str, Sequence[DagsterRun]]]:
        return self._run_storage_impl.get_run_group(run_id)

    # Run Creation Methods - moved from RunsMixin

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
        return self.run_domain.create_run_for_job(
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
        return self.run_domain.create_run(
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
        return self.run_domain.create_reexecuted_run(
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
        return self.run_domain.register_managed_run(
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

    # Run Management Methods - moved from RunsMixin

    @traced
    def add_run(self, dagster_run: DagsterRun) -> DagsterRun:
        return self._run_storage_impl.add_run(dagster_run)

    @traced
    def handle_run_event(
        self, run_id: str, event: "DagsterEvent", update_timestamp: Optional[datetime] = None
    ) -> None:
        return self._run_storage_impl.handle_run_event(run_id, event, update_timestamp)

    @traced
    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]) -> None:
        return self._run_storage_impl.add_run_tags(run_id, new_tags)

    @traced
    def has_run(self, run_id: str) -> bool:
        return self._run_storage_impl.has_run(run_id)

    @traced
    def get_runs(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
        ascending: bool = False,
    ) -> Sequence[DagsterRun]:
        return self._run_storage_impl.get_runs(filters, cursor, limit, bucket_by, ascending)

    @traced
    def get_run_ids(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[str]:
        return self._run_storage_impl.get_run_ids(filters, cursor=cursor, limit=limit)

    @traced
    def get_runs_count(self, filters: Optional[RunsFilter] = None) -> int:
        return self._run_storage_impl.get_runs_count(filters)

    @traced
    def get_run_partition_data(self, runs_filter: RunsFilter) -> Sequence[RunPartitionData]:
        """Get run partition data for a given partitioned job."""
        return self._run_storage_impl.get_run_partition_data(runs_filter)
