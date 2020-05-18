from __future__ import absolute_import

import sys
import time

from dagster_graphql.implementation.utils import ExecutionMetadata, ExecutionParams
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.config.validate import validate_config_from_snap
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.errors import (
    DagsterUserCodeExecutionError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import EngineEventData
from dagster.core.scheduler import ScheduleTickStatus
from dagster.core.scheduler.scheduler import ScheduleTickData
from dagster.core.storage.tags import check_tags
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.merger import merge_dicts

from ..external import ExternalPipeline, get_external_pipeline_subset_or_raise
from ..fetch_schedules import get_dagster_schedule_def
from ..utils import capture_dauphin_error
from .launch_execution import _launch_pipeline_execution_for_created_run
from .start_execution import _start_pipeline_execution_for_created_run


@capture_dauphin_error
def start_scheduled_execution(graphene_info, schedule_name):
    '''
    When a scheduler ticks and needs to run for a given schedule, it issues a
    START_SCHEDULED_EXECUTION mutation with just the schedule name. The mutation is
    resolved entirely by this method.
    '''

    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    tick = None
    try:
        # We first load the repository and schedule definition to create
        # and store a ScheduleTick.
        # If this fails, this error should be sent to the file based scheduler logs.
        repository = graphene_info.context.get_repository()
        schedule_def = get_dagster_schedule_def(graphene_info, schedule_name)
        cron_schedule = "Unknown" if not schedule_def else schedule_def.cron_schedule
        tick = graphene_info.context.instance.create_schedule_tick(
            repository,
            ScheduleTickData(
                schedule_name=schedule_name,
                cron_schedule=cron_schedule,
                timestamp=time.time(),
                status=ScheduleTickStatus.STARTED,
            ),
        )

        # Run should_execute and halt if it returns False
        schedule_context = ScheduleExecutionContext(graphene_info.context.instance, repository)
        with user_code_error_boundary(
            ScheduleExecutionError,
            lambda: 'Error occurred during the execution should_execute for schedule '
            '{schedule_name}'.format(schedule_name=schedule_def.name),
        ):
            should_execute = schedule_def.should_execute(schedule_context)

        if not should_execute:
            # Update tick to skipped state and return
            tick = tick.with_status(ScheduleTickStatus.SKIPPED)
            graphene_info.context.instance.update_schedule_tick(repository, tick)
            # Return skipped specific gql response
            return graphene_info.schema.type_named('ScheduledExecutionBlocked')(
                message='Schedule {schedule_name} did not run because the should_execute did not return'
                ' True'.format(schedule_name=schedule_name)
            )

        errors = []

        environment_dict = {}
        schedule_tags = {}
        try:
            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: 'Error occurred during the execution of environment_dict_fn for schedule '
                '{schedule_name}'.format(schedule_name=schedule_def.name),
            ):
                environment_dict = schedule_def.get_environment_dict(schedule_context)
        except DagsterUserCodeExecutionError as exc:
            error_data = serializable_error_info_from_exc_info(sys.exc_info())
            errors.append(error_data)

        try:
            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: 'Error occurred during the execution of tags_fn for schedule '
                '{schedule_name}'.format(schedule_name=schedule_def.name),
            ):
                schedule_tags = schedule_def.get_tags(schedule_context)
        except DagsterUserCodeExecutionError:
            error_data = serializable_error_info_from_exc_info(sys.exc_info())
            errors.append(error_data)

        external_pipeline = get_external_pipeline_subset_or_raise(
            graphene_info, schedule_def.selector.name, schedule_def.selector.solid_subset
        )
        pipeline_tags = external_pipeline.tags or {}
        check_tags(pipeline_tags, 'pipeline_tags')
        tags = merge_dicts(pipeline_tags, schedule_tags)

        selector = schedule_def.selector
        mode = schedule_def.mode

        execution_params = ExecutionParams(
            selector=selector,
            environment_dict=environment_dict,
            mode=mode,
            execution_metadata=ExecutionMetadata(tags=tags, run_id=None),
            step_keys=None,
        )

        run, result = _execute_schedule(graphene_info, external_pipeline, execution_params, errors)
        graphene_info.context.instance.update_schedule_tick(
            repository, tick.with_status(ScheduleTickStatus.SUCCESS, run_id=run.run_id),
        )

        return result

    except Exception as exc:  # pylint: disable=broad-except
        error_data = serializable_error_info_from_exc_info(sys.exc_info())

        if tick:
            graphene_info.context.instance.update_schedule_tick(
                repository, tick.with_status(ScheduleTickStatus.FAILURE, error=error_data),
            )

        raise exc


def _execute_schedule(graphene_info, external_pipeline, execution_params, errors):
    check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)

    instance = graphene_info.context.instance

    mode, environment_dict = execution_params.mode, execution_params.environment_dict

    validation_result = validate_config_from_snap(
        external_pipeline.config_schema_snapshot,
        external_pipeline.get_mode(mode).root_config_key,
        environment_dict,
    )

    execution_plan_snapshot = None
    if validation_result.success:
        execution_plan_index = graphene_info.context.create_execution_plan_index(
            external_pipeline, environment_dict, mode, execution_params.step_keys
        )
        execution_plan_snapshot = execution_plan_index.execution_plan_snapshot

    pipeline_run = instance.create_run(
        pipeline_name=external_pipeline.name,
        environment_dict=environment_dict,
        mode=mode,
        solid_subset=(
            execution_params.selector.solid_subset
            if execution_params.selector is not None
            else None
        ),
        tags=execution_params.execution_metadata.tags,
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
    )

    # Inject errors into event log at this point
    if len(errors) > 0:
        for error in errors:
            instance.report_engine_event(
                error.message, pipeline_run, EngineEventData.engine_error(error)
            )

    # Launch run if run launcher is defined
    run_launcher = graphene_info.context.instance.run_launcher
    if run_launcher:
        result = _launch_pipeline_execution_for_created_run(graphene_info, pipeline_run.run_id)
    else:
        result = _start_pipeline_execution_for_created_run(graphene_info, pipeline_run.run_id)

    return pipeline_run, result
