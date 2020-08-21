from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_schedules import (
    reconcile_scheduler_state,
    start_schedule,
    stop_schedule,
)
from dagster_graphql.schema.errors import (
    DauphinPythonError,
    DauphinRepositoryNotFoundError,
    DauphinScheduleDefinitionNotFoundError,
    DauphinScheduleNotFoundError,
    DauphinSchedulerNotDefinedError,
)

from dagster import check
from dagster.core.host_representation import ExternalSchedule, ScheduleSelector
from dagster.core.host_representation.selector import RepositorySelector
from dagster.core.scheduler import ScheduleState, ScheduleTickStatus
from dagster.core.scheduler.scheduler import ScheduleTickStatsSnapshot
from dagster.core.storage.pipeline_run import PipelineRunsFilter

from .schedule_definition import (
    DapuphinScheduleDefinitionOrError,
    DauphinScheduleDefinition,
    DauphinScheduleDefinitions,
    DauphinScheduleDefintionsOrError,
)
from .schedule_state import (
    DapuphinScheduleStateOrError,
    DauphinScheduleState,
    DauphinScheduleStates,
    DauphinScheduleStatesOrError,
)


class DauphinScheduleStatus(dauphin.Enum):
    class Meta(object):
        name = "ScheduleStatus"

    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ENDED = "ENDED"


class DauphinSchedulerOrError(dauphin.Union):
    class Meta(object):
        name = "SchedulerOrError"
        types = ("Scheduler", DauphinSchedulerNotDefinedError, "PythonError")


DauphinScheduleTickStatus = dauphin.Enum.from_enum(ScheduleTickStatus)


class DauphinScheduleTick(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleTick"

    tick_id = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull("ScheduleTickStatus")
    timestamp = dauphin.NonNull(dauphin.Float)
    tick_specific_data = dauphin.Field("ScheduleTickSpecificData")


class DauphinScheduleTickSuccessData(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleTickSuccessData"

    run = dauphin.Field("PipelineRun")


class DauphinScheduleTickFailureData(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleTickFailureData"

    error = dauphin.NonNull("PythonError")


class DauphinScheduleTickSpecificData(dauphin.Union):
    class Meta(object):
        name = "ScheduleTickSpecificData"
        types = (
            DauphinScheduleTickSuccessData,
            DauphinScheduleTickFailureData,
        )


class DauphinScheduleTickStatsSnapshot(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleTickStatsSnapshot"

    ticks_started = dauphin.NonNull(dauphin.Int)
    ticks_succeeded = dauphin.NonNull(dauphin.Int)
    ticks_skipped = dauphin.NonNull(dauphin.Int)
    ticks_failed = dauphin.NonNull(dauphin.Int)

    def __init__(self, stats):
        super(DauphinScheduleTickStatsSnapshot, self).__init__(
            ticks_started=stats.ticks_started,
            ticks_succeeded=stats.ticks_succeeded,
            ticks_skipped=stats.ticks_skipped,
            ticks_failed=stats.ticks_failed,
        )
        self._stats = check.inst_param(stats, "stats", ScheduleTickStatsSnapshot)


class DauphinScheduler(dauphin.ObjectType):
    class Meta(object):
        name = "Scheduler"

    scheduler_class = dauphin.String()


class DauphinReconcileSchedulerStateSuccess(dauphin.ObjectType):
    class Meta(object):
        name = "ReconcileSchedulerStateSuccess"

    message = dauphin.NonNull(dauphin.String)


class DauphinReconcilScheduleStateMutationResult(dauphin.Union):
    class Meta(object):
        name = "ReconcileSchedulerStateMutationResult"
        types = (DauphinPythonError, DauphinReconcileSchedulerStateSuccess)


class DauphinReconcileSchedulerStateMutation(dauphin.Mutation):
    class Meta(object):
        name = "ReconcileSchedulerStateMutation"

    class Arguments(object):
        repository_selector = dauphin.NonNull("RepositorySelector")

    Output = dauphin.NonNull("ReconcileSchedulerStateMutationResult")

    def mutate(self, graphene_info, repository_selector):
        return reconcile_scheduler_state(
            graphene_info, RepositorySelector.from_graphql_input(repository_selector)
        )


class DauphinScheduleStateResult(dauphin.ObjectType):
    class Meta(object):
        name = "ScheduleStateResult"

    schedule_state = dauphin.NonNull("ScheduleState")


class DauphinScheduleMutationResult(dauphin.Union):
    class Meta(object):
        name = "ScheduleMutationResult"
        types = (DauphinPythonError, DauphinScheduleStateResult)


class DauphinStartScheduleMutation(dauphin.Mutation):
    class Meta(object):
        name = "StartScheduleMutation"

    class Arguments(object):
        schedule_selector = dauphin.NonNull("ScheduleSelector")

    Output = dauphin.NonNull("ScheduleMutationResult")

    def mutate(self, graphene_info, schedule_selector):
        return start_schedule(graphene_info, ScheduleSelector.from_graphql_input(schedule_selector))


class DauphinStopRunningScheduleMutation(dauphin.Mutation):
    class Meta(object):
        name = "StopRunningScheduleMutation"

    class Arguments(object):
        schedule_origin_id = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull("ScheduleMutationResult")

    def mutate(self, graphene_info, schedule_origin_id):
        return stop_schedule(graphene_info, schedule_origin_id)
