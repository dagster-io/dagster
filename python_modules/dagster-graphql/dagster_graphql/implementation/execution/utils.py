from dagster_graphql.implementation.utils import ExecutionParams

from dagster import PipelineDefinition, RunConfig, check
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.memoization import get_retry_steps_from_execution_plan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.utils import make_new_run_id

from ..utils import UserFacingGraphQLError


def pipeline_run_from_execution_params(execution_params, step_keys_to_execute=None):
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    return PipelineRun(
        pipeline_name=execution_params.selector.name,
        run_id=execution_params.execution_metadata.run_id
        if execution_params.execution_metadata.run_id
        else make_new_run_id(),
        selector=execution_params.selector,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
        step_keys_to_execute=step_keys_to_execute or execution_params.step_keys,
        tags=execution_params.execution_metadata.tags,
        root_run_id=(
            execution_params.execution_metadata.root_run_id or execution_params.previous_run_id
        ),
        parent_run_id=(
            execution_params.execution_metadata.parent_run_id or execution_params.previous_run_id
        ),
        previous_run_id=execution_params.previous_run_id,
        status=PipelineRunStatus.NOT_STARTED,
    )


def _create_pipeline_run(instance, pipeline_def, execution_params):
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    return pipeline_run_from_execution_params(
        execution_params, get_step_keys_to_execute(instance, pipeline_def, execution_params)
    )


def get_step_keys_to_execute(instance, pipeline_def, execution_params):
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    if not execution_params.step_keys and execution_params.previous_run_id:
        execution_plan = create_execution_plan(
            pipeline_def,
            execution_params.environment_dict,
            run_config=RunConfig(
                mode=execution_params.mode,
                previous_run_id=execution_params.previous_run_id,
                tags=execution_params.execution_metadata.tags,
            ),
        )
        return get_retry_steps_from_execution_plan(
            instance, execution_plan, execution_params.previous_run_id
        )
    else:
        return execution_params.step_keys


def _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan):
    if execution_params.step_keys:
        for step_key in execution_params.step_keys:
            if not execution_plan.has_step(step_key):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidStepError')(invalid_step_key=step_key)
                )
