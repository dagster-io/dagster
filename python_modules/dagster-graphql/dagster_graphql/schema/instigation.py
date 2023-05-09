import sys
import warnings
from typing import Optional, Union

import dagster._check as check
import graphene
import pendulum
from dagster._core.definitions.run_request import (
    AddDynamicPartitionsRequest,
    DeleteDynamicPartitionsRequest,
    RunRequest,
)
from dagster._core.definitions.schedule_definition import ScheduleExecutionData
from dagster._core.definitions.selector import ScheduleSelector, SensorSelector
from dagster._core.definitions.sensor_definition import SensorExecutionData
from dagster._core.scheduler.instigation import (
    DynamicPartitionsRequestResult,
    InstigatorState,
    InstigatorTick,
    InstigatorType,
    ScheduleInstigatorData,
    SensorInstigatorData,
    TickStatus,
)
from dagster._core.storage.dagster_run import DagsterRun, RunsFilter
from dagster._core.storage.tags import REPOSITORY_LABEL_TAG, TagType, get_tag_type
from dagster._core.workspace.permissions import Permissions
from dagster._seven.compat.pendulum import to_timezone
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster._utils.yaml_utils import dump_run_config_yaml

from dagster_graphql.schema.asset_key import GrapheneAssetKey

from ..implementation.fetch_instigators import get_tick_log_events
from ..implementation.fetch_schedules import get_schedule_next_tick
from ..implementation.fetch_sensors import get_sensor_next_tick
from ..implementation.loader import RepositoryScopedBatchLoader
from ..implementation.utils import UserFacingGraphQLError
from .errors import (
    GrapheneError,
    GraphenePythonError,
    GrapheneRepositoryLocationNotFound,
    GrapheneRepositoryNotFoundError,
    GrapheneScheduleNotFoundError,
    GrapheneSensorNotFoundError,
)
from .logs.log_level import GrapheneLogLevel
from .repository_origin import GrapheneRepositoryOrigin
from .tags import GraphenePipelineTag
from .util import ResolveInfo, non_null_list


class GrapheneInstigationType(graphene.Enum):
    SCHEDULE = "SCHEDULE"
    SENSOR = "SENSOR"

    class Meta:
        name = "InstigationType"


class GrapheneInstigationStatus(graphene.Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"

    class Meta:
        name = "InstigationStatus"


class GrapheneInstigationTickStatus(graphene.Enum):
    STARTED = "STARTED"
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

    class Meta:
        name = "InstigationTickStatus"


class GrapheneSensorData(graphene.ObjectType):
    lastTickTimestamp = graphene.Float()
    lastRunKey = graphene.String()
    lastCursor = graphene.String()

    class Meta:
        name = "SensorData"

    def __init__(self, instigator_data):
        check.inst_param(instigator_data, "instigator_data", SensorInstigatorData)
        super().__init__(
            lastTickTimestamp=instigator_data.last_tick_timestamp,
            lastRunKey=instigator_data.last_run_key,
            lastCursor=instigator_data.cursor,
        )


class GrapheneScheduleData(graphene.ObjectType):
    cronSchedule = graphene.NonNull(graphene.String)
    startTimestamp = graphene.Float()

    class Meta:
        name = "ScheduleData"

    def __init__(self, instigator_data):
        check.inst_param(instigator_data, "instigator_data", ScheduleInstigatorData)
        super().__init__(
            cronSchedule=str(instigator_data.cron_schedule),
            startTimestamp=instigator_data.start_timestamp,
        )


class GrapheneInstigationTypeSpecificData(graphene.Union):
    class Meta:
        types = (GrapheneSensorData, GrapheneScheduleData)
        name = "InstigationTypeSpecificData"


class GrapheneInstigationEvent(graphene.ObjectType):
    class Meta:
        name = "InstigationEvent"

    message = graphene.NonNull(graphene.String)
    timestamp = graphene.NonNull(graphene.String)
    level = graphene.NonNull(GrapheneLogLevel)


class GrapheneInstigationEventConnection(graphene.ObjectType):
    class Meta:
        name = "InstigationEventConnection"

    events = non_null_list(GrapheneInstigationEvent)
    cursor = graphene.NonNull(graphene.String)
    hasMore = graphene.NonNull(graphene.Boolean)


class GrapheneDynamicPartitionsRequestType(graphene.Enum):
    ADD_PARTITIONS = "ADD_PARTITIONS"
    DELETE_PARTITIONS = "DELETE_PARTITIONS"

    class Meta:
        name = "DynamicPartitionsRequestType"


class DynamicPartitionsRequestMixin:
    # Mixin this class to implement DynamicPartitionsRequest
    #
    # Graphene has some strange properties that make it so that you cannot
    # implement ABCs nor use properties in an overridable way. So the way
    # the mixin works is that the target classes have to have a method
    # get_dynamic_partitions_request()
    partitionKeys = graphene.List(graphene.NonNull(graphene.String))
    partitionsDefName = graphene.NonNull(graphene.String)
    type = graphene.NonNull(GrapheneDynamicPartitionsRequestType)

    class Meta:
        name = "DynamicPartitionRequestMixin"

    def get_dynamic_partitions_request(
        self,
    ) -> Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest,]:
        raise NotImplementedError()

    def resolve_partitionKeys(self, _graphene_info: ResolveInfo):
        return self.get_dynamic_partitions_request().partition_keys

    def resolve_partitionsDefName(self, _graphene_info: ResolveInfo):
        return self.get_dynamic_partitions_request().partitions_def_name

    def resolve_type(self, _graphene_info: ResolveInfo):
        return (
            GrapheneDynamicPartitionsRequestType.ADD_PARTITIONS
            if isinstance(self.get_dynamic_partitions_request(), AddDynamicPartitionsRequest)
            else GrapheneDynamicPartitionsRequestType.DELETE_PARTITIONS
        )


