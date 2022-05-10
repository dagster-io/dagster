from graphql.execution.base import ResolveInfo

import dagster._check as check
from dagster.core.definitions.run_request import InstigatorType
from dagster.core.host_representation import PipelineSelector, RepositorySelector, ScheduleSelector
from dagster.seven import get_current_datetime_in_utc, get_timestamp_from_utc_datetime

from .utils import UserFacingGraphQLError, capture_error


@capture_error
def start_schedule(graphene_info, schedule_selector):
    from ..schema.instigation import GrapheneInstigationState
    from ..schema.schedules import GrapheneScheduleStateResult

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)
    instance = graphene_info.context.instance
    schedule_state = instance.start_schedule(
        repository.get_external_schedule(schedule_selector.schedule_name)
    )
    return GrapheneScheduleStateResult(GrapheneInstigationState(schedule_state))


@capture_error
def stop_schedule(graphene_info, schedule_origin_id, schedule_selector_id):
    from ..schema.instigation import GrapheneInstigationState
    from ..schema.schedules import GrapheneScheduleStateResult

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    instance = graphene_info.context.instance

    external_schedules = {
        job.get_external_origin_id(): job
        for repository_location in graphene_info.context.repository_locations
        for repository in repository_location.get_repositories().values()
        for job in repository.get_external_schedules()
    }

    schedule_state = instance.stop_schedule(
        schedule_origin_id, schedule_selector_id, external_schedules.get(schedule_origin_id)
    )
    return GrapheneScheduleStateResult(GrapheneInstigationState(schedule_state))


@capture_error
def get_scheduler_or_error(graphene_info):
    from ..schema.errors import GrapheneSchedulerNotDefinedError
    from ..schema.schedules import GrapheneScheduler

    instance = graphene_info.context.instance

    if not instance.scheduler:
        raise UserFacingGraphQLError(GrapheneSchedulerNotDefinedError())

    return GrapheneScheduler(scheduler_class=instance.scheduler.__class__.__name__)


@capture_error
def get_schedules_or_error(graphene_info, repository_selector):
    from ..schema.schedules import GrapheneSchedule, GrapheneSchedules

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    external_schedules = repository.get_external_schedules()
    schedule_states_by_name = {
        state.name: state
        for state in graphene_info.context.instance.all_instigator_state(
            repository_origin_id=repository.get_external_origin_id(),
            repository_selector_id=repository_selector.selector_id,
            instigator_type=InstigatorType.SCHEDULE,
        )
    }

    results = [
        GrapheneSchedule(
            external_schedule,
            schedule_states_by_name.get(external_schedule.name),
        )
        for external_schedule in external_schedules
    ]

    return GrapheneSchedules(results=results)


def get_schedules_for_pipeline(graphene_info, pipeline_selector):
    from ..schema.schedules import GrapheneSchedule

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(pipeline_selector, "pipeline_selector", PipelineSelector)

    location = graphene_info.context.get_repository_location(pipeline_selector.location_name)
    repository = location.get_repository(pipeline_selector.repository_name)
    external_schedules = repository.get_external_schedules()

    results = []
    for external_schedule in external_schedules:
        if external_schedule.pipeline_name != pipeline_selector.pipeline_name:
            continue

        schedule_state = graphene_info.context.instance.get_instigator_state(
            external_schedule.get_external_origin_id(),
            external_schedule.selector_id,
        )
        results.append(GrapheneSchedule(external_schedule, schedule_state))

    return results


@capture_error
def get_schedule_or_error(graphene_info, schedule_selector):
    from ..schema.errors import GrapheneScheduleNotFoundError
    from ..schema.schedules import GrapheneSchedule

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)
    location = graphene_info.context.get_repository_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)

    external_schedule = repository.get_external_schedule(schedule_selector.schedule_name)
    if not external_schedule:
        raise UserFacingGraphQLError(
            GrapheneScheduleNotFoundError(schedule_name=schedule_selector.schedule_name)
        )

    schedule_state = graphene_info.context.instance.get_instigator_state(
        external_schedule.get_external_origin_id(), external_schedule.selector_id
    )
    return GrapheneSchedule(external_schedule, schedule_state)


def get_schedule_next_tick(graphene_info, schedule_state):
    from ..schema.instigation import GrapheneFutureInstigationTick

    if not schedule_state.is_running:
        return None

    repository_origin = schedule_state.origin.external_repository_origin
    if not graphene_info.context.has_repository_location(
        repository_origin.repository_location_origin.location_name
    ):
        return None
    repository_location = graphene_info.context.get_repository_location(
        repository_origin.repository_location_origin.location_name
    )
    if not repository_location.has_repository(repository_origin.repository_name):
        return None

    repository = repository_location.get_repository(repository_origin.repository_name)

    if not repository.has_external_schedule(schedule_state.name):
        return None

    external_schedule = repository.get_external_schedule(schedule_state.name)
    time_iter = external_schedule.execution_time_iterator(
        get_timestamp_from_utc_datetime(get_current_datetime_in_utc())
    )

    next_timestamp = next(time_iter).timestamp()
    return GrapheneFutureInstigationTick(schedule_state, next_timestamp)
