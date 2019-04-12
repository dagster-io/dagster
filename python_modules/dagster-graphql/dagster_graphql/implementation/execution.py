from __future__ import absolute_import
from collections import namedtuple

from rx import Observable

from graphql.execution.base import ResolveInfo

from dagster import RunConfig, check

from dagster.core.events import DagsterEventType, DagsterEvent
from dagster.core.execution import ExecutionSelector, create_execution_plan, execute_plan
from dagster.core.execution_context import ReexecutionConfig, make_new_run_id


from dagster_graphql.schema.execution import DauphinExecutionStep

from .fetch_pipelines import _pipeline_or_error_from_container
from .fetch_runs import _config_or_error_from_pipeline


def start_pipeline_execution(
    graphene_info,
    selector,
    environment_dict,
    step_keys_to_execute,
    reexecution_config,
    graphql_execution_metadata,
):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)
    check.opt_inst_param(reexecution_config, 'reexecution_config', ReexecutionConfig)
    graphql_execution_metadata = check.opt_dict_param(
        graphql_execution_metadata, 'graphql_execution_metadata'
    )

    run_id = graphql_execution_metadata.get('runId')

    pipeline_run_storage = graphene_info.context.pipeline_runs

    def get_config_and_start_execution(pipeline):
        def _start_execution(validated_config_either):
            new_run_id = run_id if run_id else make_new_run_id()
            execution_plan = create_execution_plan(
                pipeline.get_dagster_pipeline(), validated_config_either.value
            )
            run = pipeline_run_storage.create_run(
                new_run_id,
                selector,
                environment_dict,
                execution_plan,
                reexecution_config,
                step_keys_to_execute,
            )
            pipeline_run_storage.add_run(run)

            if step_keys_to_execute:
                for step_key in step_keys_to_execute:
                    if not execution_plan.has_step(step_key):
                        return graphene_info.schema.type_named('InvalidStepError')(
                            invalid_step_key=step_key
                        )

            if reexecution_config and reexecution_config.step_output_handles:
                for step_output_handle in reexecution_config.step_output_handles:
                    if not execution_plan.has_step(step_output_handle.step_key):
                        return graphene_info.schema.type_named('InvalidStepError')(
                            invalid_step_key=step_output_handle.step_key
                        )

                    step = execution_plan.get_step_by_key(step_output_handle.step_key)

                    if not step.has_step_output(step_output_handle.output_name):
                        return graphene_info.schema.type_named('InvalidOutputError')(
                            step_key=step_output_handle.step_key,
                            invalid_output_name=step_output_handle.output_name,
                        )

            graphene_info.context.execution_manager.execute_pipeline(
                graphene_info.context.repository_container,
                pipeline.get_dagster_pipeline(),
                run,
                raise_on_error=graphene_info.context.raise_on_error,
            )

            return graphene_info.schema.type_named('StartPipelineExecutionSuccess')(
                run=graphene_info.schema.type_named('PipelineRun')(run)
            )

        config_or_error = _config_or_error_from_pipeline(graphene_info, pipeline, environment_dict)
        return config_or_error.chain(_start_execution)

    pipeline_or_error = _pipeline_or_error_from_container(graphene_info, selector)
    return pipeline_or_error.chain(get_config_and_start_execution).value()


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
        pipeline_run_event_type = graphene_info.schema.type_named('PipelineRunEvent')
        return run.observable_after_cursor(after).map(
            lambda events: graphene_info.schema.type_named('PipelineRunLogsSubscriptionSuccess')(
                messages=[
                    pipeline_run_event_type.from_dagster_event(
                        graphene_info, event, pipeline, run.execution_plan
                    )
                    for event in events
                ]
            )
        )

    return (
        _pipeline_or_error_from_container(graphene_info, run.selector)
        .chain(get_observable)
        .value_or_raise()
    )


ExecutePlanArgs = namedtuple(
    'ExecutePlanArgs', 'graphene_info pipeline_name environment_dict execution_metadata step_keys'
)


def do_execute_plan(graphene_info, pipeline_name, environment_dict, execution_metadata, step_keys):
    execute_plan_args = ExecutePlanArgs(
        graphene_info=graphene_info,
        pipeline_name=pipeline_name,
        environment_dict=environment_dict,
        execution_metadata=execution_metadata,
        step_keys=step_keys,
    )
    return (
        _pipeline_or_error_from_container(graphene_info, ExecutionSelector(pipeline_name))
        .chain(
            lambda dauphin_pipeline: _execute_plan_resolve_config(
                execute_plan_args, dauphin_pipeline
            )
        )
        .value()
    )


