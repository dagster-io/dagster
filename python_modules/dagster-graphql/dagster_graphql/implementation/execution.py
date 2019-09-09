from __future__ import absolute_import

from collections import namedtuple

from dagster_graphql.schema.runs import (
    from_compute_log_update,
    from_dagster_event_record,
    from_event_record,
)
from graphql.execution.base import ResolveInfo
from rx import Observable

from dagster import RunConfig, check
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.config import ReexecutionConfig
from dagster.core.serdes import serialize_dagster_namedtuple
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.utils import make_new_run_id

from .fetch_pipelines import get_dauphin_pipeline_from_selector
from .fetch_runs import get_validated_config, validate_config
from .pipeline_run_storage import PipelineRunObservableSubscribe
from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def start_pipeline_execution(graphene_info, execution_params, reexecution_config):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    check.opt_inst_param(reexecution_config, 'reexecution_config', ReexecutionConfig)

    instance = graphene_info.context.instance

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

    run = instance.create_run(
        PipelineRun(
            pipeline_name=dauphin_pipeline.get_dagster_pipeline().name,
            run_id=execution_params.execution_metadata.run_id
            if execution_params.execution_metadata.run_id
            else make_new_run_id(),
            selector=execution_params.selector,
            environment_dict=execution_params.environment_dict,
            mode=execution_params.mode,
            reexecution_config=reexecution_config,
            step_keys_to_execute=execution_params.step_keys,
            tags=execution_params.execution_metadata.tags,
            status=PipelineRunStatus.NOT_STARTED,
        )
    )

    graphene_info.context.execution_manager.execute_pipeline(
        graphene_info.context.get_handle(),
        dauphin_pipeline.get_dagster_pipeline(),
        run,
        raise_on_error=graphene_info.context.raise_on_error,
        instance=instance,
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
    instance = graphene_info.context.instance
    run = instance.get_run(run_id)

    if not run:

        def _get_error_observable(observer):
            observer.on_next(
                graphene_info.schema.type_named('PipelineRunLogsSubscriptionFailure')(
                    missingRunId=run_id, message='Could not load run with id {}'.format(run_id)
                )
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    if not instance.can_watch_events:

        def _get_error_observable(observer):
            observer.on_next(
                graphene_info.schema.type_named('PipelineRunLogsSubscriptionFailure')(
                    message='Event log storage on current DagsterInstance is not watchable.'
                )
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    pipeline = get_dauphin_pipeline_from_selector(graphene_info, run.selector)
    execution_plan = create_execution_plan(
        pipeline.get_dagster_pipeline(), run.environment_dict, RunConfig(mode=run.mode)
    )

    # pylint: disable=E1101
    return Observable.create(
        PipelineRunObservableSubscribe(instance, run_id, after_cursor=after)
    ).map(
        lambda events: graphene_info.schema.type_named('PipelineRunLogsSubscriptionSuccess')(
            runId=run_id,
            messages=[
                from_event_record(graphene_info, event, pipeline, execution_plan)
                for event in events
            ],
        )
    )


def get_compute_log_observable(graphene_info, run_id, step_key, cursor=None):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(run_id, 'run_id')
    check.str_param(step_key, 'step_key')
    check.opt_str_param(cursor, 'cursor')

    return graphene_info.context.compute_log_manager.get_observable(run_id, step_key, cursor).map(
        lambda update: from_compute_log_update(graphene_info, run_id, step_key, update)
    )


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

    run_id = execution_params.execution_metadata.run_id
    run_config = RunConfig(
        run_id=run_id, mode=execution_params.mode, tags=execution_params.execution_metadata.tags
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

    event_logs = []

    def _on_event_record(record):
        if record.is_dagster_event:
            event_logs.append(record)

    graphene_info.context.instance.add_event_listener(run_id, _on_event_record)

    execute_plan(
        execution_plan=execution_plan,
        environment_dict=execution_params.environment_dict,
        run_config=run_config,
        step_keys_to_execute=execution_params.step_keys,
        instance=graphene_info.context.instance,
    )

    def to_graphql_event(event_record):
        return from_dagster_event_record(
            graphene_info, event_record, dauphin_pipeline, execution_plan
        )

    return graphene_info.schema.type_named('ExecutePlanSuccess')(
        pipeline=dauphin_pipeline,
        has_failures=any(
            er
            for er in event_logs
            if er.is_dagster_event and er.dagster_event.event_type == DagsterEventType.STEP_FAILURE
        ),
        step_events=list(map(to_graphql_event, event_logs)),
        raw_event_records=list(map(serialize_dagster_namedtuple, event_logs)),
    )
