import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

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
    from dagster_graphql.schema.errors import GrapheneScheduleNotFoundError
    from dagster_graphql.schema.instigation import GrapheneInstigationState
    from dagster_graphql.schema.schedules import GrapheneScheduleStateResult

    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)
    schedule = graphene_info.context.get_schedule(schedule_selector)
    if not schedule:
        raise UserFacingGraphQLError(
            GrapheneScheduleNotFoundError(schedule_name=schedule_selector.schedule_name)
        )

    stored_state = graphene_info.context.instance.start_schedule(schedule)
    schedule_state = schedule.get_current_instigator_state(stored_state)

    return GrapheneScheduleStateResult(GrapheneInstigationState(schedule_state))


def stop_schedule(
    graphene_info: ResolveInfo, schedule_origin_id: str, schedule_selector_id: str
) -> "GrapheneScheduleStateResult":
    from dagster_graphql.schema.instigation import GrapheneInstigationState
    from dagster_graphql.schema.schedules import GrapheneScheduleStateResult

    instance = graphene_info.context.instance

    schedules = {
        schedule.get_remote_origin_id(): schedule
        for repository_location in graphene_info.context.code_locations
        for repository in repository_location.get_repositories().values()
        for schedule in repository.get_schedules()
    }

    schedule = schedules.get(schedule_origin_id)

    if schedule:
        assert_permission_for_location(
            graphene_info,
            Permissions.STOP_RUNNING_SCHEDULE,
            schedule.selector.location_name,
        )
    else:
        assert_permission(
            graphene_info,
            Permissions.STOP_RUNNING_SCHEDULE,
        )

    schedule_state = instance.stop_schedule(schedule_origin_id, schedule_selector_id, schedule)
    return GrapheneScheduleStateResult(GrapheneInstigationState(schedule_state))


def reset_schedule(
    graphene_info: ResolveInfo, schedule_selector: ScheduleSelector
) -> "GrapheneScheduleStateResult":
    from dagster_graphql.schema.instigation import GrapheneInstigationState
    from dagster_graphql.schema.schedules import GrapheneScheduleStateResult

    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)

    location = graphene_info.context.get_code_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)

    schedule = repository.get_schedule(schedule_selector.schedule_name)
    stored_state = graphene_info.context.instance.reset_schedule(schedule)
    schedule_state = schedule.get_current_instigator_state(stored_state)

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
    instigator_statuses: Optional[set[InstigatorStatus]] = None,
) -> "GrapheneSchedules":
    from dagster_graphql.schema.schedules import GrapheneSchedule, GrapheneSchedules

    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location = graphene_info.context.get_code_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    batch_loader = RepositoryScopedBatchLoader(graphene_info.context.instance, repository)
    schedules = repository.get_schedules()
    schedule_states = graphene_info.context.instance.all_instigator_state(
        repository_origin_id=repository.get_remote_origin_id(),
        repository_selector_id=repository_selector.selector_id,
        instigator_type=InstigatorType.SCHEDULE,
        instigator_statuses=instigator_statuses,
    )

    schedule_states_by_name = {state.name: state for state in schedule_states}
    if instigator_statuses:
        filtered = [
            schedule
            for schedule in schedules
            if schedule.get_current_instigator_state(
                schedule_states_by_name.get(schedule.name)
            ).status
            in instigator_statuses
        ]
    else:
        filtered = schedules

    results = [
        GrapheneSchedule(
            schedule,
            schedule_states_by_name.get(schedule.name),
            batch_loader,
        )
        for schedule in filtered
    ]

    return GrapheneSchedules(results=results)


def get_schedules_for_job(
    graphene_info: ResolveInfo, selector: JobSubsetSelector
) -> Sequence["GrapheneSchedule"]:
    from dagster_graphql.schema.schedules import GrapheneSchedule

    check.inst_param(selector, "selector", JobSubsetSelector)

    schedules = graphene_info.context.get_schedules_targeting_job(selector)

    results = []
    for schedule in schedules:
        schedule_state = graphene_info.context.instance.get_instigator_state(
            schedule.get_remote_origin_id(),
            schedule.selector_id,
        )

        results.append(GrapheneSchedule(schedule, schedule_state))

    return results


def get_schedule_or_error(
    graphene_info: ResolveInfo, schedule_selector: ScheduleSelector
) -> "GrapheneSchedule":
    from dagster_graphql.schema.errors import GrapheneScheduleNotFoundError
    from dagster_graphql.schema.schedules import GrapheneSchedule

    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)

    schedule = graphene_info.context.get_schedule(schedule_selector)
    if not schedule:
        raise UserFacingGraphQLError(
            GrapheneScheduleNotFoundError(schedule_name=schedule_selector.schedule_name)
        )

    schedule_state = graphene_info.context.instance.get_instigator_state(
        schedule.get_remote_origin_id(), schedule.selector_id
    )
    return GrapheneSchedule(schedule, schedule_state)


def get_schedule_next_tick(
    graphene_info: ResolveInfo, schedule_state: InstigatorState
) -> Optional["GrapheneDryRunInstigationTick"]:
    from dagster_graphql.schema.instigation import GrapheneDryRunInstigationTick

    if not schedule_state.is_running:
        return None

    repository_origin = schedule_state.origin.repository_origin
    selector = ScheduleSelector(
        location_name=repository_origin.code_location_origin.location_name,
        repository_name=repository_origin.repository_name,
        schedule_name=schedule_state.name,
    )

    schedule = graphene_info.context.get_schedule(selector)
    if not schedule:
        return None

    time_iter = schedule.execution_time_iterator(time.time())

    next_timestamp = next(time_iter).timestamp()
    return GrapheneDryRunInstigationTick(schedule.schedule_selector, next_timestamp)