class GrapheneDynamicPartitionsRequest(DynamicPartitionsRequestMixin, graphene.ObjectType):
    class Meta:
        name = "DynamicPartitionRequest"

    def __init__(
        self,
        dynamic_partition_request: Union[
            AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest
        ],
    ):
        super().__init__()
        self._dynamic_partitions_request = dynamic_partition_request

    def get_dynamic_partitions_request(
        self,
    ) -> Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest,]:
        return self._dynamic_partitions_request


class GrapheneDynamicPartitionsRequestResult(DynamicPartitionsRequestMixin, graphene.ObjectType):
    class Meta:
        name = "DynamicPartitionsRequestResult"

    skippedPartitionKeys = non_null_list(graphene.String)

    def __init__(self, dynamic_partitions_request_result: DynamicPartitionsRequestResult):
        super().__init__()
        self._dynamic_partitions_request_result = dynamic_partitions_request_result

    def get_dynamic_partitions_request(
        self,
    ) -> Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest]:
        if self._dynamic_partitions_request_result.added_partitions is not None:
            return AddDynamicPartitionsRequest(
                partition_keys=self._dynamic_partitions_request_result.added_partitions,
                partitions_def_name=self._dynamic_partitions_request_result.partitions_def_name,
            )
        elif self._dynamic_partitions_request_result.deleted_partitions is not None:
            return DeleteDynamicPartitionsRequest(
                partition_keys=self._dynamic_partitions_request_result.deleted_partitions,
                partitions_def_name=self._dynamic_partitions_request_result.partitions_def_name,
            )
        else:
            check.failed(
                "Unexpected dynamic_partitions_request_result"
                f" {self._dynamic_partitions_request_result}"
            )

    def resolve_skippedPartitionKeys(self, _graphene_info: ResolveInfo):
        return self._dynamic_partitions_request_result.skipped_partitions


