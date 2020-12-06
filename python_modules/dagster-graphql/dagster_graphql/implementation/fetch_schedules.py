from dagster import check
from dagster.core.host_representation import PipelineSelector, RepositorySelector, ScheduleSelector
from graphql.execution.base import ResolveInfo

from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def reconcile_scheduler_state(graphene_info, repository_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    instance = graphene_info.context.instance

    instance.reconcile_scheduler_state(repository)
    return graphene_info.schema.type_named("ReconcileSchedulerStateSuccess")(message="Success")


@capture_dauphin_error
def start_schedule(graphene_info, schedule_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)
    instance = graphene_info.context.instance
    schedule_state = instance.start_schedule_and_update_storage_state(
        repository.get_external_schedule(schedule_selector.schedule_name)
    )
    return graphene_info.schema.type_named("ScheduleStateResult")(
        graphene_info.schema.type_named("JobState")(schedule_state)
    )


@capture_dauphin_error
def stop_schedule(graphene_info, schedule_origin_id):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    instance = graphene_info.context.instance
    schedule_state = instance.stop_schedule_and_update_storage_state(schedule_origin_id)
    return graphene_info.schema.type_named("ScheduleStateResult")(
        graphene_info.schema.type_named("JobState")(schedule_state)
    )


@capture_dauphin_error
def get_scheduler_or_error(graphene_info):
    instance = graphene_info.context.instance

    if not instance.scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named("SchedulerNotDefinedError")())

    return graphene_info.schema.type_named("Scheduler")(
        scheduler_class=instance.scheduler.__class__.__name__
    )


@capture_dauphin_error
def get_schedules_or_error(graphene_info, repository_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    external_schedules = repository.get_external_schedules()

    results = [
        graphene_info.schema.type_named("Schedule")(
            graphene_info, external_schedule=external_schedule
        )
        for external_schedule in external_schedules
    ]

    return graphene_info.schema.type_named("Schedules")(results=results)


def get_schedules_for_pipeline(graphene_info, pipeline_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(pipeline_selector, "pipeline_selector", PipelineSelector)

    location = graphene_info.context.get_repository_location(pipeline_selector.location_name)
    repository = location.get_repository(pipeline_selector.repository_name)
    external_schedules = repository.get_external_schedules()

    return [
        graphene_info.schema.type_named("Schedule")(
            graphene_info, external_schedule=external_schedule
        )
        for external_schedule in external_schedules
        if external_schedule.pipeline_name == pipeline_selector.pipeline_name
    ]


@capture_dauphin_error
def get_schedule_or_error(graphene_info, schedule_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)

    external_schedule = repository.get_external_schedule(schedule_selector.schedule_name)
    if not external_schedule:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named("ScheduleNotFoundError")(
                schedule_name=schedule_selector.schedule_name
            )
        )

    return graphene_info.schema.type_named("Schedule")(
        graphene_info, external_schedule=external_schedule
    )
