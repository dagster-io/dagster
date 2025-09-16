import logging
import os
import warnings
from collections.abc import Mapping, Sequence, Set
from typing import TYPE_CHECKING, Any, Optional

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_evaluation import (
    AssetCheckEvaluationPlanned,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.utils.time_window import TimeWindow
from dagster._core.errors import (
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
    DagsterRunAlreadyExists,
    DagsterRunConflict,
)
from dagster._core.instance.utils import (
    AIRFLOW_EXECUTION_DATE_STR,
    IS_AIRFLOW_INGEST_PIPELINE_STR,
    _check_run_equality,
    _format_field_diff,
)
from dagster._core.origin import JobPythonOrigin
from dagster._core.storage.dagster_run import (
    DagsterRun,
    DagsterRunStatus,
    assets_are_externally_managed,
)
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    ASSET_RESUME_RETRY_TAG,
    BACKFILL_ID_TAG,
    BACKFILL_TAGS,
    PARENT_RUN_ID_TAG,
    PARTITION_NAME_TAG,
    RESUME_RETRY_TAG,
    ROOT_RUN_ID_TAG,
    TAGS_TO_MAYBE_OMIT_ON_RETRY,
)
from dagster._time import get_current_datetime
from dagster._utils import is_uuid
from dagster._utils.merger import merge_dicts
from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
    from dagster._core.definitions.assets.graph.base_asset_graph import (
        BaseAssetGraph,
        BaseAssetNode,
    )
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.repository_definition.repository_definition import (
        RepositoryLoadData,
    )
    from dagster._core.definitions.utils import EntityKey
    from dagster._core.events import DagsterEvent
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.remote_origin import RemoteJobOrigin
    from dagster._core.remote_representation.code_location import CodeLocation
    from dagster._core.remote_representation.external import RemoteJob
    from dagster._core.snap import ExecutionPlanSnapshot, JobSnap
    from dagster._core.snap.execution_plan_snapshot import (
        ExecutionStepOutputSnap,
        ExecutionStepSnap,
    )


