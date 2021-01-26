import graphene
from dagster import check
from dagster.core.host_representation import ExternalSchedule, ScheduleSelector
from dagster.core.host_representation.selector import RepositorySelector
from dagster.core.scheduler.job import JobTickStatsSnapshot

from ...implementation.fetch_schedules import (
    reconcile_scheduler_state,
    start_schedule,
    stop_schedule,
)
from ..errors import (
    GraphenePythonError,
    GrapheneRepositoryNotFoundError,
    GrapheneScheduleNotFoundError,
    GrapheneSchedulerNotDefinedError,
)
from ..inputs import GrapheneRepositorySelector, GrapheneScheduleSelector
from ..jobs import GrapheneJobState
from .schedules import (
    GrapheneSchedule,
    GrapheneScheduleOrError,
    GrapheneSchedules,
    GrapheneSchedulesOrError,
)
from .ticks import GrapheneJobTickStatus


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


class GrapheneScheduleTickStatsSnapshot(graphene.ObjectType):
    ticks_started = graphene.NonNull(graphene.Int)
    ticks_succeeded = graphene.NonNull(graphene.Int)
    ticks_skipped = graphene.NonNull(graphene.Int)
    ticks_failed = graphene.NonNull(graphene.Int)

    class Meta:
        name = "ScheduleTickStatsSnapshot"

    def __init__(self, stats):
        super().__init__(
            ticks_started=stats.ticks_started,
            ticks_succeeded=stats.ticks_succeeded,
            ticks_skipped=stats.ticks_skipped,
            ticks_failed=stats.ticks_failed,
        )
        self._stats = check.inst_param(stats, "stats", JobTickStatsSnapshot)


class GrapheneReconcileSchedulerStateSuccess(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        name = "ReconcileSchedulerStateSuccess"


class GrapheneReconcileSchedulerStateMutationResult(graphene.Union):
    class Meta:
        types = (GraphenePythonError, GrapheneReconcileSchedulerStateSuccess)
        name = "ReconcileSchedulerStateMutationResult"


class GrapheneReconcileSchedulerStateMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneReconcileSchedulerStateMutationResult)

    class Arguments:
        repository_selector = graphene.NonNull(GrapheneRepositorySelector)

    class Meta:
        name = "ReconcileSchedulerStateMutation"

    def mutate(self, graphene_info, repository_selector):
        return reconcile_scheduler_state(
            graphene_info, RepositorySelector.from_graphql_input(repository_selector)
        )


class GrapheneScheduleStateResult(graphene.ObjectType):
    scheduleState = graphene.NonNull(GrapheneJobState)

    class Meta:
        name = "ScheduleStateResult"


class GrapheneScheduleMutationResult(graphene.Union):
    class Meta:
        types = (GraphenePythonError, GrapheneScheduleStateResult)
        name = "ScheduleMutationResult"


class GrapheneStartScheduleMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneScheduleMutationResult)

    class Arguments:
        schedule_selector = graphene.NonNull(GrapheneScheduleSelector)

    class Meta:
        name = "StartScheduleMutation"

    def mutate(self, graphene_info, schedule_selector):
        return start_schedule(graphene_info, ScheduleSelector.from_graphql_input(schedule_selector))


class GrapheneStopRunningScheduleMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneScheduleMutationResult)

    class Arguments:
        schedule_origin_id = graphene.NonNull(graphene.String)

    class Meta:
        name = "StopRunningScheduleMutation"

    def mutate(self, graphene_info, schedule_origin_id):
        return stop_schedule(graphene_info, schedule_origin_id)


def types():
    from .ticks import (
        GrapheneScheduleTick,
        GrapheneScheduleTickFailureData,
        GrapheneScheduleTickSpecificData,
        GrapheneScheduleTickSuccessData,
    )

    # Double check mutations don't appear twice
    return [
        GrapheneJobTickStatus,
        GrapheneReconcileSchedulerStateMutation,
        GrapheneReconcileSchedulerStateMutationResult,
        GrapheneReconcileSchedulerStateSuccess,
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
        GrapheneScheduleTickStatsSnapshot,
        GrapheneScheduleTickSuccessData,
        GrapheneStartScheduleMutation,
        GrapheneStopRunningScheduleMutation,
    ]
