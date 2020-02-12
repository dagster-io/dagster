from __future__ import absolute_import

from dagster_graphql.client.util import pipeline_run_from_execution_params
from dagster_graphql.schema.runs import (
    from_compute_log_file,
    from_dagster_event_record,
    from_event_record,
)
from graphql.execution.base import ResolveInfo
from rx import Observable

from dagster import RunConfig, check
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.memoization import get_retry_steps_from_execution_plan
from dagster.core.serdes import serialize_dagster_namedtuple
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.utils import merge_dicts

from .fetch_pipelines import (
    get_dauphin_pipeline_from_selector_or_raise,
    get_dauphin_pipeline_reference_from_selector,
)
from .fetch_runs import get_validated_config
from .fetch_schedules import get_dagster_schedule_def
from .pipeline_run_storage import PipelineRunObservableSubscribe
from .utils import ExecutionParams, UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def cancel_pipeline_execution(graphene_info, run_id):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(run_id, 'run_id')

    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)

    if not run:
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)

    dauphin_run = graphene_info.schema.type_named('PipelineRun')(run)

    if run.status != PipelineRunStatus.STARTED:
        return graphene_info.schema.type_named('CancelPipelineExecutionFailure')(
            run=dauphin_run,
            message='Run {run_id} is not in a started state. Current status is {status}'.format(
                run_id=run.run_id, status=run.status.value
            ),
        )

    if not graphene_info.context.execution_manager.terminate(run_id):
        return graphene_info.schema.type_named('CancelPipelineExecutionFailure')(
            run=dauphin_run, message='Unable to terminate run {run_id}'.format(run_id=run.run_id)
        )

    return graphene_info.schema.type_named('CancelPipelineExecutionSuccess')(dauphin_run)


@capture_dauphin_error
def delete_pipeline_run(graphene_info, run_id):
    instance = graphene_info.context.instance

    if not instance.has_run(run_id):
        return graphene_info.schema.type_named('PipelineRunNotFoundError')(run_id)

    instance.delete_run(run_id)

    return graphene_info.schema.type_named('DeletePipelineRunSuccess')(run_id)


@capture_dauphin_error
def start_scheduled_execution(graphene_info, schedule_name):
    from dagster_graphql.schema.roots import create_execution_metadata

    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    schedule_def = get_dagster_schedule_def(graphene_info, schedule_name)

    schedule_context = ScheduleExecutionContext(graphene_info.context.instance)

    # Run should_execute and halt if it returns False
    if not schedule_def.should_execute(schedule_context):
        return graphene_info.schema.type_named('ScheduledExecutionBlocked')(
            message='Schedule {schedule_name} did not run because the should_execute did not return'
            ' True'.format(schedule_name=schedule_name)
        )

    # Get environment_dict
    environment_dict = schedule_def.get_environment_dict(schedule_context)
    tags = schedule_def.get_tags(schedule_context)

    check.invariant('dagster/schedule_name' not in tags)
    tags['dagster/schedule_name'] = schedule_def.name

    execution_metadata_tags = [{'key': key, 'value': value} for key, value in tags.items()]
    execution_params = merge_dicts(
        schedule_def.execution_params, {'executionMetadata': {'tags': execution_metadata_tags}}
    )

    selector = ExecutionSelector(
        execution_params['selector']['name'], execution_params['selector'].get('solidSubset')
    )

    execution_params = ExecutionParams(
        selector=selector,
        environment_dict=environment_dict,
        mode=execution_params.get('mode'),
        execution_metadata=create_execution_metadata(execution_params.get('executionMetadata')),
        step_keys=execution_params.get('stepKeys'),
        previous_run_id=None,
    )

    # Launch run if run launcher is defined
    run_launcher = graphene_info.context.instance.run_launcher
    if run_launcher:
        return launch_pipeline_execution(graphene_info, execution_params)

    return start_pipeline_execution(graphene_info, execution_params)


@capture_dauphin_error
def start_pipeline_execution(graphene_info, execution_params):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    instance = graphene_info.context.instance

    dauphin_pipeline = get_dauphin_pipeline_from_selector_or_raise(
        graphene_info, execution_params.selector
    )

    get_validated_config(
        graphene_info,
        dauphin_pipeline,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
    )

    pipeline = dauphin_pipeline.get_dagster_pipeline()
    execution_plan = create_execution_plan(
        pipeline,
        execution_params.environment_dict,
        run_config=RunConfig(
            mode=execution_params.mode, previous_run_id=execution_params.previous_run_id
        ),
    )

    _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan)

    run = instance.get_or_create_run(_create_pipeline_run(instance, pipeline, execution_params))

    graphene_info.context.execution_manager.execute_pipeline(
        graphene_info.context.get_handle(),
        dauphin_pipeline.get_dagster_pipeline(),
        run,
        instance=instance,
    )

    return graphene_info.schema.type_named('StartPipelineExecutionSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )


def _create_pipeline_run(instance, pipeline, execution_params):
    step_keys_to_execute = execution_params.step_keys
    if not execution_params.step_keys and execution_params.previous_run_id:
        execution_plan = create_execution_plan(
            pipeline,
            execution_params.environment_dict,
            run_config=RunConfig(
                mode=execution_params.mode, previous_run_id=execution_params.previous_run_id
            ),
        )
        step_keys_to_execute = get_retry_steps_from_execution_plan(instance, execution_plan)
    return pipeline_run_from_execution_params(execution_params, step_keys_to_execute)


@capture_dauphin_error
def launch_pipeline_execution(graphene_info, execution_params):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    instance = graphene_info.context.instance
    run_launcher = instance.run_launcher

    if run_launcher is None:
        return graphene_info.schema.type_named('RunLauncherNotDefinedError')()

    dauphin_pipeline = get_dauphin_pipeline_from_selector_or_raise(
        graphene_info, execution_params.selector
    )

    get_validated_config(
        graphene_info,
        dauphin_pipeline,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
    )

    pipeline = dauphin_pipeline.get_dagster_pipeline()
    execution_plan = create_execution_plan(
        pipeline,
        execution_params.environment_dict,
        run_config=RunConfig(
            mode=execution_params.mode, previous_run_id=execution_params.previous_run_id
        ),
    )

    _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan)

    run = instance.launch_run(_create_pipeline_run(instance, pipeline, execution_params))

    return graphene_info.schema.type_named('LaunchPipelineExecutionSuccess')(
        run=graphene_info.schema.type_named('PipelineRun')(run)
    )


