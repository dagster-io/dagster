from graphql.execution.base import ResolveInfo

from dagster import check

from .utils import UserFacingGraphQLError


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
