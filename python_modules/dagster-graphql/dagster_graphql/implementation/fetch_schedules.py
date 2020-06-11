import yaml
from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.api.snapshot_schedule import sync_get_external_schedule_execution_data
from dagster.core.host_representation import (
    ExternalSchedule,
    PipelineSelector,
    RepositorySelector,
    ScheduleSelector,
)

from .utils import UserFacingGraphQLError, capture_dauphin_error


@capture_dauphin_error
def start_schedule(graphene_info, schedule_selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(schedule_selector, 'schedule_selector', ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)
    instance = graphene_info.context.instance
    schedule_state = instance.start_schedule_and_update_storage_state(
        repository.get_external_schedule(schedule_selector.schedule_name)
    )
    return graphene_info.schema.type_named('ScheduleStateResult')(
        schedule_state=graphene_info.schema.type_named('ScheduleState')(
            graphene_info, schedule_state=schedule_state
        )
    )


@capture_dauphin_error
def stop_schedule(graphene_info, schedule_selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(schedule_selector, 'schedule_selector', ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)
    instance = graphene_info.context.instance
    schedule_state = instance.stop_schedule_and_update_storage_state(
        repository.get_external_schedule(schedule_selector.schedule_name).get_origin_id()
    )
    return graphene_info.schema.type_named('ScheduleStateResult')(
        schedule_state=graphene_info.schema.type_named('ScheduleState')(
            graphene_info, schedule_state=schedule_state
        )
    )


@capture_dauphin_error
def get_scheduler_or_error(graphene_info):
    instance = graphene_info.context.instance

    if not instance.scheduler:
        raise UserFacingGraphQLError(graphene_info.schema.type_named('SchedulerNotDefinedError')())

    return graphene_info.schema.type_named('Scheduler')()


@capture_dauphin_error
def get_schedule_states_or_error(graphene_info, repository_selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(repository_selector, 'repository_selector', RepositorySelector)

    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    repository_origin_id = repository.get_origin().get_id()
    instance = graphene_info.context.instance

    results = [
        graphene_info.schema.type_named('ScheduleState')(
            graphene_info, schedule_state=schedule_state
        )
        for schedule_state in instance.all_stored_schedule_state(
            repository_origin_id=repository_origin_id
        )
    ]

    return graphene_info.schema.type_named('ScheduleStates')(results=results)


@capture_dauphin_error
def get_schedule_definitions_or_error(graphene_info, repository_selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(repository_selector, 'repository_selector', RepositorySelector)

    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    external_schedules = repository.get_external_schedules()

    results = [
        graphene_info.schema.type_named('ScheduleDefinition')(
            graphene_info, external_schedule=external_schedule
        )
        for external_schedule in external_schedules
    ]

    return graphene_info.schema.type_named('ScheduleDefinitions')(results=results)


def get_schedule_definitions_for_pipeline(graphene_info, pipeline_selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(pipeline_selector, 'pipeline_selector', PipelineSelector)

    location = graphene_info.context.get_repository_location(pipeline_selector.location_name)
    repository = location.get_repository(pipeline_selector.repository_name)
    external_schedules = repository.get_external_schedules()

    return [
        graphene_info.schema.type_named('ScheduleDefinition')(
            graphene_info, external_schedule=external_schedule
        )
        for external_schedule in external_schedules
        if external_schedule.pipeline_name == pipeline_selector.pipeline_name
    ]


@capture_dauphin_error
def get_schedule_definition_or_error(graphene_info, schedule_selector):
    check.inst_param(graphene_info, 'graphene_info', ResolveInfo)
    check.inst_param(schedule_selector, 'schedule_selector', ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)

    external_schedule = repository.get_external_schedule(schedule_selector.schedule_name)
    if not external_schedule:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named('ScheduleDefinitionNotFoundError')(
                schedule_name=schedule_selector.schedule_name
            )
        )

    return graphene_info.schema.type_named('ScheduleDefinition')(
        graphene_info, external_schedule=external_schedule
    )


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