def _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan):
    if execution_params.step_keys:
        for step_key in execution_params.step_keys:
            if not execution_plan.has_step(step_key):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidStepError')(invalid_step_key=step_key)
                )


def get_pipeline_run_observable(graphene_info, run_id, after=None):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(run_id, 'run_id')
    check.opt_int_param(after, 'after')
    instance = graphene_info.context.instance
    run = instance.get_run_by_id(run_id)

    if not run:

        def _get_error_observable(observer):
            observer.on_next(
                graphene_info.schema.type_named('PipelineRunLogsSubscriptionFailure')(
                    missingRunId=run_id, message='Could not load run with id {}'.format(run_id)
                )
            )

        return Observable.create(_get_error_observable)  # pylint: disable=E1101

    pipeline = get_dauphin_pipeline_reference_from_selector(graphene_info, run.selector)

    from ..schema.pipelines import DauphinPipeline

    if not isinstance(pipeline, DauphinPipeline):
        return Observable.empty()  # pylint: disable=no-member

    execution_plan = create_execution_plan(
        pipeline.get_dagster_pipeline(), run.environment_dict, RunConfig(mode=run.mode)
    )

    # pylint: disable=E1101
    return Observable.create(
        PipelineRunObservableSubscribe(instance, run_id, after_cursor=after)
    ).map(
        lambda events: graphene_info.schema.type_named('PipelineRunLogsSubscriptionSuccess')(
            run=graphene_info.schema.type_named('PipelineRun')(run),
            messages=[
                from_event_record(graphene_info, event, pipeline, execution_plan)
                for event in events
            ],
        )
    )


def get_compute_log_observable(graphene_info, run_id, step_key, io_type, cursor=None):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(run_id, 'run_id')
    check.str_param(step_key, 'step_key')
    check.inst_param(io_type, 'io_type', ComputeIOType)
    check.opt_str_param(cursor, 'cursor')

    return graphene_info.context.instance.compute_log_manager.observable(
        run_id, step_key, io_type, cursor
    ).map(lambda update: from_compute_log_file(graphene_info, update))


@capture_dauphin_error
def do_execute_plan(graphene_info, execution_params):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    return _execute_plan_resolve_config(
        graphene_info,
        execution_params,
        get_dauphin_pipeline_from_selector_or_raise(graphene_info, execution_params.selector),
    )


def _execute_plan_resolve_config(graphene_info, execution_params, dauphin_pipeline):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    get_validated_config(
        graphene_info, dauphin_pipeline, execution_params.environment_dict, execution_params.mode
    )
    return _do_execute_plan(graphene_info, execution_params, dauphin_pipeline)


def _do_execute_plan(graphene_info, execution_params, dauphin_pipeline):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    pipeline = dauphin_pipeline.get_dagster_pipeline()
    run_id = execution_params.execution_metadata.run_id

    pipeline_run = graphene_info.context.instance.get_run_by_id(run_id)
    if not pipeline_run:
        # TODO switch to raising a UserFacingError if the run_id cannot be found
        # https://github.com/dagster-io/dagster/issues/1876
        pipeline_run = PipelineRun(
            pipeline_name=pipeline.name,
            run_id=run_id,
            environment_dict=execution_params.environment_dict,
            mode=execution_params.mode or pipeline.get_default_mode_name(),
            tags=execution_params.execution_metadata.tags or {},
        )

    execution_plan = create_execution_plan(
        pipeline=pipeline,
        environment_dict=execution_params.environment_dict,
        run_config=pipeline_run,
    )

    if execution_params.step_keys:
        for step_key in execution_params.step_keys:
            if not execution_plan.has_step(step_key):
                raise UserFacingGraphQLError(
                    graphene_info.schema.type_named('InvalidStepError')(invalid_step_key=step_key)
                )

        execution_plan = execution_plan.build_subset_plan(execution_params.step_keys)

    event_logs = []

    def _on_event_record(record):
        if record.is_dagster_event:
            event_logs.append(record)

    graphene_info.context.instance.add_event_listener(run_id, _on_event_record)

    execute_plan(
        execution_plan=execution_plan,
        environment_dict=execution_params.environment_dict,
        pipeline_run=pipeline_run,
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
