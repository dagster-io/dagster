from graphql.execution.base import ResolveInfo

from dagster import RunConfig, check
from dagster.core.definitions import create_environment_schema
from dagster.core.definitions.pipeline import ExecutionSelector, PipelineRunsSelector
from dagster.core.execution.api import create_execution_plan
from dagster.core.types.evaluator import evaluate_config

from .fetch_pipelines import (
    get_dauphin_pipeline_from_selector_or_raise,
    get_dauphin_pipeline_reference_from_selector,
)
from .utils import UserFacingGraphQLError, capture_dauphin_error


def validate_config(graphene_info, dauphin_pipeline, env_config, mode):
    get_validated_config(graphene_info, dauphin_pipeline, env_config, mode)


def get_validated_config(graphene_info, dauphin_pipeline, environment_dict, mode):
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


def get_run(graphene_info, run_id):
    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)
    if not run:
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)
    else:
        return graphene_info.schema.type_named('PipelineRun')(run)


def get_runs(graphene_info, selector):
    check.inst_param(selector, 'selector', PipelineRunsSelector)
    instance = graphene_info.context.instance

    runs = []
    page_opts = dict(cursor=selector.cursor, limit=selector.limit)

    if selector.run_id:
        run = instance.get_run_by_id(selector.run_id)
        if run:
            runs = [run]
    elif selector.pipeline:
        runs = instance.get_runs_with_pipeline_name(selector.pipeline, **page_opts)
    elif selector.tag_key:
        runs = instance.get_runs_with_matching_tag(
            selector.tag_key, selector.tag_value, **page_opts
        )
    elif selector.status:
        runs = instance.get_runs_with_status(selector.status, **page_opts)
    else:
        runs = instance.all_runs(**page_opts)

    return [graphene_info.schema.type_named('PipelineRun')(run) for run in runs]


@capture_dauphin_error
def validate_pipeline_config(graphene_info, selector, environment_dict, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_str_param(mode, 'mode')

    dauphin_pipeline = get_dauphin_pipeline_from_selector_or_raise(graphene_info, selector)
    get_validated_config(graphene_info, dauphin_pipeline, environment_dict, mode)
    return graphene_info.schema.type_named('PipelineConfigValidationValid')(dauphin_pipeline)


@capture_dauphin_error
def get_execution_plan(graphene_info, selector, environment_dict, mode):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_str_param(mode, 'mode')

    dauphin_pipeline = get_dauphin_pipeline_reference_from_selector(graphene_info, selector)
    get_validated_config(graphene_info, dauphin_pipeline, environment_dict, mode)
    return graphene_info.schema.type_named('ExecutionPlan')(
        dauphin_pipeline,
        create_execution_plan(
            dauphin_pipeline.get_dagster_pipeline(), environment_dict, RunConfig(mode=mode)
        ),
    )
