import yaml
from dagster import check
from dagster.core.host_representation import (
    ExternalSchedule,
    ExternalScheduleExecutionData,
    PipelineSelector,
    RepositorySelector,
    ScheduleSelector,
)
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
        schedule_state=graphene_info.schema.type_named("ScheduleState")(
            graphene_info, schedule_state=schedule_state
        )
    )


@capture_dauphin_error
def stop_schedule(graphene_info, schedule_origin_id):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    instance = graphene_info.context.instance
    schedule_state = instance.stop_schedule_and_update_storage_state(schedule_origin_id)
    return graphene_info.schema.type_named("ScheduleStateResult")(
        schedule_state=graphene_info.schema.type_named("ScheduleState")(
            graphene_info, schedule_state=schedule_state
        )
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
def get_schedule_states_or_error(
    graphene_info, repository_selector, with_no_schedule_definition_filter=None
):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.opt_inst_param(repository_selector, "repository_selector", RepositorySelector)
    check.opt_bool_param(
        with_no_schedule_definition_filter, "with_no_schedule_definition_filter", default=False
    )

    instance = graphene_info.context.instance
    if not repository_selector:
        # Return all schedule states
        results = [
            graphene_info.schema.type_named("ScheduleState")(
                graphene_info, schedule_state=schedule_state
            )
            for schedule_state in instance.all_stored_schedule_state()
        ]
        return graphene_info.schema.type_named("ScheduleStates")(results=results)

    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    repository_origin_id = repository.get_origin().get_id()
    instance = graphene_info.context.instance

    results = [
        graphene_info.schema.type_named("ScheduleState")(
            graphene_info, schedule_state=schedule_state
        )
        for schedule_state in instance.all_stored_schedule_state(
            repository_origin_id=repository_origin_id
        )
    ]

    if with_no_schedule_definition_filter:
        external_schedules = repository.get_external_schedules()
        external_schedule_origin_ids = set(
            external_schedule.get_origin_id() for external_schedule in external_schedules
        )

        # Filter for all schedule states for which there are no matching external schedules with the
        # same origin id
        results = list(
            filter(
                lambda schedule_state: schedule_state.schedule_origin_id
                not in external_schedule_origin_ids,
                results,
            )
        )

    return graphene_info.schema.type_named("ScheduleStates")(results=results)


@capture_dauphin_error
def get_schedule_definitions_or_error(graphene_info, repository_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    external_schedules = repository.get_external_schedules()

    results = [
        graphene_info.schema.type_named("ScheduleDefinition")(
            graphene_info, external_schedule=external_schedule
        )
        for external_schedule in external_schedules
    ]

    return graphene_info.schema.type_named("ScheduleDefinitions")(results=results)


def get_schedule_definitions_for_pipeline(graphene_info, pipeline_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(pipeline_selector, "pipeline_selector", PipelineSelector)

    location = graphene_info.context.get_repository_location(pipeline_selector.location_name)
    repository = location.get_repository(pipeline_selector.repository_name)
    external_schedules = repository.get_external_schedules()

    return [
        graphene_info.schema.type_named("ScheduleDefinition")(
            graphene_info, external_schedule=external_schedule
        )
        for external_schedule in external_schedules
        if external_schedule.pipeline_name == pipeline_selector.pipeline_name
    ]


@capture_dauphin_error
def get_schedule_definition_or_error(graphene_info, schedule_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)

    external_schedule = repository.get_external_schedule(schedule_selector.schedule_name)
    if not external_schedule:
        raise UserFacingGraphQLError(
            graphene_info.schema.type_named("ScheduleDefinitionNotFoundError")(
                schedule_name=schedule_selector.schedule_name
            )
        )

    return graphene_info.schema.type_named("ScheduleDefinition")(
        graphene_info, external_schedule=external_schedule
    )


def get_schedule_config(graphene_info, external_schedule):
    check.inst_param(external_schedule, "external_schedule", ExternalSchedule)
    handle = external_schedule.handle.repository_handle

    result = graphene_info.context.get_external_schedule_execution_data(
        handle, external_schedule.name
    )
    if isinstance(result, ExternalScheduleExecutionData):
        run_config_yaml = yaml.safe_dump(result.run_config, default_flow_style=False)
        return graphene_info.schema.type_named("ScheduleRunConfig")(
            yaml=run_config_yaml if run_config_yaml else ""
        )
    else:
        return graphene_info.schema.type_named("PythonError")(result.error)
