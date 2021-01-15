import pendulum
import yaml
from dagster import check
from dagster.core.definitions.job import JobType, RunRequest
from dagster.core.host_representation import (
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.scheduler.job import (
    JobState,
    JobStatus,
    JobTick,
    JobTickStatus,
    ScheduleJobData,
    SensorJobData,
)
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster.core.storage.tags import TagType, get_tag_type
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
    evaluationResult = dauphin.Field("TickEvaluation")

    def __init__(self, job_state, timestamp):
        self._job_state = check.inst_param(job_state, "job_state", JobState)
        self._timestamp = timestamp
        super(DauphinFutureJobTick, self).__init__(
            timestamp=check.float_param(timestamp, "timestamp"),
        )

    def resolve_evaluationResult(self, graphene_info):
        if self._job_state.status != JobStatus.RUNNING:
            return None

        if self._job_state.job_type != JobType.SCHEDULE:
            return None

        repository_origin = self._job_state.origin.external_repository_origin
        if not graphene_info.context.has_repository_location(
            repository_origin.repository_location_origin.location_name
        ):
            return None

        repository_location = graphene_info.context.get_repository_location(
            repository_origin.repository_location_origin.location_name
        )
        if not repository_location.has_repository(repository_origin.repository_name):
            return None

        repository = repository_location.get_repository(repository_origin.repository_name)
        external_schedule = repository.get_external_job(self._job_state.name)
        timezone_str = external_schedule.execution_timezone
        if not timezone_str:
            timezone_str = pendulum.now().timezone.name

        next_tick_datetime = next(external_schedule.execution_time_iterator(self._timestamp))
        schedule_time = pendulum.instance(next_tick_datetime).in_tz(timezone_str)
        schedule_data = repository_location.get_external_schedule_execution_data(
            instance=graphene_info.context.instance,
            repository_handle=repository.handle,
            schedule_name=external_schedule.name,
            scheduled_execution_time=schedule_time,
        )
        return graphene_info.schema.type_named("TickEvaluation")(schedule_data)


class DauphinTickEvaluation(dauphin.ObjectType):
    class Meta(object):
        name = "TickEvaluation"

    runRequests = dauphin.List("RunRequest")
    skipReason = dauphin.String()
    error = dauphin.Field("PythonError")

    def __init__(self, schedule_data):
        check.inst_param(
            schedule_data,
            "schedule_data",
            (ExternalScheduleExecutionData, ExternalScheduleExecutionErrorData),
        )
        error = (
            schedule_data.error
            if isinstance(schedule_data, ExternalScheduleExecutionErrorData)
            else None
        )
        skip_reason = (
            schedule_data.skip_message
            if isinstance(schedule_data, ExternalScheduleExecutionData)
            else None
        )
        self._run_requests = (
            schedule_data.run_requests
            if isinstance(schedule_data, ExternalScheduleExecutionData)
            else None
        )
        super(DauphinTickEvaluation, self).__init__(skipReason=skip_reason, error=error)

    def resolve_runRequests(self, graphene_info):
        if not self._run_requests:
            return self._run_requests

        return [
            graphene_info.schema.type_named("RunRequest")(run_request)
            for run_request in self._run_requests
        ]


class DauphinRunRequest(dauphin.ObjectType):
    class Meta(object):
        name = "RunRequest"

    runKey = dauphin.String()
    tags = dauphin.non_null_list("PipelineTag")
    runConfigYaml = dauphin.NonNull(dauphin.String)

    def __init__(self, run_request):
        super(DauphinRunRequest, self).__init__(runKey=run_request.run_key)
        self._run_request = check.inst_param(run_request, "run_request", RunRequest)

    def resolve_tags(self, graphene_info):
        return [
            graphene_info.schema.type_named("PipelineTag")(key=key, value=value)
            for key, value in self._run_request.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]

    def resolve_runConfigYaml(self, _graphene_info):
        return yaml.dump(self._run_request.run_config, default_flow_style=False, allow_unicode=True)


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
    ticks = dauphin.Field(
        dauphin.non_null_list("JobTick"),
        dayRange=dauphin.Int(),
        dayOffset=dauphin.Int(),
        limit=dauphin.Int(),
    )
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

    def resolve_ticks(self, graphene_info, dayRange=None, dayOffset=None, limit=None):
        before = pendulum.now("UTC").subtract(days=dayOffset).timestamp() if dayOffset else None
        after = (
            pendulum.now("UTC").subtract(days=dayRange + (dayOffset or 0)).timestamp()
            if dayRange
            else None
        )
        return [
            graphene_info.schema.type_named("JobTick")(graphene_info, tick)
            for tick in graphene_info.context.instance.get_job_ticks(
                self._job_state.job_origin_id, before=before, after=after, limit=limit
            )
        ]

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
