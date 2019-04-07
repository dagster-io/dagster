from __future__ import absolute_import
from collections import namedtuple
import sys

from rx import Observable

from graphql.execution.base import ResolveInfo

from dagster import RunConfig, check

from dagster.core.events import DagsterEventType, DagsterEvent
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution import ExecutionSelector, create_execution_plan, execute_plan
from dagster.core.execution_context import ReexecutionConfig, make_new_run_id
from dagster.core.runs import RunStorageMode
from dagster.core.types.evaluator import evaluate_config_value

from dagster.utils.error import serializable_error_info_from_exc_info

from dagster_graphql.schema.config_types import to_dauphin_config_type
from dagster_graphql.schema.runtime_types import to_dauphin_runtime_type

from .execution import DauphinExecutionStep
from .utils import EitherValue, EitherError


def get_pipelines(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return _get_pipelines(graphene_info).value()


def get_pipelines_or_raise(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    return _get_pipelines(graphene_info).value_or_raise()


def _get_pipelines(graphene_info):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)

    def process_pipelines(repository):
        try:
            pipeline_instances = []
            for pipeline_def in repository.get_all_pipelines():
                pipeline_instances.append(graphene_info.schema.type_named('Pipeline')(pipeline_def))
            return graphene_info.schema.type_named('PipelineConnection')(
                nodes=sorted(pipeline_instances, key=lambda pipeline: pipeline.name)
            )
        except DagsterInvalidDefinitionError:
            return EitherError(
                graphene_info.schema.type_named('InvalidDefinitionError')(
                    serializable_error_info_from_exc_info(sys.exc_info())
                )
            )

    repository_or_error = _repository_or_error_from_container(
        graphene_info, graphene_info.context.repository_container
    )
    return repository_or_error.chain(process_pipelines)


def get_pipeline(graphene_info, selector):
    return _get_pipeline(graphene_info, selector).value()


def get_pipeline_or_raise(graphene_info, selector):
    return _get_pipeline(graphene_info, selector).value_or_raise()


def _get_pipeline(graphene_info, selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(selector, 'selector', ExecutionSelector)
    return _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, selector
    )


def get_pipeline_type(graphene_info, pipelineName, typeName):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(pipelineName, 'pipelineName')
    check.str_param(typeName, 'typeName')
    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, ExecutionSelector(pipelineName)
    )
    return pipeline_or_error.chain(
        lambda pipeline: pipeline.get_type(graphene_info, typeName)
    ).value_or_raise()


def _config_type_or_error(graphene_info, dauphin_pipeline, config_type_name):
    pipeline = dauphin_pipeline.get_dagster_pipeline()
    if not pipeline.has_config_type(config_type_name):
        return EitherError(
            graphene_info.schema.type_named('ConfigTypeNotFoundError')(
                pipeline=pipeline, config_type_name=config_type_name
            )
        )
    else:
        dauphin_config_type = to_dauphin_config_type(pipeline.config_type_named(config_type_name))
        return EitherValue(dauphin_config_type)


def get_config_type(graphene_info, pipeline_name, type_name):
    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, ExecutionSelector(pipeline_name)
    )

    return pipeline_or_error.chain(
        lambda pipeline: _config_type_or_error(graphene_info, pipeline, type_name)
    ).value()


def _runtime_type_or_error(graphene_info, dauphin_pipeline, runtime_type_name):
    pipeline = dauphin_pipeline.get_dagster_pipeline()
    if not pipeline.has_runtime_type(runtime_type_name):
        return EitherError(
            graphene_info.schema.type_named('RuntimeTypeNotFoundError')(
                pipeline=pipeline, runtime_type_name=runtime_type_name
            )
        )
    else:
        dauphin_runtime_type = to_dauphin_runtime_type(
            pipeline.runtime_type_named(runtime_type_name)
        )
        return EitherValue(dauphin_runtime_type)


def get_runtime_type(graphene_info, pipeline_name, type_name):
    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, ExecutionSelector(pipeline_name)
    )

    return pipeline_or_error.chain(
        lambda pipeline: _runtime_type_or_error(graphene_info, pipeline, type_name)
    ).value()


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

    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, selector
    )
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

    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, selector
    )
    return pipeline_or_error.chain(create_plan).value()


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
                throw_on_user_error=graphene_info.context.throw_on_user_error,
            )

            return graphene_info.schema.type_named('StartPipelineExecutionSuccess')(
                run=graphene_info.schema.type_named('PipelineRun')(run)
            )

        config_or_error = _config_or_error_from_pipeline(graphene_info, pipeline, environment_dict)
        return config_or_error.chain(_start_execution)

    pipeline_or_error = _pipeline_or_error_from_container(
        graphene_info, graphene_info.context.repository_container, selector
    )
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
        _pipeline_or_error_from_container(
            graphene_info, graphene_info.context.repository_container, run.selector
        )
        .chain(get_observable)
        .value_or_raise()
    )


def _repository_or_error_from_container(graphene_info, container):
    error = container.error
    if error is not None:
        return EitherError(
            graphene_info.schema.type_named('PythonError')(
                serializable_error_info_from_exc_info(error)
            )
        )
    try:
        return EitherValue(container.repository)
    except Exception:  # pylint: disable=broad-except
        return EitherError(
            graphene_info.schema.type_named('PythonError')(
                serializable_error_info_from_exc_info(sys.exc_info())
            )
        )


def _pipeline_or_error_from_repository(graphene_info, repository, selector):
    if not repository.has_pipeline(selector.name):
        return EitherError(
            graphene_info.schema.type_named('PipelineNotFoundError')(pipeline_name=selector.name)
        )
    else:
        orig_pipeline = repository.get_pipeline(selector.name)
        if selector.solid_subset:
            for solid_name in selector.solid_subset:
                if not orig_pipeline.has_solid(solid_name):
                    return EitherError(
                        graphene_info.schema.type_named('SolidNotFoundError')(solid_name=solid_name)
                    )
        pipeline = orig_pipeline.build_sub_pipeline(selector.solid_subset)

        return EitherValue(graphene_info.schema.type_named('Pipeline')(pipeline))


def _pipeline_or_error_from_container(graphene_info, container, selector):
    return _repository_or_error_from_container(graphene_info, container).chain(
        lambda repository: _pipeline_or_error_from_repository(graphene_info, repository, selector)
    )


def _config_or_error_from_pipeline(graphene_info, pipeline, env_config):
    pipeline_env_type = pipeline.get_dagster_pipeline().environment_type
    validated_config = evaluate_config_value(pipeline_env_type, env_config)

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
        _pipeline_or_error_from_container(
            graphene_info,
            graphene_info.context.repository_container,
            ExecutionSelector(pipeline_name),
        )
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
    run_storage_mode = (
        None if 'storage' in execute_plan_args.environment_dict else RunStorageMode.FILESYSTEM
    )

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

    run_config = RunConfig(run_id=run_id, tags=tags, storage_mode=run_storage_mode)

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


def _type_of(args, type_name):
    return args.graphene_info.schema.type_named(type_name)


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
