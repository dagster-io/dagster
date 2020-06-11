import yaml
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.api.snapshot_schedule import sync_get_external_schedule_execution_data
from dagster.core.host_representation import ExternalSchedule, ScheduleSelector

from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def start_schedule(graphene_info, schedule_selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(schedule_selector, 'schedule_selector', ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)
    instance = graphene_info.context.instance
    schedule = instance.start_schedule_and_update_storage_state(
        repository.get_external_schedule(schedule_selector.schedule_name)
    )
    return graphene_info.schema.type_named('RunningScheduleResult')(
        schedule=graphene_info.schema.type_named('RunningSchedule')(
            graphene_info, schedule=schedule
        )
    )


@capture_dauphin_error
def stop_schedule(graphene_info, schedule_selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(schedule_selector, 'schedule_selector', ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)
    instance = graphene_info.context.instance
    schedule = instance.stop_schedule_and_update_storage_state(
        repository.get_external_schedule(schedule_selector.schedule_name).get_origin_id()
    )
    return graphene_info.schema.type_named('RunningScheduleResult')(
        schedule=graphene_info.schema.type_named('RunningSchedule')(
            graphene_info, schedule=schedule
        )
    )


@capture_dauphin_error
def get_scheduler_or_error(graphene_info):
    instance = graphene_info.context.instance

    if not instance.scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    return graphene_info.schema.type_named('Scheduler')()


@capture_dauphin_error
def get_schedules(graphene_info):
    instance = graphene_info.context.instance

    return [
        graphene_info.schema.type_named('RunningSchedule')(graphene_info, schedule=s)
        for s in instance.all_stored_schedule_state()
    ]


@capture_dauphin_error
def get_schedule_definitions(graphene_info):
    external_repository = graphene_info.context.legacy_external_repository
    external_schedules = external_repository.get_external_schedules()

    return [
        graphene_info.schema.type_named('ScheduleDefinition')(external_schedule=external_schedule,)
        for external_schedule in external_schedules
    ]


@capture_dauphin_error
def get_schedule_or_error(graphene_info, schedule_selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(schedule_selector, 'schedule_selector', ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)
    instance = graphene_info.context.instance

    schedule = instance.get_schedule_state(
        repository.get_external_schedule(schedule_selector.schedule_name).get_origin_id()
    )
    if not schedule:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ScheduleNotFoundError')(
                schedule_name=schedule_selector.schedule_name
            )
        )

    return graphene_info.schema.type_named('RunningSchedule')(graphene_info, schedule=schedule)


def get_schedule_yaml(graphene_info, external_schedule):
    check.inst_param(external_schedule, 'external_schedule', ExternalSchedule)
    handle = external_schedule.handle.repository_handle
    schedule_execution_data = sync_get_external_schedule_execution_data(
        graphene_info.context.instance, handle, external_schedule.name
    )
    if schedule_execution_data.error:
        return None
    run_config_yaml = yaml.safe_dump(schedule_execution_data.run_config, default_flow_style=False)
    return run_config_yaml if run_config_yaml else ''


def get_dagster_schedule_def(graphene_info, schedule_name):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.str_param(schedule_name, 'schedule_name')

    # TODO: Serialize schedule as ExternalScheduleData and add to ExternalRepositoryData
    repository = graphene_info.context.legacy_get_repository_definition()
    schedule_definition = repository.get_schedule_def(schedule_name)
    return schedule_definition
