from __future__ import absolute_import
from collections import namedtuple

from rx import Observable

from graphql.execution.base import ResolveInfo

from dagster import RunConfig, check

from dagster.core.events import DagsterEventType
from dagster.core.execution.api import ExecutionSelector, create_execution_plan, execute_plan
from dagster.core.execution.config import ReexecutionConfig
from dagster.core.utils import make_new_run_id

from dagster_graphql.schema.runs import from_event_record, from_dagster_event_record

from .fetch_runs import get_validated_config, validate_config
from .fetch_pipelines import get_dauphin_pipeline_from_selector
from .utils import capture_dauphin_error, UserFacingGraphQLError


@capture_dauphin_error
def start_pipeline_execution(graphene_info, execution_params, reexecution_config):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    check.opt_inst_param(reexecution_config, 'reexecution_config', ReexecutionConfig)

    pipeline_run_storage = graphene_info.context.pipeline_runs

    dauphin_pipeline = get_dauphin_pipeline_from_selector(graphene_info, execution_params.selector)

    get_validated_config(
        graphene_info,
        dauphin_pipeline,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
    )

    execution_plan = create_execution_plan(
        dauphin_pipeline.get_dagster_pipeline(),
        execution_params.environment_dict,
        run_config=RunConfig(mode=execution_params.mode),
    )

    _check_start_pipeline_execution_errors(
        graphene_info, execution_params, execution_plan, reexecution_config
    )

    run = pipeline_run_storage.create_run(
        run_id=execution_params.execution_metadata.run_id
        if execution_params.execution_metadata.run_id
        else make_new_run_id(),
        selector=execution_params.selector,
        env_config=execution_params.environment_dict,
        mode=execution_params.mode,
        reexecution_config=reexecution_config,
        step_keys_to_execute=execution_params.step_keys,
    )
    pipeline_run_storage.add_run(run)

    graphene_info.context.execution_manager.execute_pipeline(
        graphene_info.context.get_handle(),
        dauphin_pipeline.get_dagster_pipeline(),
        run,
        raise_on_error=graphene_info.context.raise_on_error,
    )

    return graphene_info.schema.type_named('StartPipelineExecutionSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )


def _check_start_pipeline_execution_errors(
    graphene_info, execution_params, execution_plan, reexecution_config
):
    if execution_params.step_keys:
        for step_key in execution_params.step_keys:
            if not execution_plan.has_step(step_key):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidStepError')(invalid_step_key=step_key)
                )

    if reexecution_config and reexecution_config.step_output_handles:
        for step_output_handle in reexecution_config.step_output_handles:
            if not execution_plan.has_step(step_output_handle.step_key):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidStepError')(
                        invalid_step_key=step_output_handle.step_key
                    )
                )

            step = execution_plan.get_step_by_key(step_output_handle.step_key)

            if not step.has_step_output(step_output_handle.output_name):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidOutputError')(
                        step_key=step_output_handle.step_key,
                        invalid_output_name=step_output_handle.output_name,
                    )
                )


def get_pipeline_run_observable(graphene_info, run_id, after=None):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(run_id, 'run_id')
    check.opt_str_param(after, 'after')
    pipeline_run_storage = graphene_info.context.pipeline_runs
    run = pipeline_run_storage.get_run_by_id(run_id)

    if not run:

        def _get_error_observable(observer):
            observer.on_next(
                graphene_info.schema.type_named('PipelineRunLogsSubscriptionMissingRunIdFailure')(
                    missingRunId=run_id
                )
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    def get_observable(pipeline):
        execution_plan = create_execution_plan(
            pipeline.get_dagster_pipeline(), run.config, RunConfig(mode=run.mode)
        )
        return run.observable_after_cursor(after).map(
            lambda events: graphene_info.schema.type_named('PipelineRunLogsSubscriptionSuccess')(
                runId=run_id,
                messages=[
                    from_event_record(graphene_info, event, pipeline, execution_plan)
                    for event in events
                ],
            )
        )

    return get_observable(get_dauphin_pipeline_from_selector(graphene_info, run.selector))


class ExecutionParams(
    namedtuple('_ExecutionParams', 'selector environment_dict mode execution_metadata step_keys')
):
    def __new__(cls, selector, environment_dict, mode, execution_metadata, step_keys):
        check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
        check.opt_list_param(step_keys, 'step_keys', of_type=str)

        return super(ExecutionParams, cls).__new__(
            cls,
            selector=check.inst_param(selector, 'selector', ExecutionSelector),
            environment_dict=environment_dict,
            mode=check.str_param(mode, 'mode'),
            execution_metadata=check.inst_param(
                execution_metadata, 'execution_metadata', ExecutionMetadata
            ),
            step_keys=step_keys,
        )


class ExecutionMetadata(namedtuple('_ExecutionMetadata', 'run_id tags')):
    def __new__(cls, run_id, tags):
        return super(ExecutionMetadata, cls).__new__(
            cls,
            check.opt_str_param(run_id, 'run_id'),
            check.dict_param(tags, 'tags', key_type=str, value_type=str),
        )


@capture_dauphin_error
def do_execute_plan(graphene_info, execution_params):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    return _execute_plan_resolve_config(
        graphene_info,
        execution_params,
        get_dauphin_pipeline_from_selector(graphene_info, execution_params.selector),
    )


def _execute_plan_resolve_config(graphene_info, execution_params, dauphin_pipeline):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    validate_config(
        graphene_info, dauphin_pipeline, execution_params.environment_dict, execution_params.mode
    )
    return _do_execute_plan(graphene_info, execution_params, dauphin_pipeline)


def _do_execute_plan(graphene_info, execution_params, dauphin_pipeline):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    event_records = []

    run_config = RunConfig(
        run_id=execution_params.execution_metadata.run_id,
        mode=execution_params.mode,
        tags=execution_params.execution_metadata.tags,
        event_callback=event_records.append,
    )

    execution_plan = create_execution_plan(
        pipeline=dauphin_pipeline.get_dagster_pipeline(),
        environment_dict=execution_params.environment_dict,
        run_config=run_config,
    )

    if execution_params.step_keys:
        for step_key in execution_params.step_keys:
            if not execution_plan.has_step(step_key):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidStepError')(invalid_step_key=step_key)
                )

    execute_plan(
        execution_plan=execution_plan,
        environment_dict=execution_params.environment_dict,
        run_config=run_config,
        step_keys_to_execute=execution_params.step_keys,
    )

    def to_graphql_event(event_record):
        return from_dagster_event_record(
            graphene_info, event_record, dauphin_pipeline, execution_plan
        )

    return graphene_info.schema.type_named('ExecutePlanSuccess')(
        pipeline=dauphin_pipeline,
        has_failures=any(
            er
            for er in event_records
            if er.is_dagster_event and er.dagster_event.event_type == DagsterEventType.STEP_FAILURE
        ),
        step_events=list(
            map(to_graphql_event, filter(lambda er: er.is_dagster_event, event_records))
        ),
    )
