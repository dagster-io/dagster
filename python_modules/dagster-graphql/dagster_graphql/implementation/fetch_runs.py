from graphql.execution.base import ResolveInfo

from dagster import check, RunConfig
from dagster.core.definitions import create_environment_schema
from dagster.core.execution.api import ExecutionSelector, create_execution_plan
from dagster.core.types.evaluator import evaluate_config

from .fetch_pipelines import get_dauphin_pipeline_from_selector
from .utils import capture_dauphin_error, UserFacingGraphQLError


def validate_config(graphene_info, dauphin_pipeline, env_config, mode):
    get_validated_config(graphene_info, dauphin_pipeline, env_config, mode)


def get_validated_config(graphene_info, dauphin_pipeline, environment_dict, mode):
    check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    check.str_param(mode, 'mode')

    pipeline = dauphin_pipeline.get_dagster_pipeline()

    environment_schema = create_environment_schema(pipeline, mode)

    validated_config = evaluate_config(
        environment_schema.environment_type, environment_dict, pipeline
    )

    if not validated_config.success:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('PipelineConfigValidationInvalid')(
                pipeline=dauphin_pipeline,
                errors=[
                    graphene_info.schema.type_named(
                        'PipelineConfigValidationError'
                    ).from_dagster_error(graphene_info, err)
                    for err in validated_config.errors
                ],
            )
        )

    return validated_config


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


@capture_dauphin_error
def validate_pipeline_config(graphene_info, selector, environment_dict, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_str_param(mode, 'mode')

    dauphin_pipeline = get_dauphin_pipeline_from_selector(graphene_info, selector)
    get_validated_config(graphene_info, dauphin_pipeline, environment_dict, mode)
    return graphene_info.schema.type_named('PipelineConfigValidationValid')(dauphin_pipeline)


@capture_dauphin_error
def get_execution_plan(graphene_info, selector, environment_dict, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_str_param(mode, 'mode')

    dauphin_pipeline = get_dauphin_pipeline_from_selector(graphene_info, selector)
    get_validated_config(graphene_info, dauphin_pipeline, environment_dict, mode)
    return graphene_info.schema.type_named('ExecutionPlan')(
        dauphin_pipeline,
        create_execution_plan(
            dauphin_pipeline.get_dagster_pipeline(), environment_dict, RunConfig(mode=mode)
        ),
    )