class RunDomain:
    """Domain object encapsulating run-related operations.

    This class holds a reference to a DagsterInstance and provides methods
    for creating, managing, and querying runs.
    """

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

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
        job_code_origin: Optional[JobPythonOrigin],
        asset_graph: "BaseAssetGraph",
    ) -> DagsterRun:
        """Create a run with the given parameters."""
        from dagster._core.definitions.asset_key import AssetCheckKey
        from dagster._core.remote_origin import RemoteJobOrigin
        from dagster._core.snap import ExecutionPlanSnapshot, JobSnap
        from dagster._utils.tags import normalize_tags

        check.str_param(job_name, "job_name")
        check.opt_str_param(
            run_id, "run_id"
        )  # will be assigned to make_new_run_id() lower in callstack
        check.opt_mapping_param(run_config, "run_config", key_type=str)

        check.opt_inst_param(status, "status", DagsterRunStatus)
        check.opt_mapping_param(tags, "tags", key_type=str)

        with disable_dagster_warnings():
            validated_tags = normalize_tags(tags)

        check.opt_str_param(root_run_id, "root_run_id")
        check.opt_str_param(parent_run_id, "parent_run_id")

        # If step_keys_to_execute is None, then everything is executed.  In some cases callers
        # are still exploding and sending the full list of step keys even though that is
        # unnecessary.

        check.opt_sequence_param(step_keys_to_execute, "step_keys_to_execute")
        check.opt_inst_param(
            execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot
        )

        if run_id and not is_uuid(run_id):
            check.failed(f"run_id must be a valid UUID. Got {run_id}")

        if root_run_id or parent_run_id:
            check.invariant(
                root_run_id and parent_run_id,
                "If root_run_id or parent_run_id is passed, this is a re-execution scenario and"
                " root_run_id and parent_run_id must both be passed.",
            )

        # The job_snapshot should always be set in production scenarios. In tests
        # we have sometimes omitted it out of convenience.

        check.opt_inst_param(job_snapshot, "job_snapshot", JobSnap)
        check.opt_inst_param(parent_job_snapshot, "parent_job_snapshot", JobSnap)

        if parent_job_snapshot:
            check.invariant(
                job_snapshot,
                "If parent_job_snapshot is set, job_snapshot should also be.",
            )

        # op_selection is a sequence of selection queries assigned by the user.
        # *Most* callers expand the op_selection into an explicit set of
        # resolved_op_selection via accessing remote_job.resolved_op_selection
        # but not all do. Some (launch execution mutation in graphql and backfill run
        # creation, for example) actually pass the solid *selection* into the
        # resolved_op_selection parameter, but just as a frozen set, rather than
        # fully resolving the selection, as the daemon launchers do. Given the
        # state of callers we just check to ensure that the arguments are well-formed.
        #
        # asset_selection adds another dimension to this lovely dance. op_selection
        # and asset_selection are mutually exclusive and should never both be set.
        # This is invariant is checked in a sporadic fashion around
        # the codebase, but is never enforced in a typed fashion.
        #
        # Additionally, the way that callsites currently behave *if* asset selection
        # is set (i.e., not None) then *neither* op_selection *nor*
        # resolved_op_selection is passed. In the asset selection case resolving
        # the set of assets into the canonical resolved_op_selection is done in
        # the user process, and the exact resolution is never persisted in the run.
        # We are asserting that invariant here to maintain that behavior.
        #
        # Finally, asset_check_selection can be passed along with asset_selection. It
        # is mutually exclusive with op_selection and resolved_op_selection. A `None`
        # value will include any asset checks that target selected assets. An empty set
        # will include no asset checks.

        check.opt_set_param(resolved_op_selection, "resolved_op_selection", of_type=str)
        check.opt_sequence_param(op_selection, "op_selection", of_type=str)
        check.opt_set_param(asset_selection, "asset_selection", of_type=AssetKey)
        check.opt_set_param(asset_check_selection, "asset_check_selection", of_type=AssetCheckKey)

        # asset_selection will always be None on an op job, but asset_check_selection may be
        # None or []. This is because [] and None are different for asset checks: None means
        # include all asset checks on selected assets, while [] means include no asset checks.
        # In an op job (which has no asset checks), these two are equivalent.
        if asset_selection is not None or asset_check_selection:
            check.invariant(
                op_selection is None,
                "Cannot pass op_selection with either of asset_selection or asset_check_selection",
            )

            check.invariant(
                resolved_op_selection is None,
                "Cannot pass resolved_op_selection with either of asset_selection or"
                " asset_check_selection",
            )

        # The "python origin" arguments exist so a job can be reconstructed in memory
        # after a DagsterRun has been fetched from the database.
        #
        # There are cases (notably in _logged_execute_job with Reconstructable jobs)
        # where job_code_origin and is not. In some cloud test cases only
        # remote_job_origin is passed But they are almost always passed together.
        # If these are not set the created run will never be able to be relaunched from
        # the information just in the run or in another process.

        check.opt_inst_param(remote_job_origin, "remote_job_origin", RemoteJobOrigin)
        check.opt_inst_param(job_code_origin, "job_code_origin", JobPythonOrigin)

        dagster_run = self.construct_run_with_snapshots(
            job_name=job_name,
            run_id=run_id,  # type: ignore  # (possible none)
            run_config=run_config,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
            op_selection=op_selection,
            resolved_op_selection=resolved_op_selection,
            step_keys_to_execute=step_keys_to_execute,
            status=status,
            tags=validated_tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot=job_snapshot,
            execution_plan_snapshot=execution_plan_snapshot,
            parent_job_snapshot=parent_job_snapshot,
            remote_job_origin=remote_job_origin,
            job_code_origin=job_code_origin,
            asset_graph=asset_graph,
        )

        dagster_run = self._instance.run_storage.add_run(dagster_run)

        if execution_plan_snapshot and not assets_are_externally_managed(dagster_run):
            self.log_asset_planned_events(dagster_run, execution_plan_snapshot, asset_graph)

        return dagster_run

    def construct_run_with_snapshots(
        self,
        job_name: str,
        run_id: str,
        run_config: Optional[Mapping[str, object]],
        resolved_op_selection: Optional[Set[str]],
        step_keys_to_execute: Optional[Sequence[str]],
        status: Optional[DagsterRunStatus],
        tags: Mapping[str, str],
        root_run_id: Optional[str],
        parent_run_id: Optional[str],
        job_snapshot: Optional["JobSnap"],
        execution_plan_snapshot: Optional["ExecutionPlanSnapshot"],
        parent_job_snapshot: Optional["JobSnap"],
        asset_selection: Optional[Set[AssetKey]] = None,
        asset_check_selection: Optional[Set["AssetCheckKey"]] = None,
        op_selection: Optional[Sequence[str]] = None,
        remote_job_origin: Optional["RemoteJobOrigin"] = None,
        job_code_origin: Optional[JobPythonOrigin] = None,
        asset_graph: Optional["BaseAssetGraph[BaseAssetNode]"] = None,
    ) -> DagsterRun:
        """Heavy run construction logic moved from DagsterInstance."""
        # https://github.com/dagster-io/dagster/issues/2403
        if tags and IS_AIRFLOW_INGEST_PIPELINE_STR in tags:
            if AIRFLOW_EXECUTION_DATE_STR not in tags:
                tags = {
                    **tags,
                    AIRFLOW_EXECUTION_DATE_STR: get_current_datetime().isoformat(),
                }

        check.invariant(
            not (not job_snapshot and execution_plan_snapshot),
            "It is illegal to have an execution plan snapshot and not have a pipeline snapshot."
            " It is possible to have no execution plan snapshot since we persist runs that do"
            " not successfully compile execution plans in the scheduled case.",
        )

        job_snapshot_id = (
            self.ensure_persisted_job_snapshot(job_snapshot, parent_job_snapshot)
            if job_snapshot
            else None
        )
        partitions_definition = None

        # ensure that all asset outputs list their execution type, even if the snapshot was
        # created on an older version before it was being set
        if execution_plan_snapshot and asset_graph:
            adjusted_steps = []
            for step in execution_plan_snapshot.steps:
                adjusted_outputs = []
                for output in step.outputs:
                    asset_key = output.properties.asset_key if output.properties else None
                    adjusted_output = output

                    if asset_key and asset_graph.has(asset_key):
                        if partitions_definition is None:
                            # this assumes that if one partitioned asset is in a run, all other partitioned
                            # assets in the run have the same partitions definition.
                            asset_node = asset_graph.get(asset_key)
                            partitions_definition = asset_node.partitions_def

                        if (
                            output.properties is not None
                            and output.properties.asset_execution_type is None
                        ):
                            adjusted_output = output._replace(
                                properties=output.properties._replace(
                                    asset_execution_type=asset_graph.get(asset_key).execution_type
                                )
                            )

                    adjusted_outputs.append(adjusted_output)

                adjusted_steps.append(step._replace(outputs=adjusted_outputs))

            execution_plan_snapshot = execution_plan_snapshot._replace(steps=adjusted_steps)

        execution_plan_snapshot_id = (
            self.ensure_persisted_execution_plan_snapshot(
                execution_plan_snapshot, job_snapshot_id, step_keys_to_execute
            )
            if execution_plan_snapshot and job_snapshot_id
            else None
        )

        if execution_plan_snapshot:
            from dagster._core.op_concurrency_limits_counter import (
                compute_run_op_concurrency_info_for_snapshot,
            )

            run_op_concurrency = compute_run_op_concurrency_info_for_snapshot(
                execution_plan_snapshot
            )
        else:
            run_op_concurrency = None

        # Calculate partitions_subset for time window partitions
        partitions_subset = None
        if partitions_definition is not None:
            from dagster._core.definitions.partitions.definition import DynamicPartitionsDefinition
            from dagster._core.definitions.partitions.definition.time_window import (
                TimeWindowPartitionsDefinition,
            )
            from dagster._core.definitions.partitions.subset import KeyRangesPartitionsSubset
            from dagster._core.remote_representation.external_data import PartitionsSnap

            partition_tag = tags.get(PARTITION_NAME_TAG)
            partition_key_range = (
                PartitionKeyRange(
                    tags[ASSET_PARTITION_RANGE_START_TAG],
                    tags[ASSET_PARTITION_RANGE_END_TAG],
                )
                if (
                    tags.get(ASSET_PARTITION_RANGE_START_TAG) is not None
                    and tags.get(ASSET_PARTITION_RANGE_END_TAG) is not None
                )
                else None
            )
            if partition_tag is not None or partition_key_range is not None:
                if partition_tag is not None and partition_key_range is not None:
                    raise DagsterInvariantViolationError(
                        f"Cannot have {ASSET_PARTITION_RANGE_START_TAG} or"
                        f" {ASSET_PARTITION_RANGE_END_TAG} tags set along with"
                        f" {PARTITION_NAME_TAG}"
                    )
                if partition_tag is not None:
                    partition_key_range = PartitionKeyRange(partition_tag, partition_tag)
            if partition_key_range is not None:
                # only store certain subsets that can be represented compactly
                if isinstance(partitions_definition, TimeWindowPartitionsDefinition):
                    start_window = partitions_definition.time_window_for_partition_key(
                        partition_key_range.start
                    )
                    end_window = partitions_definition.time_window_for_partition_key(
                        partition_key_range.end
                    )
                    partitions_subset = partitions_definition.get_partition_subset_in_time_window(
                        TimeWindow(start_window.start, end_window.end)
                    ).to_serializable_subset()

                    # only store the subset of time window partitions, since those can be compressed efficiently
                elif (
                    isinstance(partitions_definition, DynamicPartitionsDefinition)
                    and partitions_definition.name is not None
                ):
                    partitions_subset = KeyRangesPartitionsSubset(
                        key_ranges=[partition_key_range],
                        partitions_snap=PartitionsSnap.from_def(partitions_definition),
                    )

        return DagsterRun(
            job_name=job_name,
            run_id=run_id,
            run_config=run_config,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
            op_selection=op_selection,
            resolved_op_selection=resolved_op_selection,
            step_keys_to_execute=step_keys_to_execute,
            status=status,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot_id=job_snapshot_id,
            execution_plan_snapshot_id=execution_plan_snapshot_id,
            remote_job_origin=remote_job_origin,
            job_code_origin=job_code_origin,
            has_repository_load_data=execution_plan_snapshot is not None
            and execution_plan_snapshot.repository_load_data is not None,
            run_op_concurrency=run_op_concurrency,
            partitions_subset=partitions_subset,
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
        """Reexecution logic moved from DagsterInstance."""
        from dagster._core.execution.backfill import BulkActionStatus
        from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
        from dagster._core.execution.plan.state import KnownExecutionState
        from dagster._core.remote_representation.code_location import CodeLocation
        from dagster._core.remote_representation.external import RemoteJob

        check.inst_param(parent_run, "parent_run", DagsterRun)
        check.inst_param(code_location, "code_location", CodeLocation)
        check.inst_param(remote_job, "remote_job", RemoteJob)
        check.inst_param(strategy, "strategy", ReexecutionStrategy)
        check.opt_mapping_param(extra_tags, "extra_tags", key_type=str)
        check.opt_mapping_param(run_config, "run_config", key_type=str)

        check.bool_param(use_parent_run_tags, "use_parent_run_tags")

        root_run_id = parent_run.root_run_id or parent_run.run_id
        parent_run_id = parent_run.run_id

        # these can differ from remote_job.tags if tags were added at launch time
        parent_run_tags_to_include = {}
        if use_parent_run_tags:
            parent_run_tags_to_include = {
                key: val
                for key, val in parent_run.tags.items()
                if key not in TAGS_TO_MAYBE_OMIT_ON_RETRY
            }
            # condition to determine whether to include BACKFILL_ID_TAG, PARENT_BACKFILL_ID_TAG,
            # ROOT_BACKFILL_ID_TAG on retried run
            if parent_run.tags.get(BACKFILL_ID_TAG) is not None:
                # if the run was part of a backfill and the backfill is complete, we do not want the
                # retry to be considered part of the backfill, so remove all backfill-related tags
                backfill = self._instance.get_backfill(parent_run.tags[BACKFILL_ID_TAG])
                if backfill and backfill.status == BulkActionStatus.REQUESTED:
                    for tag in BACKFILL_TAGS:
                        if parent_run.tags.get(tag) is not None:
                            parent_run_tags_to_include[tag] = parent_run.tags[tag]

        tags = merge_dicts(
            remote_job.tags,
            parent_run_tags_to_include,
            extra_tags or {},
            {
                PARENT_RUN_ID_TAG: parent_run_id,
                ROOT_RUN_ID_TAG: root_run_id,
            },
        )

        run_config = run_config if run_config is not None else parent_run.run_config

        if strategy == ReexecutionStrategy.FROM_FAILURE:
            (
                step_keys_to_execute,
                known_state,
            ) = KnownExecutionState.build_resume_retry_reexecution(
                self._instance,
                parent_run=parent_run,
            )
            tags[RESUME_RETRY_TAG] = "true"

            if not step_keys_to_execute:
                raise DagsterInvalidSubsetError("No steps needed to be retried in the failed run.")
        elif strategy == ReexecutionStrategy.FROM_ASSET_FAILURE:
            parent_snapshot_id = check.not_none(parent_run.execution_plan_snapshot_id)
            snapshot = self._instance.get_execution_plan_snapshot(parent_snapshot_id)
            skipped_asset_keys, skipped_asset_check_keys = self.get_keys_to_reexecute(
                parent_run_id, snapshot
            )

            if not skipped_asset_keys and not skipped_asset_check_keys:
                raise DagsterInvalidSubsetError(
                    "No assets or asset checks needed to be retried in the failed run."
                )

            remote_job = code_location.get_job(
                remote_job.get_subset_selector(
                    asset_selection=skipped_asset_keys,
                    asset_check_selection=skipped_asset_check_keys,
                )
            )
            step_keys_to_execute = None
            known_state = None
            tags[ASSET_RESUME_RETRY_TAG] = "true"
        elif strategy == ReexecutionStrategy.ALL_STEPS:
            step_keys_to_execute = None
            known_state = None
        else:
            raise DagsterInvariantViolationError(f"Unknown reexecution strategy: {strategy}")

        remote_execution_plan = code_location.get_execution_plan(
            remote_job,
            run_config,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance=self._instance,
        )

        return self.create_run(
            job_name=parent_run.job_name,
            run_id=None,
            run_config=run_config,
            resolved_op_selection=parent_run.resolved_op_selection,
            step_keys_to_execute=step_keys_to_execute,
            status=DagsterRunStatus.NOT_STARTED,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot=remote_job.job_snapshot,
            execution_plan_snapshot=remote_execution_plan.execution_plan_snapshot,
            parent_job_snapshot=remote_job.parent_job_snapshot,
            op_selection=parent_run.op_selection,
            asset_selection=remote_job.asset_selection,
            asset_check_selection=remote_job.asset_check_selection,
            remote_job_origin=remote_job.get_remote_origin(),
            job_code_origin=remote_job.get_python_origin(),
            asset_graph=code_location.get_repository(
                remote_job.repository_handle.repository_name
            ).asset_graph,
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
        job_code_origin: Optional[JobPythonOrigin] = None,
    ) -> DagsterRun:
        """Managed run registration moved from DagsterInstance."""
        # The usage of this method is limited to dagster-airflow, specifically in Dagster
        # Operators that are executed in Airflow. Because a common workflow in Airflow is to
        # retry dags from arbitrary tasks, we need any node to be capable of creating a
        # DagsterRun.
        #
        # The try-except DagsterRunAlreadyExists block handles the race when multiple "root" tasks
        # simultaneously execute self._run_storage.add_run(dagster_run). When this happens, only
        # one task succeeds in creating the run, while the others get DagsterRunAlreadyExists
        # error; at this point, the failed tasks try again to fetch the existing run.
        # https://github.com/dagster-io/dagster/issues/2412

        dagster_run = self.construct_run_with_snapshots(
            job_name=job_name,
            run_id=run_id,
            run_config=run_config,
            op_selection=op_selection,
            resolved_op_selection=resolved_op_selection,
            step_keys_to_execute=step_keys_to_execute,
            status=DagsterRunStatus.MANAGED,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot=job_snapshot,
            execution_plan_snapshot=execution_plan_snapshot,
            parent_job_snapshot=parent_job_snapshot,
            job_code_origin=job_code_origin,
        )

        def get_run() -> DagsterRun:
            candidate_run = self._instance.get_run_by_id(dagster_run.run_id)

            field_diff = _check_run_equality(dagster_run, candidate_run)  # type: ignore  # (possible none)

            if field_diff:
                raise DagsterRunConflict(
                    f"Found conflicting existing run with same id {dagster_run.run_id}. Runs differ in:"
                    f"\n{_format_field_diff(field_diff)}",
                )
            return candidate_run  # type: ignore  # (possible none)

        if self._instance.has_run(dagster_run.run_id):
            return get_run()

        try:
            return self._instance.run_storage.add_run(dagster_run)
        except DagsterRunAlreadyExists:
            return get_run()

    def ensure_persisted_job_snapshot(
        self,
        job_snapshot: "JobSnap",
        parent_job_snapshot: "Optional[JobSnap]",
    ) -> str:
        """Moved from DagsterInstance._ensure_persisted_job_snapshot."""
        from dagster._core.snap import JobSnap

        check.inst_param(job_snapshot, "job_snapshot", JobSnap)
        check.opt_inst_param(parent_job_snapshot, "parent_job_snapshot", JobSnap)

        if job_snapshot.lineage_snapshot:
            parent_snapshot_id = check.not_none(parent_job_snapshot).snapshot_id

            if job_snapshot.lineage_snapshot.parent_snapshot_id != parent_snapshot_id:
                warnings.warn(
                    f"Stored parent snapshot ID {parent_snapshot_id} did not match the parent snapshot ID {job_snapshot.lineage_snapshot.parent_snapshot_id} on the subsetted job"
                )

            if not self._instance.run_storage.has_job_snapshot(parent_snapshot_id):
                self._instance.run_storage.add_job_snapshot(check.not_none(parent_job_snapshot))

        job_snapshot_id = job_snapshot.snapshot_id
        if not self._instance.run_storage.has_job_snapshot(job_snapshot_id):
            returned_job_snapshot_id = self._instance.run_storage.add_job_snapshot(job_snapshot)
            check.invariant(job_snapshot_id == returned_job_snapshot_id)

        return job_snapshot_id

    def ensure_persisted_execution_plan_snapshot(
        self,
        execution_plan_snapshot: "ExecutionPlanSnapshot",
        job_snapshot_id: str,
        step_keys_to_execute: Optional[Sequence[str]],
    ) -> str:
        """Moved from DagsterInstance._ensure_persisted_execution_plan_snapshot."""
        from dagster._core.snap.execution_plan_snapshot import (
            ExecutionPlanSnapshot,
            create_execution_plan_snapshot_id,
        )

        check.inst_param(execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot)
        check.str_param(job_snapshot_id, "job_snapshot_id")
        check.opt_nullable_sequence_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

        check.invariant(
            execution_plan_snapshot.job_snapshot_id == job_snapshot_id,
            "Snapshot mismatch: Snapshot ID in execution plan snapshot is "
            f'"{execution_plan_snapshot.job_snapshot_id}" and snapshot_id created in memory is '
            f'"{job_snapshot_id}"',
        )

        execution_plan_snapshot_id = create_execution_plan_snapshot_id(execution_plan_snapshot)

        if not self._instance.run_storage.has_execution_plan_snapshot(execution_plan_snapshot_id):
            returned_execution_plan_snapshot_id = (
                self._instance.run_storage.add_execution_plan_snapshot(execution_plan_snapshot)
            )

            check.invariant(execution_plan_snapshot_id == returned_execution_plan_snapshot_id)

        return execution_plan_snapshot_id

    def get_keys_to_reexecute(
        self,
        run_id: str,
        execution_plan_snapshot: "ExecutionPlanSnapshot",
    ) -> tuple[Set["AssetKey"], Set["AssetCheckKey"]]:
        """For a given run_id, return the subset of asset keys and asset check keys that should be
        re-executed for a run when in the `FROM_ASSET_FAILURE` mode.

        An asset key will be included if it was planned but not materialized in the original run,
        or if any of its planned blocking asset checks were planned but not executed, or failed.

        An asset check key will be included if it was planned but not executed in the original run,
        or if it was associated with an asset that will be re-executed.
        """
        from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
        from dagster._core.events import (
            AssetCheckEvaluation,
            DagsterEventType,
            StepMaterializationData,
        )

        # figure out the set of assets that were materialized and checks that successfully executed
        logs = self._instance.all_logs(
            run_id=run_id,
            of_type={
                DagsterEventType.ASSET_MATERIALIZATION,
                DagsterEventType.ASSET_CHECK_EVALUATION,
            },
        )
        executed_keys: set[EntityKey] = set()
        blocking_failure_keys: set[AssetKey] = set()
        for log in logs:
            event_data = log.dagster_event.event_specific_data if log.dagster_event else None
            if isinstance(event_data, StepMaterializationData):
                executed_keys.add(event_data.materialization.asset_key)
            elif isinstance(event_data, AssetCheckEvaluation):
                # blocking asset checks did not "successfully execute", so we keep track
                # of them and their associated assets
                if event_data.blocking and not event_data.passed:
                    blocking_failure_keys.add(event_data.asset_check_key.asset_key)
                else:
                    executed_keys.add(event_data.asset_check_key)

        # handled_keys is the set of keys that do not need to be re-executed
        to_not_reexecute = executed_keys - blocking_failure_keys

        # find the set of planned assets and checks
        to_reexecute: set[EntityKey] = set()
        for step in execution_plan_snapshot.steps:
            if step.key not in execution_plan_snapshot.step_keys_to_execute:
                continue
            to_reexecute_for_step = {
                key
                for key in step.entity_keys
                if key not in to_not_reexecute
                # we need to re-execute any asset check keys (blocking or otherwise) if the asset
                # has a failed blocking check.
                or (isinstance(key, AssetCheckKey) and key.asset_key in blocking_failure_keys)
            }
            if to_reexecute_for_step:
                # we need to include all keys that were marked as required on the step
                to_reexecute.update(to_reexecute_for_step | step.required_entity_keys)

        return (
            {key for key in to_reexecute if isinstance(key, AssetKey)},
            {key for key in to_reexecute if isinstance(key, AssetCheckKey)},
        )

    def log_asset_planned_events(
        self,
        dagster_run: DagsterRun,
        execution_plan_snapshot: "ExecutionPlanSnapshot",
        asset_graph: "BaseAssetGraph",
    ) -> None:
        """Moved from DagsterInstance._log_asset_planned_events."""
        from dagster._core.events import (
            DagsterEvent,
            DagsterEventBatchMetadata,
            DagsterEventType,
            generate_event_batch_id,
        )

        job_name = dagster_run.job_name

        events = []

        for step in execution_plan_snapshot.steps:
            if step.key in execution_plan_snapshot.step_keys_to_execute:
                for output in step.outputs:
                    asset_key = check.not_none(output.properties).asset_key
                    if asset_key:
                        events.extend(
                            self.get_materialization_planned_events_for_asset(
                                dagster_run, asset_key, job_name, step, output, asset_graph
                            )
                        )

                    if check.not_none(output.properties).asset_check_key:
                        asset_check_key = check.not_none(
                            check.not_none(output.properties).asset_check_key
                        )
                        target_asset_key = asset_check_key.asset_key
                        check_name = asset_check_key.name

                        event = DagsterEvent(
                            event_type_value=DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED.value,
                            job_name=job_name,
                            message=(
                                f"{job_name} intends to execute asset check {check_name} on"
                                f" asset {target_asset_key.to_string()}"
                            ),
                            event_specific_data=AssetCheckEvaluationPlanned(
                                target_asset_key,
                                check_name=check_name,
                            ),
                            step_key=step.key,
                        )
                        events.append(event)

        batch_id = generate_event_batch_id()
        last_index = len(events) - 1
        for i, event in enumerate(events):
            batch_metadata = (
                DagsterEventBatchMetadata(batch_id, i == last_index)
                if os.getenv("DAGSTER_BATCH_PLANNED_EVENTS")
                else None
            )
            self._instance.report_dagster_event(
                event, dagster_run.run_id, logging.DEBUG, batch_metadata=batch_metadata
            )

    def get_materialization_planned_events_for_asset(
        self,
        dagster_run: DagsterRun,
        asset_key: AssetKey,
        job_name: str,
        step: "ExecutionStepSnap",
        output: "ExecutionStepOutputSnap",
        asset_graph: "BaseAssetGraph[BaseAssetNode]",
    ) -> Sequence["DagsterEvent"]:
        """Moved from DagsterInstance._log_materialization_planned_event_for_asset."""
        from dagster._core.definitions.partitions.context import partition_loading_context
        from dagster._core.definitions.partitions.definition import DynamicPartitionsDefinition
        from dagster._core.events import AssetMaterializationPlannedData, DagsterEvent

        events = []

        partition_tag = dagster_run.tags.get(PARTITION_NAME_TAG)
        partition_range_start, partition_range_end = (
            dagster_run.tags.get(ASSET_PARTITION_RANGE_START_TAG),
            dagster_run.tags.get(ASSET_PARTITION_RANGE_END_TAG),
        )

        if partition_tag and (partition_range_start or partition_range_end):
            raise DagsterInvariantViolationError(
                f"Cannot have {ASSET_PARTITION_RANGE_START_TAG} or"
                f" {ASSET_PARTITION_RANGE_END_TAG} set along with"
                f" {PARTITION_NAME_TAG}"
            )

        partitions_subset = None
        individual_partitions = None
        if partition_range_start or partition_range_end:
            if not partition_range_start or not partition_range_end:
                raise DagsterInvariantViolationError(
                    f"Cannot have {ASSET_PARTITION_RANGE_START_TAG} or"
                    f" {ASSET_PARTITION_RANGE_END_TAG} set without the other"
                )

            partitions_def = asset_graph.get(asset_key).partitions_def
            if (
                isinstance(partitions_def, DynamicPartitionsDefinition)
                and partitions_def.name is None
            ):
                raise DagsterInvariantViolationError(
                    "Creating a run targeting a partition range is not supported for assets partitioned with function-based dynamic partitions"
                )

            if partitions_def is not None:
                with partition_loading_context(dynamic_partitions_store=self._instance):
                    if self._instance.event_log_storage.supports_partition_subset_in_asset_materialization_planned_events:
                        partitions_subset = partitions_def.subset_with_partition_keys(
                            partitions_def.get_partition_keys_in_range(
                                PartitionKeyRange(partition_range_start, partition_range_end),
                            )
                        ).to_serializable_subset()
                        individual_partitions = []
                    else:
                        individual_partitions = partitions_def.get_partition_keys_in_range(
                            PartitionKeyRange(partition_range_start, partition_range_end),
                        )
        elif check.not_none(output.properties).is_asset_partitioned and partition_tag:
            individual_partitions = [partition_tag]

        assert not (individual_partitions and partitions_subset), (
            "Should set either individual_partitions or partitions_subset, but not both"
        )

        if not individual_partitions and not partitions_subset:
            materialization_planned = DagsterEvent.build_asset_materialization_planned_event(
                job_name,
                step.key,
                AssetMaterializationPlannedData(asset_key, partition=None, partitions_subset=None),
            )
            events.append(materialization_planned)
        elif individual_partitions:
            for individual_partition in individual_partitions:
                materialization_planned = DagsterEvent.build_asset_materialization_planned_event(
                    job_name,
                    step.key,
                    AssetMaterializationPlannedData(
                        asset_key,
                        partition=individual_partition,
                        partitions_subset=partitions_subset,
                    ),
                )
                events.append(materialization_planned)

        else:
            materialization_planned = DagsterEvent.build_asset_materialization_planned_event(
                job_name,
                step.key,
                AssetMaterializationPlannedData(
                    asset_key, partition=None, partitions_subset=partitions_subset
                ),
            )
            events.append(materialization_planned)

        return events

    def create_run_for_job(
        self,
        job_def: "JobDefinition",
        execution_plan: Optional["ExecutionPlan"] = None,
        run_id: Optional[str] = None,
        run_config: Optional[Mapping[str, object]] = None,
        resolved_op_selection: Optional[Set[str]] = None,
        status: Optional[DagsterRunStatus] = None,
        tags: Optional[Mapping[str, str]] = None,
        root_run_id: Optional[str] = None,
        parent_run_id: Optional[str] = None,
        op_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[Set[AssetKey]] = None,
        remote_job_origin: Optional["RemoteJobOrigin"] = None,
        job_code_origin: Optional[JobPythonOrigin] = None,
        repository_load_data: Optional["RepositoryLoadData"] = None,
    ) -> DagsterRun:
        """Create run for job - moved from DagsterInstance.create_run_for_job()."""
        from dagster._core.definitions.job_definition import JobDefinition
        from dagster._core.execution.api import create_execution_plan
        from dagster._core.execution.plan.plan import ExecutionPlan
        from dagster._core.snap import snapshot_from_execution_plan

        check.inst_param(job_def, "pipeline_def", JobDefinition)
        check.opt_inst_param(execution_plan, "execution_plan", ExecutionPlan)
        # note that op_selection is required to execute the solid subset, which is the
        # frozenset version of the previous solid_subset.
        # op_selection is not required and will not be converted to op_selection here.
        # i.e. this function doesn't handle solid queries.
        # op_selection is only used to pass the user queries further down.
        check.opt_set_param(resolved_op_selection, "resolved_op_selection", of_type=str)
        check.opt_list_param(op_selection, "op_selection", of_type=str)
        check.opt_set_param(asset_selection, "asset_selection", of_type=AssetKey)

        # op_selection never provided
        if asset_selection or op_selection:
            # for cases when `create_run_for_pipeline` is directly called
            job_def = job_def.get_subset(
                asset_selection=asset_selection,
                op_selection=op_selection,
            )

        if not execution_plan:
            execution_plan = create_execution_plan(
                job=job_def,
                run_config=run_config,
                instance_ref=self._instance.get_ref() if self._instance.is_persistent else None,
                tags=tags,
                repository_load_data=repository_load_data,
            )

        return self.create_run(
            job_name=job_def.name,
            run_id=run_id,
            run_config=run_config,
            op_selection=op_selection,
            asset_selection=asset_selection,
            asset_check_selection=None,
            resolved_op_selection=resolved_op_selection,
            step_keys_to_execute=execution_plan.step_keys_to_execute,
            status=status,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot=job_def.get_job_snapshot(),
            execution_plan_snapshot=snapshot_from_execution_plan(
                execution_plan,
                job_def.get_job_snapshot_id(),
            ),
            parent_job_snapshot=job_def.get_parent_job_snapshot(),
            remote_job_origin=remote_job_origin,
            job_code_origin=job_code_origin,
            asset_graph=job_def.asset_layer.asset_graph,
        )
