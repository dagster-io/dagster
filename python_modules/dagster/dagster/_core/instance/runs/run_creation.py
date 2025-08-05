from collections.abc import Mapping, Sequence, Set
from typing import TYPE_CHECKING, Any, Optional

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partitions.utils.time_window import TimeWindow
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.instance.runs.run_events import log_asset_planned_events
from dagster._core.instance.runs.snapshot_persistence import (
    ensure_persisted_execution_plan_snapshot,
    ensure_persisted_job_snapshot,
)
from dagster._core.instance.utils import AIRFLOW_EXECUTION_DATE_STR, IS_AIRFLOW_INGEST_PIPELINE_STR
from dagster._core.origin import JobPythonOrigin
from dagster._core.storage.dagster_run import (
    DagsterRun,
    DagsterRunStatus,
    assets_are_externally_managed,
)
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    PARTITION_NAME_TAG,
)
from dagster._time import get_current_datetime
from dagster._utils import is_uuid
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
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.instance.runs.run_instance_ops import RunInstanceOps
    from dagster._core.remote_representation.origin import RemoteJobOrigin
    from dagster._core.snap import ExecutionPlanSnapshot, JobSnap


def create_run_for_job(
    ops: "RunInstanceOps",
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
    """Create a run for a given job definition.

    This function handles job subsetting, execution plan creation, and parameter validation
    before delegating to create_run for actual run creation.
    """
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
            instance_ref=ops.get_ref() if ops.is_persistent else None,
            tags=tags,
            repository_load_data=repository_load_data,
        )

    return create_run(
        ops,
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


def create_run(
    ops: "RunInstanceOps",
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
    from dagster._core.remote_representation.origin import RemoteJobOrigin
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
    check.opt_inst_param(execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot)

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

    dagster_run = construct_run_with_snapshots(
        ops,
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

    dagster_run = ops.run_storage.add_run(dagster_run)

    if execution_plan_snapshot and not assets_are_externally_managed(dagster_run):
        log_asset_planned_events(ops, dagster_run, execution_plan_snapshot, asset_graph)

    return dagster_run


def construct_run_with_snapshots(
    ops: "RunInstanceOps",
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
        ensure_persisted_job_snapshot(ops, job_snapshot, parent_job_snapshot)
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
        ensure_persisted_execution_plan_snapshot(
            ops, execution_plan_snapshot, job_snapshot_id, step_keys_to_execute
        )
        if execution_plan_snapshot and job_snapshot_id
        else None
    )

    if execution_plan_snapshot:
        from dagster._core.op_concurrency_limits_counter import (
            compute_run_op_concurrency_info_for_snapshot,
        )

        run_op_concurrency = compute_run_op_concurrency_info_for_snapshot(execution_plan_snapshot)
    else:
        run_op_concurrency = None

    # Calculate partitions_subset for time window partitions
    partitions_subset = None
    if partitions_definition is not None:
        from dagster._core.definitions.partitions.definition.time_window import (
            TimeWindowPartitionsDefinition,
        )

        if isinstance(partitions_definition, TimeWindowPartitionsDefinition):
            # only store the subset of time window partitions, since those can be compressed efficiently
            partition_tag = tags.get(PARTITION_NAME_TAG)
            partition_range_start, partition_range_end = (
                tags.get(ASSET_PARTITION_RANGE_START_TAG),
                tags.get(ASSET_PARTITION_RANGE_END_TAG),
            )

            if partition_tag and (partition_range_start or partition_range_end):
                raise DagsterInvariantViolationError(
                    f"Cannot have {ASSET_PARTITION_RANGE_START_TAG} or"
                    f" {ASSET_PARTITION_RANGE_END_TAG} set along with"
                    f" {PARTITION_NAME_TAG}"
                )
            if partition_tag is not None:
                partition_range_start = partition_tag
                partition_range_end = partition_tag

            if partition_range_start and partition_range_end:
                start_window = partitions_definition.time_window_for_partition_key(
                    partition_range_start
                )
                end_window = partitions_definition.time_window_for_partition_key(
                    partition_range_end
                )
                partitions_subset = partitions_definition.get_partition_subset_in_time_window(
                    TimeWindow(start_window.start, end_window.end)
                ).to_serializable_subset()

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
