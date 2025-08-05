from collections.abc import Mapping, Set
from typing import TYPE_CHECKING, Any, Optional

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterInvalidSubsetError, DagsterInvariantViolationError
from dagster._core.instance.runs.run_creation import create_run
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import (
    ASSET_RESUME_RETRY_TAG,
    BACKFILL_ID_TAG,
    BACKFILL_TAGS,
    PARENT_RUN_ID_TAG,
    RESUME_RETRY_TAG,
    ROOT_RUN_ID_TAG,
    TAGS_TO_MAYBE_OMIT_ON_RETRY,
)
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
    from dagster._core.definitions.utils import EntityKey
    from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
    from dagster._core.instance.runs.run_instance_ops import RunInstanceOps
    from dagster._core.remote_representation import CodeLocation, RemoteJob
    from dagster._core.snap import ExecutionPlanSnapshot


def create_reexecuted_run(
    ops: "RunInstanceOps",
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
    from dagster._core.remote_representation import CodeLocation, RemoteJob

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
            backfill = ops.get_backfill(parent_run.tags[BACKFILL_ID_TAG])
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
            ops.as_dynamic_partitions_store(),
            parent_run=parent_run,
        )
        tags[RESUME_RETRY_TAG] = "true"

        if not step_keys_to_execute:
            raise DagsterInvalidSubsetError("No steps needed to be retried in the failed run.")
    elif strategy == ReexecutionStrategy.FROM_ASSET_FAILURE:
        parent_snapshot_id = check.not_none(parent_run.execution_plan_snapshot_id)
        snapshot = ops.get_execution_plan_snapshot(parent_snapshot_id)
        skipped_asset_keys, skipped_asset_check_keys = get_keys_to_reexecute(
            ops, parent_run_id, snapshot
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
        instance=ops.as_dynamic_partitions_store(),
    )

    return create_run(
        ops,
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


def get_keys_to_reexecute(
    ops: "RunInstanceOps",
    run_id: str,
    execution_plan_snapshot: "ExecutionPlanSnapshot",
) -> tuple[Set[AssetKey], Set["AssetCheckKey"]]:
    """For a given run_id, return the subset of asset keys and asset check keys that should be
    re-executed for a run when in the `FROM_ASSET_FAILURE` mode.

    An asset key will be included if it was planned but not materialized in the original run,
    or if any of its planned blocking asset checks were planned but not executed, or failed.

    An asset check key will be included if it was planned but not executed in the original run,
    or if it was associated with an asset that will be re-executed.
    """
    from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
    from dagster._core.definitions.events import AssetKey
    from dagster._core.events import AssetCheckEvaluation, DagsterEventType, StepMaterializationData

    # figure out the set of assets that were materialized and checks that successfully executed
    logs = ops.all_logs(
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
