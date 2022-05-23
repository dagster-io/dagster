from graphql.execution.base import ResolveInfo

import dagster._check as check
from dagster.core.execution.plan.resume_retry import get_retry_steps_from_parent_run
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.tags import RESUME_RETRY_TAG
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts

from ...schema.errors import GrapheneNoModeProvidedError
from ..external import ensure_valid_config, get_external_execution_plan_or_raise
from ..utils import ExecutionParams, UserFacingGraphQLError


def compute_step_keys_to_execute(graphene_info, execution_params):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(execution_params, "execution_params", ExecutionParams)

    instance = graphene_info.context.instance

    if not execution_params.step_keys and is_resume_retry(execution_params):
        # Get step keys from parent_run_id if it's a resume/retry
        return get_retry_steps_from_parent_run(
            instance, execution_params.execution_metadata.parent_run_id
        )
    else:
        known_state = None
        if execution_params.execution_metadata.parent_run_id and execution_params.step_keys:
            known_state = KnownExecutionState.for_reexecution(
                instance.all_logs(execution_params.execution_metadata.parent_run_id),
                execution_params.step_keys,
            )

        return execution_params.step_keys, known_state


def is_resume_retry(execution_params):
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    return execution_params.execution_metadata.tags.get(RESUME_RETRY_TAG) == "true"


def create_valid_pipeline_run(graphene_info, external_pipeline, execution_params):
    if execution_params.mode is None and len(external_pipeline.available_modes) > 1:
        raise UserFacingGraphQLError(
            GrapheneNoModeProvidedError(external_pipeline.name, external_pipeline.available_modes)
        )
    elif execution_params.mode is None and len(external_pipeline.available_modes) == 1:
        mode = external_pipeline.available_modes[0]

    else:
        mode = execution_params.mode

    ensure_valid_config(external_pipeline, mode, execution_params.run_config)

    step_keys_to_execute, known_state = compute_step_keys_to_execute(
        graphene_info, execution_params
    )

    external_execution_plan = get_external_execution_plan_or_raise(
        graphene_info=graphene_info,
        external_pipeline=external_pipeline,
        mode=mode,
        run_config=execution_params.run_config,
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
    )
    tags = merge_dicts(external_pipeline.tags, execution_params.execution_metadata.tags)

    pipeline_run = graphene_info.context.instance.create_run(
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        pipeline_name=execution_params.selector.pipeline_name,
        run_id=execution_params.execution_metadata.run_id
        if execution_params.execution_metadata.run_id
        else make_new_run_id(),
        asset_selection=frozenset(execution_params.selector.asset_selection)
        if execution_params.selector.asset_selection
        else None,
        solid_selection=execution_params.selector.solid_selection,
        solids_to_execute=frozenset(execution_params.selector.solid_selection)
        if execution_params.selector.solid_selection
        else None,
        run_config=execution_params.run_config,
        mode=mode,
        step_keys_to_execute=step_keys_to_execute,
        tags=tags,
        root_run_id=execution_params.execution_metadata.root_run_id,
        parent_run_id=execution_params.execution_metadata.parent_run_id,
        status=PipelineRunStatus.NOT_STARTED,
        external_pipeline_origin=external_pipeline.get_external_origin(),
        pipeline_code_origin=external_pipeline.get_python_origin(),
    )

    return pipeline_run
