from typing import TYPE_CHECKING, Optional, Sequence, Tuple, cast

import dagster._check as check
from dagster._core.errors import DagsterRunNotFoundError
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.host_representation.external import ExternalJob
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import RESUME_RETRY_TAG
from dagster._core.utils import make_new_run_id
from dagster._utils.merger import merge_dicts

from ..external import ensure_valid_config, get_external_execution_plan_or_raise
from ..utils import ExecutionParams

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo


def _get_run(instance: DagsterInstance, run_id: str) -> DagsterRun:
    run = instance.get_run_by_id(run_id)
    if not run:
        raise DagsterRunNotFoundError(invalid_run_id=run_id)
    return cast(DagsterRun, run)


def compute_step_keys_to_execute(
    graphene_info: "ResolveInfo", execution_params: ExecutionParams
) -> Tuple[Optional[Sequence[str]], Optional[KnownExecutionState]]:
    check.inst_param(execution_params, "execution_params", ExecutionParams)

    instance = graphene_info.context.instance

    if not execution_params.step_keys and is_resume_retry(execution_params):
        # Get step keys from parent_run_id if it's a resume/retry
        parent_run_id = check.not_none(execution_params.execution_metadata.parent_run_id)
        parent_run = _get_run(instance, parent_run_id)
        return KnownExecutionState.build_resume_retry_reexecution(
            instance,
            parent_run,
        )
    else:
        known_state = None
        if execution_params.execution_metadata.parent_run_id and execution_params.step_keys:
            parent_run = _get_run(instance, execution_params.execution_metadata.parent_run_id)
            known_state = KnownExecutionState.build_for_reexecution(
                instance,
                parent_run,
            ).update_for_step_selection(execution_params.step_keys)

        return execution_params.step_keys, known_state


def is_resume_retry(execution_params: ExecutionParams) -> bool:
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    return execution_params.execution_metadata.tags.get(RESUME_RETRY_TAG) == "true"


def create_valid_pipeline_run(
    graphene_info: "ResolveInfo",
    external_pipeline: ExternalJob,
    execution_params: ExecutionParams,
) -> DagsterRun:
    ensure_valid_config(external_pipeline, execution_params.run_config)

    step_keys_to_execute, known_state = compute_step_keys_to_execute(
        graphene_info, execution_params
    )

    external_execution_plan = get_external_execution_plan_or_raise(
        graphene_info=graphene_info,
        external_pipeline=external_pipeline,
        run_config=execution_params.run_config,
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
    )
    tags = merge_dicts(external_pipeline.tags, execution_params.execution_metadata.tags)

    dagster_run = graphene_info.context.instance.create_run(
        job_snapshot=external_pipeline.job_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        parent_job_snapshot=external_pipeline.parent_job_snapshot,
        job_name=execution_params.selector.job_name,
        run_id=(
            execution_params.execution_metadata.run_id
            if execution_params.execution_metadata.run_id
            else make_new_run_id()
        ),
        asset_selection=(
            frozenset(execution_params.selector.asset_selection)
            if execution_params.selector.asset_selection
            else None
        ),
        asset_check_selection=(
            frozenset(execution_params.selector.asset_check_selection)
            if execution_params.selector.asset_check_selection is not None
            else None
        ),
        op_selection=execution_params.selector.op_selection,
        resolved_op_selection=(
            frozenset(execution_params.selector.op_selection)
            if execution_params.selector.op_selection
            else None
        ),
        run_config=execution_params.run_config,
        step_keys_to_execute=step_keys_to_execute,
        tags=tags,
        root_run_id=execution_params.execution_metadata.root_run_id,
        parent_run_id=execution_params.execution_metadata.parent_run_id,
        status=DagsterRunStatus.NOT_STARTED,
        external_job_origin=external_pipeline.get_external_origin(),
        job_code_origin=external_pipeline.get_python_origin(),
    )

    return dagster_run
