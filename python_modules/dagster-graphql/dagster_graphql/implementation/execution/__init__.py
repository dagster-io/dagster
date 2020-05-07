from __future__ import absolute_import

import sys
import time

from dagster_graphql.implementation.fetch_runs import is_config_valid
from dagster_graphql.schema.pipelines import DauphinPipeline
from dagster_graphql.schema.runs import (
    from_compute_log_file,
    from_dagster_event_record,
    from_event_record,
)
from graphql.execution.base import ResolveInfo
from rx import Observable

from dagster import check
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.errors import (
    DagsterInvalidConfigError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import DagsterEventType
from dagster.core.execution.memoization import get_retry_steps_from_execution_plan
from dagster.core.scheduler import ScheduleTickStatus
from dagster.core.scheduler.scheduler import ScheduleTickData
from dagster.core.snap import ExecutionPlanIndex, PipelineIndex
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.serdes import serialize_dagster_namedtuple
from dagster.utils.error import serializable_error_info_from_exc_info

from ..external import (
    ExternalPipeline,
    ensure_valid_config,
    ensure_valid_step_keys,
    get_external_pipeline_subset_or_raise,
)
from ..fetch_schedules import execution_params_for_schedule, get_dagster_schedule_def
from ..pipeline_run_storage import PipelineRunObservableSubscribe
from ..utils import ExecutionParams, UserFacingGraphQLError, capture_dauphin_error
from .launch_execution import launch_pipeline_execution, launch_pipeline_reexecution
from .scheduled_execution import start_scheduled_execution
from .start_execution import start_pipeline_execution, start_pipeline_reexecution


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

    execution_plan_index = (
        ExecutionPlanIndex(
            execution_plan_snapshot=instance.get_execution_plan_snapshot(
                run.execution_plan_snapshot_id
            ),
            pipeline_index=PipelineIndex(instance.get_pipeline_snapshot(run.pipeline_snapshot_id)),
        )
        if run.pipeline_snapshot_id and run.execution_plan_snapshot_id
        else None
    )

    # pylint: disable=E1101
    return Observable.create(
        PipelineRunObservableSubscribe(instance, run_id, after_cursor=after)
    ).map(
        lambda events: graphene_info.schema.type_named('PipelineRunLogsSubscriptionSuccess')(
            run=graphene_info.schema.type_named('PipelineRun')(run),
            messages=[
                from_event_record(event, run.pipeline_name, execution_plan_index)
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

    external_pipeline = get_external_pipeline_subset_or_raise(
        graphene_info, execution_params.selector.name, execution_params.selector.solid_subset
    )
    ensure_valid_config(
        external_pipeline=external_pipeline,
        mode=execution_params.mode,
        environment_dict=execution_params.environment_dict,
    )
    return _do_execute_plan(graphene_info, execution_params, external_pipeline)


def _do_execute_plan(graphene_info, execution_params, external_pipeline):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(execution_params, 'execution_params', ExecutionParams)
    check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)

    run_id = execution_params.execution_metadata.run_id

    mode = execution_params.mode or external_pipeline.get_default_mode_name()

    pipeline_run = graphene_info.context.instance.get_run_by_id(run_id)

    execution_plan_index = graphene_info.context.create_execution_plan_index(
        external_pipeline=external_pipeline,
        environment_dict=execution_params.environment_dict,
        mode=mode,
    )

    if not pipeline_run:
        # TODO switch to raising a UserFacingError if the run_id cannot be found
        # https://github.com/dagster-io/dagster/issues/1876
        pipeline_run = graphene_info.context.instance.create_run(
            pipeline_name=external_pipeline.name,
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=execution_plan_index.execution_plan_snapshot,
            run_id=run_id,
            environment_dict=execution_params.environment_dict,
            mode=mode,
            tags=execution_params.execution_metadata.tags or {},
        )

    ensure_valid_step_keys(execution_plan_index, execution_params.step_keys)

    if execution_params.step_keys:
        execution_plan_index = graphene_info.context.create_execution_plan_index(
            external_pipeline=external_pipeline,
            environment_dict=execution_params.environment_dict,
            mode=mode,
            step_keys_to_execute=execution_params.step_keys,
        )

    event_logs = []

    def _on_event_record(record):
        if record.is_dagster_event:
            event_logs.append(record)

    graphene_info.context.instance.add_event_listener(run_id, _on_event_record)

    graphene_info.context.execute_plan(
        external_pipeline=external_pipeline,
        environment_dict=execution_params.environment_dict,
        pipeline_run=pipeline_run,
        step_keys_to_execute=execution_params.step_keys,
    )

    def to_graphql_event(event_record):
        return from_dagster_event_record(event_record, external_pipeline.name, execution_plan_index)

    return graphene_info.schema.type_named('ExecutePlanSuccess')(
        pipeline=DauphinPipeline(external_pipeline),
        has_failures=any(
            er
            for er in event_logs
            if er.is_dagster_event and er.dagster_event.event_type == DagsterEventType.STEP_FAILURE
        ),
        step_events=list(map(to_graphql_event, event_logs)),
        raw_event_records=list(map(serialize_dagster_namedtuple, event_logs)),
    )
