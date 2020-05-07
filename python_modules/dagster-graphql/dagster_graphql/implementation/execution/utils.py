from dagster_graphql.implementation.utils import ExecutionParams

from dagster import PipelineDefinition, check
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.memoization import get_retry_steps_from_execution_plan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.tags import RESUME_RETRY_TAG
from dagster.core.utils import make_new_run_id


def pipeline_run_args_from_execution_params(execution_params, step_keys_to_execute=None):
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    return dict(
        pipeline_name=execution_params.selector.name,
        run_id=execution_params.execution_metadata.run_id
        if execution_params.execution_metadata.run_id
        else make_new_run_id(),
        solid_subset=execution_params.selector.solid_subset,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
        step_keys_to_execute=step_keys_to_execute or execution_params.step_keys,
        tags=execution_params.execution_metadata.tags,
        root_run_id=execution_params.execution_metadata.root_run_id,
        parent_run_id=execution_params.execution_metadata.parent_run_id,
        status=PipelineRunStatus.NOT_STARTED,
    )


def get_step_keys_to_execute(instance, pipeline_def, execution_params):
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    if not execution_params.step_keys and is_resume_retry(execution_params):
        # Get step keys from parent_run_id if it's a resume/retry
        execution_plan = create_execution_plan(
            pipeline_def, execution_params.environment_dict, mode=execution_params.mode,
        )
        return get_retry_steps_from_execution_plan(
            instance, execution_plan, execution_params.execution_metadata.parent_run_id
        )
    else:
        return execution_params.step_keys


def is_resume_retry(execution_params):
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    return execution_params.execution_metadata.tags.get(RESUME_RETRY_TAG) == 'true'
