import time
from typing import TYPE_CHECKING, Optional, Sequence, Set

import dagster._check as check
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.definitions.selector import (
    JobSubsetSelector,
    RepositorySelector,
    ScheduleSelector,
)
from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.loader import RepositoryScopedBatchLoader
from dagster_graphql.implementation.utils import (
    UserFacingGraphQLError,
    assert_permission,
    assert_permission_for_location,
)
from dagster_graphql.schema.util import ResolveInfo

if TYPE_CHECKING:
    from dagster_graphql.schema.instigation import GrapheneDryRunInstigationTick
    from dagster_graphql.schema.schedules import (
        GrapheneSchedule,
        GrapheneScheduler,
        GrapheneSchedules,
        GrapheneScheduleStateResult,
    )


def start_schedule(
    graphene_info: ResolveInfo, schedule_selector: ScheduleSelector
) -> "GrapheneScheduleStateResult":
    from dagster_graphql.schema.instigation import GrapheneInstigationState
    from dagster_graphql.schema.schedules import GrapheneScheduleStateResult

    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)
    location = graphene_info.context.get_code_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)

    external_schedule = repository.get_external_schedule(schedule_selector.schedule_name)
    stored_state = graphene_info.context.instance.start_schedule(external_schedule)
    schedule_state = external_schedule.get_current_instigator_state(stored_state)

    return GrapheneScheduleStateResult(GrapheneInstigationState(schedule_state))


def stop_schedule(
    graphene_info: ResolveInfo, schedule_origin_id: str, schedule_selector_id: str
) -> "GrapheneScheduleStateResult":
    from dagster_graphql.schema.instigation import GrapheneInstigationState
    from dagster_graphql.schema.schedules import GrapheneScheduleStateResult

    instance = graphene_info.context.instance

    external_schedules = {
        schedule.get_external_origin_id(): schedule
        for repository_location in graphene_info.context.code_locations
        for repository in repository_location.get_repositories().values()
        for schedule in repository.get_external_schedules()
    }

    external_schedule = external_schedules.get(schedule_origin_id)

    if external_schedule:
        assert_permission_for_location(
            graphene_info,
            Permissions.STOP_RUNNING_SCHEDULE,
            external_schedule.selector.location_name,
        )
    else:
        assert_permission(
            graphene_info,
            Permissions.STOP_RUNNING_SCHEDULE,
        )

    schedule_state = instance.stop_schedule(
        schedule_origin_id, schedule_selector_id, external_schedule
    )
    return GrapheneScheduleStateResult(GrapheneInstigationState(schedule_state))


def reset_schedule(
    graphene_info: ResolveInfo, schedule_selector: ScheduleSelector
) -> "GrapheneScheduleStateResult":
    from dagster_graphql.schema.instigation import GrapheneInstigationState
    from dagster_graphql.schema.schedules import GrapheneScheduleStateResult

    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)

    location = graphene_info.context.get_code_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)

    external_schedule = repository.get_external_schedule(schedule_selector.schedule_name)
    stored_state = graphene_info.context.instance.reset_schedule(external_schedule)
    schedule_state = external_schedule.get_current_instigator_state(stored_state)

    return GrapheneScheduleStateResult(GrapheneInstigationState(schedule_state))


def get_scheduler_or_error(graphene_info: ResolveInfo) -> "GrapheneScheduler":
    from dagster_graphql.schema.errors import GrapheneSchedulerNotDefinedError
    from dagster_graphql.schema.schedules import GrapheneScheduler

    instance = graphene_info.context.instance

    if not instance.scheduler:
        raise UserFacingGraphQLError(GrapheneSchedulerNotDefinedError())

    return GrapheneScheduler(scheduler_class=instance.scheduler.__class__.__name__)


