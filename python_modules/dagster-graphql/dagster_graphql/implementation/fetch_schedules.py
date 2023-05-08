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
from dagster._seven import get_current_datetime_in_utc, get_timestamp_from_utc_datetime

from dagster_graphql.schema.util import ResolveInfo

from .loader import RepositoryScopedBatchLoader
from .utils import (
    UserFacingGraphQLError,
    assert_permission,
    assert_permission_for_location,
    capture_error,
)

if TYPE_CHECKING:
    from ..schema.instigation import GrapheneDryRunInstigationTick
    from ..schema.schedules import (
        GrapheneSchedule,
        GrapheneScheduler,
        GrapheneSchedules,
        GrapheneScheduleStateResult,
    )


@capture_error
def start_schedule(
    graphene_info: ResolveInfo, schedule_selector: ScheduleSelector
) -> "GrapheneScheduleStateResult":
    from ..schema.instigation import GrapheneInstigationState
    from ..schema.schedules import GrapheneScheduleStateResult

    check.inst_param(schedule_selector, "schedule_selector", ScheduleSelector)
    location = graphene_info.context.get_code_location(schedule_selector.location_name)
    repository = location.get_repository(schedule_selector.repository_name)
    instance = graphene_info.context.instance
    schedule_state = instance.start_schedule(
        repository.get_external_schedule(schedule_selector.schedule_name)
    )
    return GrapheneScheduleStateResult(GrapheneInstigationState(schedule_state))


@capture_error
def stop_schedule(
    graphene_info: ResolveInfo, schedule_origin_id: str, schedule_selector_id: str
) -> "GrapheneScheduleStateResult":
    from ..schema.instigation import GrapheneInstigationState
    from ..schema.schedules import GrapheneScheduleStateResult

    instance = graphene_info.context.instance

    external_schedules = {
        job.get_external_origin_id(): job
        for repository_location in graphene_info.context.code_locations
        for repository in repository_location.get_repositories().values()
        for job in repository.get_external_schedules()
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


@capture_error
def get_scheduler_or_error(graphene_info: ResolveInfo) -> "GrapheneScheduler":
    from ..schema.errors import GrapheneSchedulerNotDefinedError
    from ..schema.schedules import GrapheneScheduler

    instance = graphene_info.context.instance

    if not instance.scheduler:
        raise UserFacingGraphQLError(GrapheneSchedulerNotDefinedError())

    return GrapheneScheduler(scheduler_class=instance.scheduler.__class__.__name__)


@capture_error
def get_schedules_or_error(
    graphene_info: ResolveInfo,
    repository_selector: RepositorySelector,
    instigator_statuses: Optional[Set[InstigatorStatus]] = None,
) -> "GrapheneSchedules":
    from ..schema.schedules import GrapheneSchedule, GrapheneSchedules

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
        GrapheneSchedule(schedule, schedule_states_by_name.get(schedule.name), batch_loader)
        for schedule in filtered
    ]

    return GrapheneSchedules(results=results)


def get_schedules_for_pipeline(
    graphene_info: ResolveInfo, pipeline_selector: JobSubsetSelector
) -> Sequence["GrapheneSchedule"]:
    from ..schema.schedules import GrapheneSchedule

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
        results.append(GrapheneSchedule(external_schedule, schedule_state))

    return results


@capture_error
def get_schedule_or_error(
    graphene_info: ResolveInfo, schedule_selector: ScheduleSelector
) -> "GrapheneSchedule":
    from ..schema.errors import GrapheneScheduleNotFoundError
    from ..schema.schedules import GrapheneSchedule

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
    return GrapheneSchedule(external_schedule, schedule_state)


def get_schedule_next_tick(
    graphene_info: ResolveInfo, schedule_state: InstigatorState
) -> Optional["GrapheneDryRunInstigationTick"]:
    from ..schema.instigation import GrapheneDryRunInstigationTick

    if not schedule_state.is_running:
        return None

    repository_origin = schedule_state.origin.external_repository_origin
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
    time_iter = external_schedule.execution_time_iterator(
        get_timestamp_from_utc_datetime(get_current_datetime_in_utc())
    )

    next_timestamp = next(time_iter).timestamp()
    return GrapheneDryRunInstigationTick(external_schedule.schedule_selector, next_timestamp)
