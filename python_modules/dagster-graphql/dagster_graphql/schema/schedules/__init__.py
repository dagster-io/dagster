import graphene
from dagster._core.definitions.selector import ScheduleSelector
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.schema.util import ResolveInfo

from ...implementation.fetch_schedules import start_schedule, stop_schedule
from ...implementation.utils import (
    assert_permission_for_location,
    capture_error,
    require_permission_check,
)
from ..errors import (
    GraphenePythonError,
    GrapheneSchedulerNotDefinedError,
    GrapheneUnauthorizedError,
)
from ..inputs import GrapheneScheduleSelector
from ..instigation import GrapheneInstigationState
from .schedules import (
    GrapheneSchedule,
    GrapheneScheduleOrError,
    GrapheneSchedules,
    GrapheneSchedulesOrError,
)
from .ticks import GrapheneInstigationTickStatus


class GrapheneScheduleStatus(graphene.Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ENDED = "ENDED"

    class Meta:
        name = "ScheduleStatus"


class GrapheneScheduler(graphene.ObjectType):
    scheduler_class = graphene.String()

    class Meta:
        name = "Scheduler"


class GrapheneSchedulerOrError(graphene.Union):
    class Meta:
        types = (GrapheneScheduler, GrapheneSchedulerNotDefinedError, GraphenePythonError)
        name = "SchedulerOrError"


class GrapheneScheduleStateResult(graphene.ObjectType):
    scheduleState = graphene.NonNull(GrapheneInstigationState)

    class Meta:
        name = "ScheduleStateResult"


class GrapheneScheduleMutationResult(graphene.Union):
    class Meta:
        types = (GraphenePythonError, GrapheneUnauthorizedError, GrapheneScheduleStateResult)
        name = "ScheduleMutationResult"


class GrapheneStartScheduleMutation(graphene.Mutation):
    """Enable a schedule to launch runs for a job at a fixed interval."""

    Output = graphene.NonNull(GrapheneScheduleMutationResult)

    class Arguments:
        schedule_selector = graphene.NonNull(GrapheneScheduleSelector)

    class Meta:
        name = "StartScheduleMutation"

    @capture_error
    @require_permission_check(Permissions.START_SCHEDULE)
    def mutate(self, graphene_info: ResolveInfo, schedule_selector):
        selector = ScheduleSelector.from_graphql_input(schedule_selector)
        assert_permission_for_location(
            graphene_info, Permissions.START_SCHEDULE, selector.location_name
        )
        return start_schedule(graphene_info, selector)


class GrapheneStopRunningScheduleMutation(graphene.Mutation):
    """Disable a schedule from launching runs for a job."""

    Output = graphene.NonNull(GrapheneScheduleMutationResult)

    class Arguments:
        schedule_origin_id = graphene.NonNull(graphene.String)
        schedule_selector_id = graphene.NonNull(graphene.String)

    class Meta:
        name = "StopRunningScheduleMutation"

    @capture_error
    @require_permission_check(Permissions.STOP_RUNNING_SCHEDULE)
    def mutate(self, graphene_info: ResolveInfo, schedule_origin_id, schedule_selector_id):
        return stop_schedule(graphene_info, schedule_origin_id, schedule_selector_id)


def types():
    from .ticks import (
        GrapheneScheduleTick,
        GrapheneScheduleTickFailureData,
        GrapheneScheduleTickSpecificData,
        GrapheneScheduleTickSuccessData,
    )

    # Double check mutations don't appear twice
    return [
        GrapheneInstigationTickStatus,
        GrapheneSchedule,
        GrapheneScheduleMutationResult,
        GrapheneScheduleOrError,
        GrapheneScheduler,
        GrapheneSchedulerOrError,
        GrapheneSchedules,
        GrapheneSchedulesOrError,
        GrapheneScheduleStateResult,
        GrapheneScheduleStatus,
        GrapheneScheduleTick,
        GrapheneScheduleTickFailureData,
        GrapheneScheduleTickSpecificData,
        GrapheneScheduleTickSuccessData,
        GrapheneStartScheduleMutation,
        GrapheneStopRunningScheduleMutation,
    ]