def get_schedules_or_error(
    graphene_info: ResolveInfo,
    repository_selector: RepositorySelector,
    instigator_statuses: Optional[Set[InstigatorStatus]] = None,
) -> "GrapheneSchedules":
    from dagster_graphql.schema.schedules import GrapheneSchedule, GrapheneSchedules

    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_code_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    batch_loader = RepositoryScopedBatchLoader(graphene_info.context.instance, repository)
    external_schedules = repository.get_external_schedules()
    schedule_states = graphene_info.context.instance.all_instigator_state(
        repository_origin_id=repository.get_external_origin_id(),
        repository_selector_id=repository_selector.selector_id,
        instigator_type=InstigatorType.SCHEDULE,
        instigator_statuses=instigator_statuses,
    )

    schedule_states_by_name = {state.name: state for state in schedule_states}
    if instigator_statuses:
        filtered = [
            external_schedule
            for external_schedule in external_schedules
            if external_schedule.get_current_instigator_state(
                schedule_states_by_name.get(external_schedule.name)
            ).status
            in instigator_statuses
        ]
    else:
        filtered = external_schedules

    results = [
        GrapheneSchedule(
            schedule, repository, schedule_states_by_name.get(schedule.name), batch_loader
        )
        for schedule in filtered
    ]

    return GrapheneSchedules(results=results)


def get_schedules_for_pipeline(
    graphene_info: ResolveInfo, pipeline_selector: JobSubsetSelector
) -> Sequence["GrapheneSchedule"]:
    from dagster_graphql.schema.schedules import GrapheneSchedule

    check.inst_param(pipeline_selector, "pipeline_selector", JobSubsetSelector)

    location = graphene_info.context.get_code_location(pipeline_selector.location_name)
    repository = location.get_repository(pipeline_selector.repository_name)
    external_schedules = repository.get_external_schedules()

    results = []
    for external_schedule in external_schedules:
        if external_schedule.job_name != pipeline_selector.job_name:
            continue

        schedule_state = graphene_info.context.instance.get_instigator_state(
            external_schedule.get_external_origin_id(),
            external_schedule.selector_id,
        )
        results.append(GrapheneSchedule(external_schedule, repository, schedule_state))

    return results


def get_schedule_or_error(
    graphene_info: ResolveInfo, schedule_selector: ScheduleSelector
) -> "GrapheneSchedule":
    from dagster_graphql.schema.errors import GrapheneScheduleNotFoundError
    from dagster_graphql.schema.schedules import GrapheneSchedule

    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)
    location = graphene_info.context.get_code_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)

    if not repository.has_external_schedule(schedule_selector.schedule_name):
        raise UserFacingGraphQLError(
            GrapheneScheduleNotFoundError(schedule_name=schedule_selector.schedule_name)
        )

    external_schedule = repository.get_external_schedule(schedule_selector.schedule_name)

    schedule_state = graphene_info.context.instance.get_instigator_state(
        external_schedule.get_external_origin_id(), external_schedule.selector_id
    )
    return GrapheneSchedule(external_schedule, repository, schedule_state)


def get_schedule_next_tick(
    graphene_info: ResolveInfo, schedule_state: InstigatorState
) -> Optional["GrapheneDryRunInstigationTick"]:
    from dagster_graphql.schema.instigation import GrapheneDryRunInstigationTick

    if not schedule_state.is_running:
        return None

    repository_origin = schedule_state.origin.repository_origin
    if not graphene_info.context.has_code_location(
        repository_origin.code_location_origin.location_name
    ):
        return None
    code_location = graphene_info.context.get_code_location(
        repository_origin.code_location_origin.location_name
    )
    if not code_location.has_repository(repository_origin.repository_name):
        return None

    repository = code_location.get_repository(repository_origin.repository_name)

    if not repository.has_external_schedule(schedule_state.name):
        return None

    external_schedule = repository.get_external_schedule(schedule_state.name)
    time_iter = external_schedule.execution_time_iterator(time.time())

    next_timestamp = next(time_iter).timestamp()
    return GrapheneDryRunInstigationTick(external_schedule.schedule_selector, next_timestamp)
