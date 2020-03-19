from __future__ import absolute_import

import sys
import time

from dagster_graphql.client.util import pipeline_run_from_execution_params
from dagster_graphql.schema.pipelines import DauphinPipeline
from dagster_graphql.schema.runs import (
    from_compute_log_file,
    from_dagster_event_record,
    from_event_record,
)
from graphql.execution.base import ResolveInfo
from rx import Observable

from dagster import RunConfig, check
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.errors import ScheduleExecutionError, user_code_error_boundary
from dagster.core.events import DagsterEventType
from dagster.core.execution.api import create_execution_plan, execute_plan
from dagster.core.execution.memoization import get_retry_steps_from_execution_plan
from dagster.core.scheduler import ScheduleTickStatus
from dagster.core.scheduler.scheduler import ScheduleTickData
from dagster.core.serdes import serialize_dagster_namedtuple
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.utils.error import serializable_error_info_from_exc_info

from .fetch_pipelines import (
    get_dauphin_pipeline_reference_from_selector,
    get_pipeline_def_from_selector,
)
from .fetch_runs import get_validated_config
from .fetch_schedules import execution_params_for_schedule, get_dagster_schedule_def
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
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    try:
        repository = graphene_info.context.get_repository()
        schedule_context = ScheduleExecutionContext(graphene_info.context.instance)
        schedule_def = get_dagster_schedule_def(graphene_info, schedule_name)
        tick = graphene_info.context.instance.create_schedule_tick(
            repository,
            ScheduleTickData(
                schedule_name=schedule_def.name,
                cron_schedule=schedule_def.cron_schedule,
                timestamp=time.time(),
                status=ScheduleTickStatus.STARTED,
            ),
        )

        # Run should_execute and halt if it returns False
        with user_code_error_boundary(
            ScheduleExecutionError,
            lambda: 'Error occurred during the execution should_execute for schedule '
            '{schedule_name}'.format(schedule_name=schedule_def.name),
        ):
            should_execute = schedule_def.should_execute(schedule_context)

        if not should_execute:
            # Update tick
            tick = tick.with_status(ScheduleTickStatus.SKIPPED)
            graphene_info.context.instance.update_schedule_tick(repository, tick)
            # Return skipped specific gql response
            return graphene_info.schema.type_named('ScheduledExecutionBlocked')(
                message='Schedule {schedule_name} did not run because the should_execute did not return'
                ' True'.format(schedule_name=schedule_name)
            )

        pipeline_def = get_pipeline_def_from_selector(graphene_info, schedule_def.selector)
        execution_params = execution_params_for_schedule(
            graphene_info, schedule_def=schedule_def, pipeline_def=pipeline_def
        )

        # Launch run if run launcher is defined
        run_launcher = graphene_info.context.instance.run_launcher
        if run_launcher:
            result = launch_pipeline_execution(graphene_info, execution_params)
        else:
            result = start_pipeline_execution(graphene_info, execution_params)

        run = result.run
        graphene_info.context.instance.update_schedule_tick(
            repository, tick.with_status(ScheduleTickStatus.SUCCESS, run_id=run.run_id),
        )

        return result

    except Exception as exc:  # pylint: disable=broad-except
        error_data = serializable_error_info_from_exc_info(sys.exc_info())
        graphene_info.context.instance.update_schedule_tick(
            repository, tick.with_status(ScheduleTickStatus.FAILURE, error=error_data),
        )

        raise exc


@capture_dauphin_error
def start_pipeline_execution(graphene_info, execution_params):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    instance = graphene_info.context.instance

    execution_manager_settings = instance.dagit_settings.get('execution_manager')
    if execution_manager_settings and execution_manager_settings.get('disabled'):
        return graphene_info.schema.type_named('StartPipelineExecutionDisabledError')()

    pipeline_def = get_pipeline_def_from_selector(graphene_info, execution_params.selector)

    get_validated_config(
        graphene_info,
        pipeline_def,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
    )

    execution_plan = create_execution_plan(
        pipeline_def,
        execution_params.environment_dict,
        run_config=RunConfig(
            mode=execution_params.mode, previous_run_id=execution_params.previous_run_id,
        ),
    )

    _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan)

    run = instance.get_or_create_run(_create_pipeline_run(instance, pipeline_def, execution_params))

    graphene_info.context.execution_manager.execute_pipeline(
        graphene_info.context.get_handle(), pipeline_def, run, instance=instance,
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
                mode=execution_params.mode, previous_run_id=execution_params.previous_run_id,
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

    pipeline_def = get_pipeline_def_from_selector(graphene_info, execution_params.selector)

    get_validated_config(
        graphene_info,
        pipeline_def,
        environment_dict=execution_params.environment_dict,
        mode=execution_params.mode,
    )

    execution_plan = create_execution_plan(
        pipeline_def,
        execution_params.environment_dict,
        run_config=RunConfig(
            mode=execution_params.mode, previous_run_id=execution_params.previous_run_id
        ),
    )

    _check_start_pipeline_execution_errors(graphene_info, execution_params, execution_plan)

    run = instance.launch_run(_create_pipeline_run(instance, pipeline_def, execution_params))

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

    pipeline_def = get_pipeline_def_from_selector(graphene_info, run.selector)
    pipeline_ref = get_dauphin_pipeline_reference_from_selector(graphene_info, run.selector)

    execution_plan = None
    if isinstance(pipeline_ref, DauphinPipeline):
        execution_plan = create_execution_plan(
            pipeline_def, run.environment_dict, RunConfig(mode=run.mode)
        )

    # pylint: disable=E1101
    return Observable.create(
        PipelineRunObservableSubscribe(instance, run_id, after_cursor=after)
    ).map(
        lambda events: graphene_info.schema.type_named('PipelineRunLogsSubscriptionSuccess')(
            run=graphene_info.schema.type_named('PipelineRun')(run),
            messages=[
                from_event_record(graphene_info, event, pipeline_ref, execution_plan)
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

    pipeline_def = get_pipeline_def_from_selector(graphene_info, execution_params.selector)
    get_validated_config(
        graphene_info, pipeline_def, execution_params.environment_dict, execution_params.mode
    )
    return _do_execute_plan(graphene_info, execution_params, pipeline_def)


def _do_execute_plan(graphene_info, execution_params, pipeline_def):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)

    run_id = execution_params.execution_metadata.run_id

    pipeline_run = graphene_info.context.instance.get_run_by_id(run_id)
    if not pipeline_run:
        # TODO switch to raising a UserFacingError if the run_id cannot be found
        # https://github.com/dagster-io/dagster/issues/1876
        pipeline_run = PipelineRun(
            pipeline_name=pipeline_def.name,
            run_id=run_id,
            environment_dict=execution_params.environment_dict,
            mode=execution_params.mode or pipeline_def.get_default_mode_name(),
            tags=execution_params.execution_metadata.tags or {},
        )

    execution_plan = create_execution_plan(
        pipeline=pipeline_def,
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

    dauphin_pipeline = DauphinPipeline(pipeline_def)

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
