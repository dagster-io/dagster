# pylint: disable=missing-graphene-docstring
import graphene

import dagster._check as check
from dagster.core.host_representation import ExternalSchedule, ScheduleSelector
from dagster.core.host_representation.selector import RepositorySelector
from dagster.core.workspace.permissions import Permissions

from ...implementation.fetch_schedules import start_schedule, stop_schedule
from ...implementation.utils import capture_error, check_permission
from ..errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneScheduleNotFoundError,
    GrapheneSchedulerNotDefinedError,
    GrapheneUnauthorizedError,
)
from ..inputs import GrapheneRepositorySelector, GrapheneScheduleSelector
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
    Output = graphene.NonNull(GrapheneScheduleMutationResult)

    class Arguments:
        schedule_selector = graphene.NonNull(GrapheneScheduleSelector)

    class Meta:
        name = "StartScheduleMutation"

    @capture_error
    @check_permission(Permissions.START_SCHEDULE)
    def mutate(self, graphene_info, schedule_selector):
        return start_schedule(graphene_info, ScheduleSelector.from_graphql_input(schedule_selector))


class GrapheneStopRunningScheduleMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneScheduleMutationResult)

    class Arguments:
        schedule_origin_id = graphene.NonNull(graphene.String)
        schedule_selector_id = graphene.NonNull(graphene.String)

    class Meta:
        name = "StopRunningScheduleMutation"

    @capture_error
    @check_permission(Permissions.STOP_RUNNING_SCHEDULE)
    def mutate(self, graphene_info, schedule_origin_id, schedule_selector_id):
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
