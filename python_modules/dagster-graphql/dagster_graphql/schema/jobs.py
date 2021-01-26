import graphene
import pendulum
import yaml
from dagster import check
from dagster.core.definitions.sensor import RunRequest
from dagster.core.host_representation import (
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.scheduler.job import (
    JobState,
    JobStatus,
    JobTick,
    JobType,
    ScheduleJobData,
    SensorJobData,
)
from dagster.core.storage.pipeline_run import PipelineRunsFilter
from dagster.core.storage.tags import TagType, get_tag_type

from ..implementation.fetch_schedules import get_schedule_next_tick
from ..implementation.fetch_sensors import get_sensor_next_tick
from .errors import GraphenePythonError
from .repository_origin import GrapheneRepositoryOrigin
from .tags import GraphenePipelineTag
from .util import non_null_list


class GrapheneJobType(graphene.Enum):
    SCHEDULE = "SCHEDULE"
    SENSOR = "SENSOR"

    class Meta:
        name = "JobType"


class GrapheneJobStatus(graphene.Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"

    class Meta:
        name = "JobStatus"


class GrapheneJobTickStatus(graphene.Enum):
    STARTED = "STARTED"
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

    class Meta:
        name = "JobTickStatus"


class GrapheneSensorJobData(graphene.ObjectType):
    lastTickTimestamp = graphene.Float()
    lastRunKey = graphene.String()

    class Meta:
        name = "SensorJobData"

    def __init__(self, job_specific_data):
        check.inst_param(job_specific_data, "job_specific_data", SensorJobData)
        super().__init__(
            lastTickTimestamp=job_specific_data.last_tick_timestamp,
            lastRunKey=job_specific_data.last_run_key,
        )


class GrapheneScheduleJobData(graphene.ObjectType):
    cronSchedule = graphene.NonNull(graphene.String)
    startTimestamp = graphene.Float()

    class Meta:
        name = "ScheduleJobData"

    def __init__(self, job_specific_data):
        check.inst_param(job_specific_data, "job_specific_data", ScheduleJobData)
        super().__init__(
            cronSchedule=job_specific_data.cron_schedule,
            startTimestamp=job_specific_data.start_timestamp,
        )


class GrapheneJobSpecificData(graphene.Union):
    class Meta:
        types = (GrapheneSensorJobData, GrapheneScheduleJobData)
        name = "JobSpecificData"


class GrapheneJobTick(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    status = graphene.NonNull(GrapheneJobTickStatus)
    timestamp = graphene.NonNull(graphene.Float)
    runIds = non_null_list(graphene.String)
    error = graphene.Field(GraphenePythonError)
    skipReason = graphene.String()
    runs = non_null_list("dagster_graphql.schema.pipelines.pipeline.GraphenePipelineRun")

    class Meta:
        name = "JobTick"

    def __init__(self, _, job_tick):
        self._job_tick = check.inst_param(job_tick, "job_tick", JobTick)

        super().__init__(
            status=job_tick.status,
            timestamp=job_tick.timestamp,
            runIds=job_tick.run_ids,
            error=job_tick.error,
            skipReason=job_tick.skip_reason,
        )

    def resolve_id(self, _):
        return "%s:%s" % (self._job_tick.job_origin_id, self._job_tick.timestamp)

    def resolve_runs(self, graphene_info):
        from .pipelines.pipeline import GraphenePipelineRun

        instance = graphene_info.context.instance
        return [
            GraphenePipelineRun(instance.get_run_by_id(run_id))
            for run_id in self._job_tick.run_ids
            if instance.has_run(run_id)
        ]


class GrapheneFutureJobTick(graphene.ObjectType):
    timestamp = graphene.NonNull(graphene.Float)
    evaluationResult = graphene.Field(lambda: GrapheneTickEvaluation)

    class Meta:
        name = "FutureJobTick"

    def __init__(self, job_state, timestamp):
        self._job_state = check.inst_param(job_state, "job_state", JobState)
        self._timestamp = timestamp
        super().__init__(timestamp=check.float_param(timestamp, "timestamp"),)

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
        return GrapheneTickEvaluation(schedule_data)


class GrapheneTickEvaluation(graphene.ObjectType):
    runRequests = graphene.List(lambda: GrapheneRunRequest)
    skipReason = graphene.String()
    error = graphene.Field(GraphenePythonError)

    class Meta:
        name = "TickEvaluation"

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
        super().__init__(skipReason=skip_reason, error=error)

    def resolve_runRequests(self, _graphene_info):
        if not self._run_requests:
            return self._run_requests

        return [GrapheneRunRequest(run_request) for run_request in self._run_requests]


class GrapheneRunRequest(graphene.ObjectType):
    runKey = graphene.String()
    tags = non_null_list(GraphenePipelineTag)
    runConfigYaml = graphene.NonNull(graphene.String)

    class Meta:
        name = "RunRequest"

    def __init__(self, run_request):
        super().__init__(runKey=run_request.run_key)
        self._run_request = check.inst_param(run_request, "run_request", RunRequest)

    def resolve_tags(self, _graphene_info):
        return [
            GraphenePipelineTag(key=key, value=value)
            for key, value in self._run_request.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]

    def resolve_runConfigYaml(self, _graphene_info):
        return yaml.dump(self._run_request.run_config, default_flow_style=False, allow_unicode=True)


class GrapheneFutureJobTicks(graphene.ObjectType):
    results = non_null_list(GrapheneFutureJobTick)
    cursor = graphene.NonNull(graphene.Float)

    class Meta:
        name = "FutureJobTicks"


class GrapheneJobState(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    jobType = graphene.NonNull(GrapheneJobType)
    status = graphene.NonNull(GrapheneJobStatus)
    repositoryOrigin = graphene.NonNull(GrapheneRepositoryOrigin)
    jobSpecificData = graphene.Field(GrapheneJobSpecificData)
    runs = graphene.Field(
        non_null_list("dagster_graphql.schema.pipelines.pipeline.GraphenePipelineRun"),
        limit=graphene.Int(),
    )
    runsCount = graphene.NonNull(graphene.Int)
    ticks = graphene.Field(
        non_null_list(GrapheneJobTick),
        dayRange=graphene.Int(),
        dayOffset=graphene.Int(),
        limit=graphene.Int(),
    )
    nextTick = graphene.Field(GrapheneFutureJobTick)
    runningCount = graphene.NonNull(graphene.Int)  # remove with cron scheduler

    class Meta:
        name = "JobState"

    def __init__(self, job_state):
        self._job_state = check.inst_param(job_state, "job_state", JobState)
        super().__init__(
            id=job_state.job_origin_id,
            name=job_state.name,
            jobType=job_state.job_type,
            status=job_state.status,
        )

    def resolve_repositoryOrigin(self, _graphene_info):
        origin = self._job_state.origin.external_repository_origin
        return GrapheneRepositoryOrigin(origin)

    def resolve_jobSpecificData(self, _graphene_info):
        if not self._job_state.job_specific_data:
            return None

        if self._job_state.job_type == JobType.SENSOR:
            return GrapheneSensorJobData(self._job_state.job_specific_data)

        if self._job_state.job_type == JobType.SCHEDULE:
            return GrapheneScheduleJobData(self._job_state.job_specific_data)

        return None

    def resolve_runs(self, graphene_info, **kwargs):
        from .pipelines.pipeline import GraphenePipelineRun

        if self._job_state.job_type == JobType.SENSOR:
            filters = PipelineRunsFilter.for_sensor(self._job_state)
        else:
            filters = PipelineRunsFilter.for_schedule(self._job_state)
        return [
            GraphenePipelineRun(r)
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
            GrapheneJobTick(graphene_info, tick)
            for tick in graphene_info.context.instance.get_job_ticks(
                self._job_state.job_origin_id, before=before, after=after, limit=limit
            )
        ]

    def resolve_nextTick(self, graphene_info):
        # sensor
        if self._job_state.job_type == JobType.SENSOR:
            return get_sensor_next_tick(graphene_info, self._job_state)
        else:
            return get_schedule_next_tick(graphene_info, self._job_state)

    def resolve_runningCount(self, graphene_info):
        if self._job_state.job_type == JobType.SENSOR:
            return 1 if self._job_state.status == JobStatus.RUNNING else 0
        else:
            return graphene_info.context.instance.running_schedule_count(
                self._job_state.job_origin_id
            )


class GrapheneJobStates(graphene.ObjectType):
    results = non_null_list(GrapheneJobState)

    class Meta:
        name = "JobStates"


class GrapheneJobStateOrError(graphene.Union):
    class Meta:
        name = "JobStateOrError"
        types = (GrapheneJobState, GraphenePythonError)


class GrapheneJobStatesOrError(graphene.Union):
    class Meta:
        types = (GrapheneJobStates, GraphenePythonError)
        name = "JobStatesOrError"


types = [
    GrapheneFutureJobTick,
    GrapheneFutureJobTicks,
    GrapheneJobSpecificData,
    GrapheneJobState,
    GrapheneJobStateOrError,
    GrapheneJobStates,
    GrapheneJobStatesOrError,
    GrapheneJobTick,
    GrapheneScheduleJobData,
    GrapheneSensorJobData,
]
