from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.scheduler.job import (
    JobState,
    JobStatus,
    JobTick,
    JobTickStatus,
    ScheduleJobData,
    SensorJobData,
)
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster_graphql import dauphin


class DauphinJobTick(dauphin.ObjectType):
    class Meta:
        name = "JobTick"

    id = dauphin.NonNull(dauphin.ID)
    status = dauphin.NonNull("JobTickStatus")
    timestamp = dauphin.NonNull(dauphin.Float)
    runIds = dauphin.non_null_list(dauphin.String)
    error = dauphin.Field("PythonError")
    skipReason = dauphin.String()

    runs = dauphin.non_null_list("PipelineRun")

    def __init__(self, _, job_tick):
        self._job_tick = check.inst_param(job_tick, "job_tick", JobTick)

        super(DauphinJobTick, self).__init__(
            status=job_tick.status,
            timestamp=job_tick.timestamp,
            runIds=job_tick.run_ids,
            error=job_tick.error,
            skipReason=job_tick.skip_reason,
        )

    def resolve_id(self, _):
        return "%s:%s" % (self._job_tick.job_origin_id, self._job_tick.timestamp)

    def resolve_runs(self, graphene_info):
        instance = graphene_info.context.instance
        return [
            graphene_info.schema.type_named("PipelineRun")(instance.get_run_by_id(run_id))
            for run_id in self._job_tick.run_ids
            if instance.has_run(run_id)
        ]


class DauphinFutureJobTick(dauphin.ObjectType):
    class Meta(object):
        name = "FutureJobTick"

    timestamp = dauphin.NonNull(dauphin.Float)

    def __init__(self, timestamp):
        super(DauphinFutureJobTick, self).__init__(
            timestamp=check.float_param(timestamp, "timestamp"),
        )


class DauphinFutureJobTicks(dauphin.ObjectType):
    class Meta(object):
        name = "FutureJobTicks"

    results = dauphin.non_null_list("FutureJobTick")
    cursor = dauphin.NonNull(dauphin.Float)


class DauphinJobState(dauphin.ObjectType):
    class Meta:
        name = "JobState"

    id = dauphin.NonNull(dauphin.ID)
    name = dauphin.NonNull(dauphin.String)
    jobType = dauphin.NonNull("JobType")
    status = dauphin.NonNull("JobStatus")
    repositoryOrigin = dauphin.NonNull("RepositoryOrigin")
    jobSpecificData = dauphin.Field("JobSpecificData")
    runs = dauphin.Field(dauphin.non_null_list("PipelineRun"), limit=dauphin.Int())
    runsCount = dauphin.NonNull(dauphin.Int)
    ticks = dauphin.Field(dauphin.non_null_list("JobTick"), limit=dauphin.Int())
    runningCount = dauphin.NonNull(dauphin.Int)  # remove with cron scheduler

    def __init__(self, job_state):
        self._job_state = check.inst_param(job_state, "job_state", JobState)
        super(DauphinJobState, self).__init__(
            id=job_state.job_origin_id,
            name=job_state.name,
            jobType=job_state.job_type,
            status=job_state.status,
        )

    def resolve_repositoryOrigin(self, graphene_info):
        origin = self._job_state.origin.external_repository_origin
        return graphene_info.schema.type_named("RepositoryOrigin")(origin)

    def resolve_jobSpecificData(self, graphene_info):
        if not self._job_state.job_specific_data:
            return None

        if self._job_state.job_type == JobType.SENSOR:
            return graphene_info.schema.type_named("SensorJobData")(
                self._job_state.job_specific_data
            )

        if self._job_state.job_type == JobType.SCHEDULE:
            return graphene_info.schema.type_named("ScheduleJobData")(
                self._job_state.job_specific_data
            )

        return None

    def resolve_runs(self, graphene_info, **kwargs):
        if self._job_state.job_type == JobType.SENSOR:
            filters = PipelineRunsFilter.for_sensor(self._job_state)
        else:
            filters = PipelineRunsFilter.for_schedule(self._job_state)
        return [
            graphene_info.schema.type_named("PipelineRun")(r)
            for r in graphene_info.context.instance.get_runs(
                filters=filters, limit=kwargs.get("limit"),
            )
        ]

    def resolve_runsCount(self, graphene_info):
        if self._job_state.job_type == JobType.SENSOR:
            filters = PipelineRunsFilter.for_sensor(self._job_state)
        else:
            filters = PipelineRunsFilter.for_schedule(self._job_state)
        return graphene_info.context.instance.get_runs_count(filters=filters)

    def resolve_ticks(self, graphene_info, limit=None):
        ticks = graphene_info.context.instance.get_job_ticks(self._job_state.job_origin_id)

        if limit:
            ticks = ticks[:limit]

        return [graphene_info.schema.type_named("JobTick")(graphene_info, tick) for tick in ticks]

    def resolve_runningCount(self, graphene_info):
        if self._job_state.job_type == JobType.SENSOR:
            return 1 if self._job_state.status == JobStatus.RUNNING else 0
        else:
            return graphene_info.context.instance.running_schedule_count(
                self._job_state.job_origin_id
            )


class DauphinJobSpecificData(dauphin.Union):
    class Meta:
        name = "JobSpecificData"
        types = ("SensorJobData", "ScheduleJobData")


class DauphinSensorJobData(dauphin.ObjectType):
    class Meta:
        name = "SensorJobData"

    lastTickTimestamp = dauphin.Float()
    lastRunKey = dauphin.String()

    def __init__(self, job_specific_data):
        check.inst_param(job_specific_data, "job_specific_data", SensorJobData)
        super(DauphinSensorJobData, self).__init__(
            lastTickTimestamp=job_specific_data.last_tick_timestamp,
            lastRunKey=job_specific_data.last_run_key,
        )


class DauphinScheduleJobData(dauphin.ObjectType):
    class Meta:
        name = "ScheduleJobData"

    cronSchedule = dauphin.NonNull(dauphin.String)
    startTimestamp = dauphin.Float()

    def __init__(self, job_specific_data):
        check.inst_param(job_specific_data, "job_specific_data", ScheduleJobData)
        super(DauphinScheduleJobData, self).__init__(
            cronSchedule=job_specific_data.cron_schedule,
            startTimestamp=job_specific_data.start_timestamp,
        )


class DauphinJobStatesOrError(dauphin.Union):
    class Meta:
        name = "JobStatesOrError"
        types = ("JobStates", "PythonError")


class DauphinJobStates(dauphin.ObjectType):
    class Meta:
        name = "JobStates"

    results = dauphin.non_null_list("JobState")


DauphinJobType = dauphin.Enum.from_enum(JobType)
DauphinJobStatus = dauphin.Enum.from_enum(JobStatus)
DauphinJobTickStatus = dauphin.Enum.from_enum(JobTickStatus)
