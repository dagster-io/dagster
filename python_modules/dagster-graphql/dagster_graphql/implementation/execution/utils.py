from dagster_graphql.client.util import pipeline_run_from_execution_params

from dagster import RunConfig
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.memoization import get_retry_steps_from_execution_plan

from ..utils import UserFacingGraphQLError


def _create_pipeline_run(instance, pipeline, execution_params):
    step_keys_to_execute = execution_params.step_keys
    if not execution_params.step_keys and execution_params.previous_run_id:
        execution_plan = create_execution_plan(
            pipeline,
            execution_params.environment_dict,
            run_config=RunConfig(
                mode=execution_params.mode,
                previous_run_id=execution_params.previous_run_id,
                tags=execution_params.execution_metadata.tags,
            ),
        )
        step_keys_to_execute = get_retry_steps_from_execution_plan(instance, execution_plan)
    return pipeline_run_from_execution_params(execution_params, step_keys_to_execute)


def _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan):
    if execution_params.step_keys:
        for step_key in execution_params.step_keys:
            if not execution_plan.has_step(step_key):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidStepError')(invalid_step_key=step_key)
                )