class GrapheneInstigationTick(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    status = graphene.NonNull(GrapheneInstigationTickStatus)
    timestamp = graphene.NonNull(graphene.Float)
    runIds = non_null_list(graphene.String)
    runKeys = non_null_list(graphene.String)
    error = graphene.Field(GraphenePythonError)
    skipReason = graphene.String()
    cursor = graphene.String()
    runs = non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneRun")
    originRunIds = non_null_list(graphene.String)
    logKey = graphene.List(graphene.NonNull(graphene.String))
    logEvents = graphene.Field(graphene.NonNull(GrapheneInstigationEventConnection))
    dynamicPartitionsRequestResults = non_null_list(GrapheneDynamicPartitionsRequestResult)

    class Meta:
        name = "InstigationTick"

    def __init__(self, _, tick):
        self._tick = check.inst_param(tick, "tick", InstigatorTick)

        super().__init__(
            status=tick.status.value,
            timestamp=tick.timestamp,
            runIds=tick.run_ids,
            runKeys=tick.run_keys,
            error=GraphenePythonError(tick.error) if tick.error else None,
            skipReason=tick.skip_reason,
            originRunIds=tick.origin_run_ids,
            cursor=tick.cursor,
            logKey=tick.log_key,
        )

    def resolve_id(self, _):
        return "%s:%s" % (self._tick.instigator_origin_id, self._tick.timestamp)

    def resolve_runs(self, graphene_info: ResolveInfo):
        from .pipelines.pipeline import GrapheneRun

        instance = graphene_info.context.instance
        run_ids = self._tick.origin_run_ids or self._tick.run_ids
        if not run_ids:
            return []

        records_by_id = {
            record.dagster_run.run_id: record
            for record in instance.get_run_records(RunsFilter(run_ids=run_ids))
        }

        return [GrapheneRun(records_by_id[run_id]) for run_id in run_ids if run_id in records_by_id]

    def resolve_logEvents(self, graphene_info: ResolveInfo):
        return get_tick_log_events(graphene_info, self._tick)

    def resolve_dynamicPartitionsRequestResults(self, _):
        return [
            GrapheneDynamicPartitionsRequestResult(request_result)
            for request_result in self._tick.dynamic_partitions_request_results
        ]


class GrapheneDryRunInstigationTick(graphene.ObjectType):
    timestamp = graphene.Float()
    evaluationResult = graphene.Field(lambda: GrapheneTickEvaluation)

    class Meta:
        name = "DryRunInstigationTick"

    def __init__(
        self,
        selector: Union[ScheduleSelector, SensorSelector],
        timestamp: Optional[float],
        cursor: Optional[str] = None,
    ):
        self._selector = check.inst_param(selector, "selector", (ScheduleSelector, SensorSelector))
        self._cursor = cursor
        super().__init__(
            timestamp=check.opt_float_param(timestamp, "timestamp"),
        )

    def resolve_evaluationResult(self, graphene_info: ResolveInfo):
        if not graphene_info.context.has_code_location(self._selector.location_name):
            raise UserFacingGraphQLError(
                GrapheneRepositoryLocationNotFound(location_name=self._selector.location_name)
            )

        code_location = graphene_info.context.get_code_location(self._selector.location_name)
        if not code_location.has_repository(self._selector.repository_name):
            raise UserFacingGraphQLError(
                GrapheneRepositoryNotFoundError(
                    repository_location_name=self._selector.location_name,
                    repository_name=self._selector.repository_name,
                )
            )

        repository = code_location.get_repository(self._selector.repository_name)

        if isinstance(self._selector, SensorSelector):
            if not repository.has_external_sensor(self._selector.sensor_name):
                raise UserFacingGraphQLError(
                    GrapheneSensorNotFoundError(self._selector.sensor_name)
                )
            sensor_data: Union[SensorExecutionData, SerializableErrorInfo]
            try:
                sensor_data = code_location.get_external_sensor_execution_data(
                    name=self._selector.sensor_name,
                    instance=graphene_info.context.instance,
                    repository_handle=repository.handle,
                    cursor=self._cursor,
                    last_completion_time=None,
                    last_run_key=None,
                )
            except Exception:
                sensor_data = serializable_error_info_from_exc_info(sys.exc_info())
            return GrapheneTickEvaluation(sensor_data)
        else:
            if not repository.has_external_schedule(self._selector.schedule_name):
                raise UserFacingGraphQLError(
                    GrapheneScheduleNotFoundError(self._selector.schedule_name)
                )
            if not self.timestamp:
                raise Exception(
                    "No tick timestamp provided when attempting to dry-run schedule"
                    f" {self._selector.schedule_name}."
                )
            external_schedule = repository.get_external_schedule(self._selector.schedule_name)
            timezone_str = external_schedule.execution_timezone
            if not timezone_str:
                timezone_str = "UTC"

            next_tick_datetime = next(external_schedule.execution_time_iterator(self.timestamp))
            schedule_time = to_timezone(pendulum.instance(next_tick_datetime), timezone_str)
            schedule_data: Union[ScheduleExecutionData, SerializableErrorInfo]
            try:
                schedule_data = code_location.get_external_schedule_execution_data(
                    instance=graphene_info.context.instance,
                    repository_handle=repository.handle,
                    schedule_name=external_schedule.name,
                    scheduled_execution_time=schedule_time,
                )
            except Exception:
                schedule_data = serializable_error_info_from_exc_info(sys.exc_info())

            return GrapheneTickEvaluation(schedule_data)


class GrapheneTickEvaluation(graphene.ObjectType):
    dynamicPartitionsRequests = graphene.List(graphene.NonNull(GrapheneDynamicPartitionsRequest))
    runRequests = graphene.List(lambda: graphene.NonNull(GrapheneRunRequest))
    skipReason = graphene.String()
    error = graphene.Field(GraphenePythonError)
    cursor = graphene.String()

    _execution_data: Union[ScheduleExecutionData, SensorExecutionData, SerializableErrorInfo]

    class Meta:
        name = "TickEvaluation"

    def __init__(
        self,
        execution_data: Union[ScheduleExecutionData, SensorExecutionData, SerializableErrorInfo],
    ):
        check.inst_param(
            execution_data,
            "execution_data",
            (ScheduleExecutionData, SensorExecutionData, SerializableErrorInfo),
        )
        error = (
            GraphenePythonError(execution_data)
            if isinstance(execution_data, SerializableErrorInfo)
            else None
        )
        skip_reason = (
            execution_data.skip_message
            if not isinstance(execution_data, SerializableErrorInfo)
            else None
        )
        self._execution_data = execution_data
        self._run_requests = (
            execution_data.run_requests
            if not isinstance(execution_data, SerializableErrorInfo)
            else None
        )

        self._dynamic_partitions_requests = (
            execution_data.dynamic_partitions_requests
            if isinstance(execution_data, SensorExecutionData)
            else None
        )

        cursor = execution_data.cursor if isinstance(execution_data, SensorExecutionData) else None
        super().__init__(
            skipReason=skip_reason,
            error=error,
            cursor=cursor,
        )

    def resolve_runRequests(self, _graphene_info: ResolveInfo):
        if not self._run_requests:
            return self._run_requests

        return [GrapheneRunRequest(run_request) for run_request in self._run_requests]

    def resolve_dynamicPartitionsRequests(self, _graphene_info: ResolveInfo):
        if not self._dynamic_partitions_requests:
            return self._dynamic_partitions_requests

        return [
            GrapheneDynamicPartitionsRequest(request)
            for request in self._dynamic_partitions_requests
        ]


class GrapheneRunRequest(graphene.ObjectType):
    runKey = graphene.String()
    tags = non_null_list(GraphenePipelineTag)
    runConfigYaml = graphene.NonNull(graphene.String)
    assetSelection = graphene.List(graphene.NonNull(GrapheneAssetKey))

    _run_request: RunRequest

    class Meta:
        name = "RunRequest"

    def __init__(self, run_request):
        super().__init__(runKey=run_request.run_key)
        self._run_request = check.inst_param(run_request, "run_request", RunRequest)

    def resolve_tags(self, _graphene_info: ResolveInfo):
        return [
            GraphenePipelineTag(key=key, value=value)
            for key, value in self._run_request.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]

    def resolve_runConfigYaml(self, _graphene_info: ResolveInfo):
        return dump_run_config_yaml(self._run_request.run_config)

    def resolve_assetSelection(self, _graphene_info: ResolveInfo):
        if self._run_request.asset_selection:
            return [
                GrapheneAssetKey(path=asset_key.path)
                for asset_key in self._run_request.asset_selection
            ]
        return None


class GrapheneDryRunInstigationTicks(graphene.ObjectType):
    results = non_null_list(GrapheneDryRunInstigationTick)
    cursor = graphene.NonNull(graphene.Float)

    class Meta:
        name = "DryRunInstigationTicks"


class GrapheneInstigationState(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    selectorId = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)
    instigationType = graphene.NonNull(GrapheneInstigationType)
    status = graphene.NonNull(GrapheneInstigationStatus)
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)
    repositoryOrigin = graphene.NonNull(GrapheneRepositoryOrigin)
    typeSpecificData = graphene.Field(GrapheneInstigationTypeSpecificData)
    runs = graphene.Field(
        non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneRun"),
        limit=graphene.Int(),
    )
    runsCount = graphene.NonNull(graphene.Int)
    tick = graphene.Field(GrapheneInstigationTick, timestamp=graphene.Float())
    ticks = graphene.Field(
        non_null_list(GrapheneInstigationTick),
        dayRange=graphene.Int(),
        dayOffset=graphene.Int(),
        limit=graphene.Int(),
        cursor=graphene.String(),
        statuses=graphene.List(graphene.NonNull(GrapheneInstigationTickStatus)),
    )
    nextTick = graphene.Field(GrapheneDryRunInstigationTick)
    runningCount = graphene.NonNull(graphene.Int)  # remove with cron scheduler

    hasStartPermission = graphene.NonNull(graphene.Boolean)
    hasStopPermission = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "InstigationState"

    def __init__(
        self,
        instigator_state,
        batch_loader=None,
    ):
        self._instigator_state = check.inst_param(
            instigator_state, "instigator_state", InstigatorState
        )

        # optional batch loader, provided by a parent GrapheneRepository object that instantiates
        # multiple schedules/sensors
        self._batch_loader = check.opt_inst_param(
            batch_loader, "batch_loader", RepositoryScopedBatchLoader
        )
        super().__init__(
            id=instigator_state.instigator_origin_id,
            selectorId=instigator_state.selector_id,
            name=instigator_state.name,
            instigationType=instigator_state.instigator_type.value,
            status=(
                GrapheneInstigationStatus.RUNNING
                if instigator_state.is_running
                else GrapheneInstigationStatus.STOPPED
            ),
        )

    def resolve_repositoryOrigin(self, _graphene_info: ResolveInfo):
        origin = self._instigator_state.origin.external_repository_origin
        return GrapheneRepositoryOrigin(origin)

    def resolve_repositoryName(self, _graphene_info: ResolveInfo):
        return self._instigator_state.repository_selector.repository_name

    def resolve_repositoryLocationName(self, _graphene_info: ResolveInfo):
        return self._instigator_state.repository_selector.location_name

    def resolve_hasStartPermission(self, graphene_info: ResolveInfo):
        if self._instigator_state.instigator_type == InstigatorType.SCHEDULE:
            return graphene_info.context.has_permission_for_location(
                Permissions.START_SCHEDULE, self._instigator_state.repository_selector.location_name
            )
        else:
            check.invariant(self._instigator_state.instigator_type == InstigatorType.SENSOR)
            return graphene_info.context.has_permission_for_location(
                Permissions.EDIT_SENSOR, self._instigator_state.repository_selector.location_name
            )

    def resolve_hasStopPermission(self, graphene_info: ResolveInfo):
        if self._instigator_state.instigator_type == InstigatorType.SCHEDULE:
            return graphene_info.context.has_permission_for_location(
                Permissions.STOP_RUNNING_SCHEDULE,
                self._instigator_state.repository_selector.location_name,
            )
        else:
            check.invariant(self._instigator_state.instigator_type == InstigatorType.SENSOR)
            return graphene_info.context.has_permission_for_location(
                Permissions.EDIT_SENSOR, self._instigator_state.repository_selector.location_name
            )

    def resolve_typeSpecificData(self, _graphene_info: ResolveInfo):
        if not self._instigator_state.instigator_data:
            return None

        if self._instigator_state.instigator_type == InstigatorType.SENSOR:
            return GrapheneSensorData(self._instigator_state.instigator_data)

        if self._instigator_state.instigator_type == InstigatorType.SCHEDULE:
            return GrapheneScheduleData(self._instigator_state.instigator_data)

        return None

    def resolve_runs(self, graphene_info: ResolveInfo, limit: Optional[int] = None):
        from .pipelines.pipeline import GrapheneRun

        if limit and self._batch_loader:
            records = (
                self._batch_loader.get_run_records_for_sensor(self._instigator_state.name, limit)
                if self._instigator_state.instigator_type == InstigatorType.SENSOR
                else self._batch_loader.get_run_records_for_schedule(
                    self._instigator_state.name, limit
                )
            )
            return [GrapheneRun(record) for record in records]

        repository_label = self._instigator_state.origin.external_repository_origin.get_label()
        if self._instigator_state.instigator_type == InstigatorType.SENSOR:
            filters = RunsFilter(
                tags={
                    **DagsterRun.tags_for_sensor(self._instigator_state),
                    REPOSITORY_LABEL_TAG: repository_label,
                }
            )
        else:
            filters = RunsFilter(
                tags={
                    **DagsterRun.tags_for_schedule(self._instigator_state),
                    REPOSITORY_LABEL_TAG: repository_label,
                }
            )
        return [
            GrapheneRun(record)
            for record in graphene_info.context.instance.get_run_records(
                filters=filters,
                limit=limit,
            )
        ]

    def resolve_runsCount(self, graphene_info: ResolveInfo):
        if self._instigator_state.instigator_type == InstigatorType.SENSOR:
            filters = RunsFilter.for_sensor(self._instigator_state)
        else:
            filters = RunsFilter.for_schedule(self._instigator_state)
        return graphene_info.context.instance.get_runs_count(filters=filters)

    def resolve_tick(self, graphene_info: ResolveInfo, timestamp):
        matches = graphene_info.context.instance.get_ticks(
            self._instigator_state.instigator_origin_id,
            self._instigator_state.selector_id,
            before=timestamp + 1,
            after=timestamp - 1,
            limit=1,
        )
        return GrapheneInstigationTick(graphene_info, matches[0]) if matches else None

    def resolve_ticks(
        self, graphene_info, dayRange=None, dayOffset=None, limit=None, cursor=None, statuses=None
    ):
        before = None
        if dayOffset:
            before = pendulum.now("UTC").subtract(days=dayOffset).timestamp()
        elif cursor:
            parts = cursor.split(":")
            if parts:
                try:
                    before = float(parts[-1])
                except (ValueError, IndexError):
                    warnings.warn(f"Invalid cursor for {self.name} ticks: {cursor}")

        after = (
            pendulum.now("UTC").subtract(days=dayRange + (dayOffset or 0)).timestamp()
            if dayRange
            else None
        )
        if statuses:
            statuses = [TickStatus(status) for status in statuses]

        if self._batch_loader and limit and not cursor and not before and not after:
            ticks = (
                self._batch_loader.get_sensor_ticks(
                    self._instigator_state.instigator_origin_id,
                    self._instigator_state.selector_id,
                    limit,
                )
                if self._instigator_state.instigator_type == InstigatorType.SENSOR
                else self._batch_loader.get_schedule_ticks(
                    self._instigator_state.instigator_origin_id,
                    self._instigator_state.selector_id,
                    limit,
                )
            )
            return [GrapheneInstigationTick(graphene_info, tick) for tick in ticks]

        return [
            GrapheneInstigationTick(graphene_info, tick)
            for tick in graphene_info.context.instance.get_ticks(
                self._instigator_state.instigator_origin_id,
                self._instigator_state.selector_id,
                before=before,
                after=after,
                limit=limit,
                statuses=statuses,
            )
        ]

    def resolve_nextTick(self, graphene_info: ResolveInfo):
        # sensor
        if self._instigator_state.instigator_type == InstigatorType.SENSOR:
            return get_sensor_next_tick(graphene_info, self._instigator_state)
        else:
            return get_schedule_next_tick(graphene_info, self._instigator_state)

    def resolve_runningCount(self, _graphene_info: ResolveInfo):
        return 1 if self._instigator_state.is_running else 0