def _execute_plan_resolve_config(execution_subplan_args, dauphin_pipeline):
    return (
        _config_or_error_from_pipeline(
            execution_subplan_args.graphene_info,
            dauphin_pipeline,
            execution_subplan_args.environment_dict,
        )
        .chain(
            lambda evaluate_env_config_result: _execute_plan_chain_actual_execute_or_error(
                execution_subplan_args, dauphin_pipeline, evaluate_env_config_result
            )
        )
        .value()
    )


def tags_from_graphql_execution_metadata(graphql_execution_metadata):
    tags = {}
    if 'tags' in graphql_execution_metadata:
        for tag in graphql_execution_metadata['tags']:
            tags[tag['key']] = tag['value']
    return tags


def _execute_plan_chain_actual_execute_or_error(
    execute_plan_args, dauphin_pipeline, _evaluate_env_config_result
):
    graphql_execution_metadata = execute_plan_args.execution_metadata
    run_id = graphql_execution_metadata.get('runId')
    tags = tags_from_graphql_execution_metadata(graphql_execution_metadata)
    execution_plan = create_execution_plan(
        pipeline=dauphin_pipeline.get_dagster_pipeline(),
        environment_dict=execute_plan_args.environment_dict,
    )

    if execute_plan_args.step_keys:
        for step_key in execute_plan_args.step_keys:
            if not execution_plan.has_step(step_key):
                return execute_plan_args.graphene_info.schema.type_named('InvalidStepError')(
                    invalid_step_key=step_key
                )

    run_config = RunConfig(run_id=run_id, tags=tags)

    step_events = list(
        execute_plan(
            execution_plan=execution_plan,
            environment_dict=execute_plan_args.environment_dict,
            run_config=run_config,
            step_keys_to_execute=execute_plan_args.step_keys,
        )
    )

    return execute_plan_args.graphene_info.schema.type_named('ExecutePlanSuccess')(
        pipeline=dauphin_pipeline,
        has_failures=any(
            se for se in step_events if se.event_type == DagsterEventType.STEP_FAILURE
        ),
        step_events=list(
            map(lambda se: _create_dauphin_step_event(execution_plan, se), step_events)
        ),
    )


def _create_dauphin_step_event(execution_plan, step_event):
    from dagster_graphql.schema.runs import (
        DauphinExecutionStepOutputEvent,
        DauphinExecutionStepSuccessEvent,
        DauphinExecutionStepFailureEvent,
        DauphinExecutionStepStartEvent,
        DauphinExecutionStepSkippedEvent,
        DauphinStepMaterializationEvent,
    )

    check.inst_param(step_event, 'step_event', DagsterEvent)

    step = execution_plan.get_step_by_key(step_event.step_key)

    if step_event.event_type == DagsterEventType.STEP_START:
        return DauphinExecutionStepStartEvent(step=DauphinExecutionStep(execution_plan, step))
    if step_event.event_type == DagsterEventType.STEP_SKIPPED:
        return DauphinExecutionStepSkippedEvent(step=DauphinExecutionStep(execution_plan, step))
    elif step_event.event_type == DagsterEventType.STEP_OUTPUT:
        return DauphinExecutionStepOutputEvent(
            step=DauphinExecutionStep(execution_plan, step),
            output_name=step_event.step_output_data.output_name,
            storage_object_id=step_event.step_output_data.storage_object_id,
            storage_mode=step_event.step_output_data.storage_mode,
            value_repr=step_event.step_output_data.value_repr,
        )
    elif step_event.event_type == DagsterEventType.STEP_FAILURE:
        return DauphinExecutionStepFailureEvent(
            step=DauphinExecutionStep(execution_plan, step),
            error=step_event.step_failure_data.error,
        )
    elif step_event.event_type == DagsterEventType.STEP_SUCCESS:
        return DauphinExecutionStepSuccessEvent(step=DauphinExecutionStep(execution_plan, step))
    elif step_event.event_type == DagsterEventType.STEP_MATERIALIZATION:
        return DauphinStepMaterializationEvent(
            file_name=step_event.step_materialization_data.name,
            file_location=step_event.step_materialization_data.path,
            step=DauphinExecutionStep(execution_plan, step),
        )

    else:
        check.failed('Unsupported step event: {step_event}'.format(step_event=step_event))
