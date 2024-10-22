from typing import Optional

import graphene
from dagster._core.definitions.selector import ScheduleSelector
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.remote_representation.external import CompoundID
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.fetch_schedules import (
    reset_schedule,
    start_schedule,
    stop_schedule,
)
from dagster_graphql.implementation.utils import (
    assert_permission_for_location,
    capture_error,
    require_permission_check,
)
from dagster_graphql.schema.errors import (
    GraphenePythonError,
    GrapheneSchedulerNotDefinedError,
    GrapheneUnauthorizedError,
)
from dagster_graphql.schema.inputs import GrapheneScheduleSelector
from dagster_graphql.schema.instigation import GrapheneInstigationState
from dagster_graphql.schema.schedules.schedules import (
    GrapheneSchedule,
    GrapheneScheduleNotFoundError,
    GrapheneScheduleOrError,
    GrapheneSchedules,
    GrapheneSchedulesOrError,
)
from dagster_graphql.schema.schedules.ticks import GrapheneInstigationTickStatus
from dagster_graphql.schema.util import ResolveInfo


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
        types = (
            GraphenePythonError,
            GrapheneUnauthorizedError,
            GrapheneScheduleStateResult,
            GrapheneScheduleNotFoundError,
        )
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
        id = graphene.Argument(graphene.String)  # Schedule / InstigationState id
        schedule_origin_id = graphene.Argument(graphene.String)
        schedule_selector_id = graphene.Argument(graphene.String)

    class Meta:
        name = "StopRunningScheduleMutation"

    @capture_error
    @require_permission_check(Permissions.STOP_RUNNING_SCHEDULE)
    def mutate(
        self,
        graphene_info: ResolveInfo,
        id: Optional[str] = None,
        schedule_origin_id: Optional[str] = None,
        schedule_selector_id: Optional[str] = None,
    ):
        if id:
            cid = CompoundID.from_string(id)
            schedule_origin_id = cid.remote_origin_id
            schedule_selector_id = cid.selector_id
        elif schedule_origin_id and CompoundID.is_valid_string(schedule_origin_id):
            # cross-push handle if InstigationState.id being passed through as origin id
            cid = CompoundID.from_string(schedule_origin_id)
            schedule_origin_id = cid.remote_origin_id
            schedule_selector_id = cid.selector_id
        elif schedule_origin_id is None or schedule_selector_id is None:
            raise DagsterInvariantViolationError(
                "Must specify id or scheduleOriginId and scheduleSelectorId"
            )

        return stop_schedule(graphene_info, schedule_origin_id, schedule_selector_id)


class GrapheneResetScheduleMutation(graphene.Mutation):
    """Reset a schedule to its status defined in code, otherwise disable it from launching runs for a job."""

    Output = graphene.NonNull(GrapheneScheduleMutationResult)

    class Arguments:
        schedule_selector = graphene.NonNull(GrapheneScheduleSelector)

    class Meta:
        name = "ResetScheduleMutation"

    @capture_error
    @require_permission_check(Permissions.START_SCHEDULE)
    @require_permission_check(Permissions.STOP_RUNNING_SCHEDULE)
    def mutate(self, graphene_info: ResolveInfo, schedule_selector):
        selector = ScheduleSelector.from_graphql_input(schedule_selector)

        assert_permission_for_location(
            graphene_info, Permissions.START_SCHEDULE, selector.location_name
        )
        assert_permission_for_location(
            graphene_info, Permissions.STOP_RUNNING_SCHEDULE, selector.location_name
        )

        return reset_schedule(graphene_info, selector)


def types():
    from dagster_graphql.schema.schedules.ticks import (
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
        GrapheneResetScheduleMutation,
    ]
