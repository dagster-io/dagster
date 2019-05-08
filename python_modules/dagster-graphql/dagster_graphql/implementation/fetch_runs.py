from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions import create_environment_schema
from dagster.core.execution import ExecutionSelector, create_execution_plan
from dagster.core.types.evaluator import evaluate_config_value

from .either import EitherError, EitherValue
from .fetch_pipelines import _pipeline_or_error_from_container


def _config_or_error_from_pipeline(graphene_info, pipeline, env_config):
    configuration_schema = create_environment_schema(pipeline.get_dagster_pipeline())

    validated_config = evaluate_config_value(configuration_schema.environment_type, env_config)

    if not validated_config.success:
        return EitherError(
            graphene_info.schema.type_named('PipelineConfigValidationInvalid')(
                pipeline=pipeline,
                errors=[
                    graphene_info.schema.type_named(
                        'PipelineConfigValidationError'
                    ).from_dagster_error(graphene_info, err)
                    for err in validated_config.errors
                ],
            )
        )
    else:
        return EitherValue(validated_config)


def get_run(graphene_info, runId):
    pipeline_run_storage = graphene_info.context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(runId)
    if not run:
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(runId)
    else:
        return graphene_info.schema.type_named('PipelineRun')(run)


def get_runs(graphene_info):
    pipeline_run_storage = graphene_info.context.pipeline_runs
    return [
        graphene_info.schema.type_named('PipelineRun')(run)
        for run in pipeline_run_storage.all_runs()
    ]


def validate_pipeline_config(graphene_info, selector, config):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    def do_validation(pipeline):
        config_or_error = _config_or_error_from_pipeline(graphene_info, pipeline, config)
        return config_or_error.chain(
            lambda config: graphene_info.schema.type_named('PipelineConfigValidationValid')(
                pipeline
            )
        )

    pipeline_or_error = _pipeline_or_error_from_container(graphene_info, selector)
    return pipeline_or_error.chain(do_validation).value()


def get_execution_plan(graphene_info, selector, config):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)

    def create_plan(pipeline):
        config_or_error = _config_or_error_from_pipeline(graphene_info, pipeline, config)
        return config_or_error.chain(
            lambda evaluate_value_result: graphene_info.schema.type_named('ExecutionPlan')(
                pipeline,
                create_execution_plan(pipeline.get_dagster_pipeline(), evaluate_value_result.value),
            )
        )

    pipeline_or_error = _pipeline_or_error_from_container(graphene_info, selector)
    return pipeline_or_error.chain(create_plan).value()
