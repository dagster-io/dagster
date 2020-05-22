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
from dagster.core.host_representation import ExternalPipeline
from dagster.core.scheduler import ScheduleTickStatus
from dagster.core.scheduler.scheduler import ScheduleTickData
from dagster.core.storage.tags import check_tags
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.merger import merge_dicts

from ..external import get_external_pipeline_or_raise
from ..fetch_schedules import get_dagster_schedule_def
from ..utils import PipelineSelector, capture_dauphin_error
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
        external_repository = graphene_info.context.legacy_external_repository
        repository_name = external_repository.name
        schedule_def = get_dagster_schedule_def(graphene_info, schedule_name)
        cron_schedule = "Unknown" if not schedule_def else schedule_def.cron_schedule
        tick = graphene_info.context.instance.create_schedule_tick(
            repository_name,
            ScheduleTickData(
                schedule_name=schedule_name,
                cron_schedule=cron_schedule,
                timestamp=time.time(),
                status=ScheduleTickStatus.STARTED,
            ),
        )
        with user_code_error_boundary(
            ScheduleExecutionError,
            lambda: 'Schedule {schedule_name} not found in repository.'.format(
                schedule_name=schedule_name
            ),
        ):
            check.invariant(schedule_def is not None)

        # Run should_execute and halt if it returns False
        schedule_context = ScheduleExecutionContext(graphene_info.context.instance)
        with user_code_error_boundary(
            ScheduleExecutionError,
            lambda: 'Error occurred during the execution should_execute for schedule '
            '{schedule_name}'.format(schedule_name=schedule_def.name),
        ):
            should_execute = schedule_def.should_execute(schedule_context)

        if not should_execute:
            # Update tick to skipped state and return
            tick = tick.with_status(ScheduleTickStatus.SKIPPED)
            graphene_info.context.instance.update_schedule_tick(repository_name, tick)
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

        external_pipeline = get_external_pipeline_or_raise(
            graphene_info, schedule_def.pipeline_name, schedule_def.solid_subset
        )
        pipeline_tags = external_pipeline.tags or {}
        check_tags(pipeline_tags, 'pipeline_tags')
        tags = merge_dicts(pipeline_tags, schedule_tags)

        mode = schedule_def.mode

        execution_params = ExecutionParams(
            selector=PipelineSelector.legacy(
                graphene_info.context, schedule_def.pipeline_name, schedule_def.solid_subset
            ),
            environment_dict=environment_dict,
            mode=mode,
            execution_metadata=ExecutionMetadata(tags=tags, run_id=None),
            step_keys=None,
        )

        run, result = _execute_schedule(graphene_info, external_pipeline, execution_params, errors)
        graphene_info.context.instance.update_schedule_tick(
            repository_name, tick.with_status(ScheduleTickStatus.SUCCESS, run_id=run.run_id),
        )

        return result

    except Exception as exc:  # pylint: disable=broad-except
        error_data = serializable_error_info_from_exc_info(sys.exc_info())

        if tick:
            graphene_info.context.instance.update_schedule_tick(
                repository_name, tick.with_status(ScheduleTickStatus.FAILURE, error=error_data),
            )

        raise exc


def _execute_schedule(graphene_info, external_pipeline, execution_params, errors):
    check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)

    instance = graphene_info.context.instance

    mode, environment_dict = execution_params.mode, execution_params.environment_dict

    validation_result = validate_config_from_snap(
        external_pipeline.config_schema_snapshot,
        external_pipeline.root_config_key_for_mode(mode),
        environment_dict,
    )

    external_execution_plan = (
        graphene_info.context.legacy_get_external_execution_plan(
            external_pipeline, environment_dict, mode, execution_params.step_keys
        )
        if validation_result.success
        else None
    )

    pipeline_run = instance.create_run(
        pipeline_name=external_pipeline.name,
        run_id=None,
        environment_dict=environment_dict,
        mode=mode,
        solid_subset=(
            execution_params.selector.solid_subset
            if execution_params.selector is not None
            else None
        ),
        step_keys_to_execute=None,
        status=None,
        tags=execution_params.execution_metadata.tags,
        root_run_id=None,
        parent_run_id=None,
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot
        if external_execution_plan
        else None,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
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
