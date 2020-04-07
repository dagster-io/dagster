from __future__ import absolute_import

import sys
import time

from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.errors import ScheduleExecutionError, user_code_error_boundary
from dagster.core.scheduler import ScheduleTickStatus
from dagster.core.scheduler.scheduler import ScheduleTickData
from dagster.utils.error import serializable_error_info_from_exc_info

from ..fetch_pipelines import get_pipeline_def_from_selector
from ..fetch_schedules import execution_params_for_schedule, get_dagster_schedule_def
from ..utils import capture_dauphin_error
from .launch_execution import _launch_pipeline_execution
from .start_execution import _start_pipeline_execution


@capture_dauphin_error
def start_scheduled_execution(graphene_info, schedule_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    tick = None
    try:
        repository = graphene_info.context.get_repository()
        schedule_context = ScheduleExecutionContext(graphene_info.context.instance, repository)
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
            result = _launch_pipeline_execution(graphene_info, execution_params)
        else:
            result = _start_pipeline_execution(graphene_info, execution_params)

        run = result.run
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
