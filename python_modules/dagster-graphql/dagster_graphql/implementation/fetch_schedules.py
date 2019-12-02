import glob
import os

from graphql.execution.base import ResolveInfo

from dagster import check

from .utils import UserFacingGraphQLError


def get_scheduler_handle(graphene_info):
    scheduler_handle = graphene_info.context.scheduler_handle
    if not scheduler_handle:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    return scheduler_handle


def get_dagster_schedule_def(graphene_info, schedule_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    scheduler_handle = get_scheduler_handle(graphene_info)
    schedule_definition = scheduler_handle.get_schedule_def_by_name(schedule_name)
    if not schedule_definition:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ScheduleDefinitionNotFoundError')(
                schedule_name=schedule_name
            )
        )

    return schedule_definition


def get_dagster_schedule(graphene_info, schedule_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    scheduler = graphene_info.context.get_scheduler()
    if not scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    schedule = scheduler.get_schedule_by_name(schedule_name)
    if not schedule:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ScheduleNotFoundError')(schedule_name=schedule_name)
        )

    return schedule


def get_schedule_attempt_filenames(graphene_info, schedule_name):
    scheduler = graphene_info.context.get_scheduler()
    log_dir = scheduler.log_path_for_schedule(schedule_name)
    return glob.glob(os.path.join(log_dir, "*.result"))
