from dagster import check
from dagster.core.host_representation import ExternalSchedule, ScheduleSelector
from dagster.core.host_representation.selector import RepositorySelector
from dagster.core.scheduler.job import JobTickStatsSnapshot, JobTickStatus
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster_graphql import dauphin
from dagster_graphql.implementation.fetch_schedules import (
    reconcile_scheduler_state,
    start_schedule,
    stop_schedule,
)
from dagster_graphql.schema.errors import (
    DauphinPythonError,
    DauphinRepositoryNotFoundError,
    DauphinScheduleNotFoundError,
    DauphinSchedulerNotDefinedError,
)

from .schedules import (
    DauphinSchedule,
    DauphinScheduleOrError,
    DauphinSchedules,
    DauphinSchedulesOrError,
)


class DauphinScheduleStatus(dauphin.Enum):
    class Meta:
        name = "ScheduleStatus"

    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ENDED = "ENDED"


class DauphinSchedulerOrError(dauphin.Union):
    class Meta:
        name = "SchedulerOrError"
        types = ("Scheduler", DauphinSchedulerNotDefinedError, "PythonError")


DauphinJobTickStatus = dauphin.Enum.from_enum(JobTickStatus)


class DauphinScheduleTick(dauphin.ObjectType):
    class Meta:
        name = "ScheduleTick"

    tick_id = dauphin.NonNull(dauphin.String)
    status = dauphin.NonNull("JobTickStatus")
    timestamp = dauphin.NonNull(dauphin.Float)
    tick_specific_data = dauphin.Field("ScheduleTickSpecificData")


class DauphinScheduleTickSuccessData(dauphin.ObjectType):
    class Meta:
        name = "ScheduleTickSuccessData"

    run = dauphin.Field("PipelineRun")


class DauphinScheduleTickFailureData(dauphin.ObjectType):
    class Meta:
        name = "ScheduleTickFailureData"

    error = dauphin.NonNull("PythonError")


class DauphinScheduleTickSpecificData(dauphin.Union):
    class Meta:
        name = "ScheduleTickSpecificData"
        types = (
            DauphinScheduleTickSuccessData,
            DauphinScheduleTickFailureData,
        )


class DauphinScheduleTickStatsSnapshot(dauphin.ObjectType):
    class Meta:
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
        self._stats = check.inst_param(stats, "stats", JobTickStatsSnapshot)


class DauphinScheduler(dauphin.ObjectType):
    class Meta:
        name = "Scheduler"

    scheduler_class = dauphin.String()


class DauphinReconcileSchedulerStateSuccess(dauphin.ObjectType):
    class Meta:
        name = "ReconcileSchedulerStateSuccess"

    message = dauphin.NonNull(dauphin.String)


class DauphinReconcilScheduleStateMutationResult(dauphin.Union):
    class Meta:
        name = "ReconcileSchedulerStateMutationResult"
        types = (DauphinPythonError, DauphinReconcileSchedulerStateSuccess)


class DauphinReconcileSchedulerStateMutation(dauphin.Mutation):
    class Meta:
        name = "ReconcileSchedulerStateMutation"

    class Arguments:
        repository_selector = dauphin.NonNull("RepositorySelector")

    Output = dauphin.NonNull("ReconcileSchedulerStateMutationResult")

    def mutate(self, graphene_info, repository_selector):
        return reconcile_scheduler_state(
            graphene_info, RepositorySelector.from_graphql_input(repository_selector)
        )


class DauphinScheduleStateResult(dauphin.ObjectType):
    class Meta:
        name = "ScheduleStateResult"

    scheduleState = dauphin.NonNull("JobState")


class DauphinScheduleMutationResult(dauphin.Union):
    class Meta:
        name = "ScheduleMutationResult"
        types = (DauphinPythonError, DauphinScheduleStateResult)


class DauphinStartScheduleMutation(dauphin.Mutation):
    class Meta:
        name = "StartScheduleMutation"

    class Arguments:
        schedule_selector = dauphin.NonNull("ScheduleSelector")

    Output = dauphin.NonNull("ScheduleMutationResult")

    def mutate(self, graphene_info, schedule_selector):
        return start_schedule(graphene_info, ScheduleSelector.from_graphql_input(schedule_selector))


class DauphinStopRunningScheduleMutation(dauphin.Mutation):
    class Meta:
        name = "StopRunningScheduleMutation"

    class Arguments:
        schedule_origin_id = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull("ScheduleMutationResult")

    def mutate(self, graphene_info, schedule_origin_id):
        return stop_schedule(graphene_info, schedule_origin_id)