class GrapheneInstigationStates(graphene.ObjectType):
    results = non_null_list(GrapheneInstigationState)

    class Meta:
        name = "InstigationStates"


class GrapheneInstigationStateNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "InstigationStateNotFoundError"

    name = graphene.NonNull(graphene.String)

    def __init__(self, name):
        super().__init__()
        self.name = check.str_param(name, "name")
        self.message = f"Could not find `{name}` in the currently loaded repository."


class GrapheneInstigationStateOrError(graphene.Union):
    class Meta:
        name = "InstigationStateOrError"
        types = (
            GrapheneInstigationState,
            GrapheneInstigationStateNotFoundError,
            GraphenePythonError,
        )


class GrapheneInstigationStatesOrError(graphene.Union):
    class Meta:
        types = (GrapheneInstigationStates, GraphenePythonError)
        name = "InstigationStatesOrError"


types = [
    GrapheneDryRunInstigationTick,
    GrapheneDryRunInstigationTicks,
    GrapheneInstigationTypeSpecificData,
    GrapheneInstigationState,
    GrapheneInstigationStateNotFoundError,
    GrapheneInstigationStateOrError,
    GrapheneInstigationStates,
    GrapheneInstigationStatesOrError,
    GrapheneInstigationTick,
    GrapheneScheduleData,
    GrapheneSensorData,
]
