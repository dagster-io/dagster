import sys
from typing import Optional, Union

import dagster._check as check
import graphene
from dagster._core.definitions.dynamic_partitions_request import (
    AddDynamicPartitionsRequest,
    DeleteDynamicPartitionsRequest,
)
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.schedule_definition import ScheduleExecutionData
from dagster._core.definitions.selector import ScheduleSelector, SensorSelector
from dagster._core.definitions.sensor_definition import SensorExecutionData
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.remote_representation.external import CompoundID
from dagster._core.scheduler.instigation import (
    DynamicPartitionsRequestResult,
    InstigatorState,
    InstigatorTick,
    InstigatorType,
    ScheduleInstigatorData,
    SensorInstigatorData,
)
from dagster._core.storage.dagster_run import DagsterRun, RunsFilter
from dagster._core.storage.tags import REPOSITORY_LABEL_TAG, TagType, get_tag_type
from dagster._core.utils import is_valid_run_id
from dagster._core.workspace.permissions import Permissions
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster_shared.yaml_utils import dump_run_config_yaml

from dagster_graphql.implementation.fetch_instigators import get_tick_log_events
from dagster_graphql.implementation.fetch_schedules import get_schedule_next_tick
from dagster_graphql.implementation.fetch_sensors import get_sensor_next_tick
from dagster_graphql.implementation.fetch_ticks import get_instigation_ticks
from dagster_graphql.implementation.loader import RepositoryScopedBatchLoader
from dagster_graphql.implementation.utils import UserFacingGraphQLError
from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.errors import (
    GrapheneError,
    GraphenePythonError,
    GrapheneRepositoryLocationNotFound,
    GrapheneRepositoryNotFoundError,
    GrapheneScheduleNotFoundError,
    GrapheneSensorNotFoundError,
)
from dagster_graphql.schema.logs.log_level import GrapheneLogLevel
from dagster_graphql.schema.repository_origin import GrapheneRepositoryOrigin
from dagster_graphql.schema.tags import GraphenePipelineTag
from dagster_graphql.schema.util import ResolveInfo, non_null_list

GrapheneInstigationType = graphene.Enum.from_enum(InstigatorType, "InstigationType")


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
    ) -> Union[
        AddDynamicPartitionsRequest,
        DeleteDynamicPartitionsRequest,
    ]:
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
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
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
    ) -> Union[
        AddDynamicPartitionsRequest,
        DeleteDynamicPartitionsRequest,
    ]:
        return self._dynamic_partitions_request


class GrapheneDynamicPartitionsRequestResult(DynamicPartitionsRequestMixin, graphene.ObjectType):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
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


class GrapheneRequestedMaterializationsForAsset(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)
    partitionKeys = non_null_list(graphene.String)

    class Meta:
        name = "RequestedMaterializationsForAsset"


class GrapheneInstigationTick(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    tickId = graphene.NonNull(graphene.ID)
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
    endTimestamp = graphene.Field(graphene.Float)
    requestedAssetKeys = non_null_list(GrapheneAssetKey)
    requestedAssetMaterializationCount = graphene.NonNull(graphene.Int)
    requestedMaterializationsForAssets = non_null_list(GrapheneRequestedMaterializationsForAsset)
    autoMaterializeAssetEvaluationId = graphene.Field(graphene.ID)
    instigationType = graphene.NonNull(GrapheneInstigationType)

    class Meta:
        name = "InstigationTick"

    def __init__(self, tick: InstigatorTick):
        self._tick = check.inst_param(tick, "tick", InstigatorTick)

        super().__init__(
            status=tick.status.value,
            timestamp=tick.timestamp,
            runIds=tick.run_ids,
            runKeys=tick.run_keys,
            error=GraphenePythonError(tick.error) if tick.error else None,
            instigationType=tick.instigator_type,
            skipReason=tick.skip_reason,
            originRunIds=tick.origin_run_ids,
            cursor=tick.cursor,
            logKey=tick.log_key,
            endTimestamp=tick.end_timestamp,
            autoMaterializeAssetEvaluationId=tick.automation_condition_evaluation_id,
        )

    def resolve_id(self, _):
        return f"{self._tick.instigator_origin_id}:{self._tick.timestamp}"

    def resolve_tickId(self, _: ResolveInfo) -> str:
        return str(self._tick.tick_id)

    def resolve_runs(self, graphene_info: ResolveInfo):
        from dagster_graphql.schema.pipelines.pipeline import GrapheneRun

        instance = graphene_info.context.instance
        run_ids = self._tick.origin_run_ids or self._tick.run_ids or []

        # filter out backfills
        run_ids = [run_id for run_id in run_ids if is_valid_run_id(run_id)]

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

    def resolve_requestedAssetKeys(self, _):
        return [
            GrapheneAssetKey(path=asset_key.path) for asset_key in self._tick.requested_asset_keys
        ]

    def resolve_requestedMaterializationsForAssets(self, _):
        return [
            GrapheneRequestedMaterializationsForAsset(
                assetKey=GrapheneAssetKey(path=asset_key.path), partitionKeys=list(partition_keys)
            )
            for asset_key, partition_keys in self._tick.requested_assets_and_partitions.items()
        ]

    def resolve_requestedAssetMaterializationCount(self, _):
        return self._tick.requested_asset_materialization_count


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
            if not repository.has_sensor(self._selector.sensor_name):
                raise UserFacingGraphQLError(
                    GrapheneSensorNotFoundError(self._selector.sensor_name)
                )
            sensor_data: Union[SensorExecutionData, SerializableErrorInfo]
            try:
                sensor_data = code_location.get_sensor_execution_data(
                    name=self._selector.sensor_name,
                    instance=graphene_info.context.instance,
                    repository_handle=repository.handle,
                    cursor=self._cursor,
                    last_tick_completion_time=None,
                    last_run_key=None,
                    last_sensor_start_time=None,
                    log_key=None,
                )
            except Exception:
                sensor_data = serializable_error_info_from_exc_info(sys.exc_info())
            return GrapheneTickEvaluation(sensor_data)
        else:
            if not repository.has_schedule(self._selector.schedule_name):
                raise UserFacingGraphQLError(
                    GrapheneScheduleNotFoundError(self._selector.schedule_name)
                )
            if not self.timestamp:
                raise Exception(
                    "No tick timestamp provided when attempting to dry-run schedule"
                    f" {self._selector.schedule_name}."
                )
            schedule = repository.get_schedule(self._selector.schedule_name)
            timezone_str = schedule.execution_timezone
            if not timezone_str:
                timezone_str = "UTC"

            next_tick_datetime = next(schedule.execution_time_iterator(self.timestamp))
            schedule_data: Union[ScheduleExecutionData, SerializableErrorInfo]
            try:
                schedule_data = code_location.get_schedule_execution_data(
                    instance=graphene_info.context.instance,
                    repository_handle=repository.handle,
                    schedule_name=schedule.name,
                    scheduled_execution_time=TimestampWithTimezone(
                        next_tick_datetime.timestamp(),
                        timezone_str,
                    ),
                    log_key=None,
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
    jobName = graphene.String()

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

    def resolve_jobName(self, _graphene_info: ResolveInfo):
        return self._run_request.job_name


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
    tick = graphene.Field(
        graphene.NonNull(GrapheneInstigationTick),
        tickId=graphene.NonNull(graphene.ID),
    )
    ticks = graphene.Field(
        non_null_list(GrapheneInstigationTick),
        dayRange=graphene.Int(),
        dayOffset=graphene.Int(),
        limit=graphene.Int(),
        cursor=graphene.String(),
        statuses=graphene.List(graphene.NonNull(GrapheneInstigationTickStatus)),
        beforeTimestamp=graphene.Float(),
        afterTimestamp=graphene.Float(),
    )
    nextTick = graphene.Field(GrapheneDryRunInstigationTick)
    runningCount = graphene.NonNull(graphene.Int)  # remove with cron scheduler

    hasStartPermission = graphene.NonNull(graphene.Boolean)
    hasStopPermission = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "InstigationState"

    def __init__(
        self,
        instigator_state: InstigatorState,
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
        cid = CompoundID(
            remote_origin_id=instigator_state.instigator_origin_id,
            selector_id=instigator_state.selector_id,
        )
        super().__init__(
            id=cid.to_string(),
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
        origin = self._instigator_state.origin.repository_origin
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
        from dagster_graphql.schema.pipelines.pipeline import GrapheneRun

        repository_label = self._instigator_state.origin.repository_origin.get_label()
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

    def resolve_tick(
        self,
        graphene_info: ResolveInfo,
        tickId: str,
    ) -> GrapheneInstigationTick:
        schedule_storage = check.not_none(graphene_info.context.instance.schedule_storage)
        tick = schedule_storage.get_tick(int(tickId))

        return GrapheneInstigationTick(tick)

    def resolve_ticks(
        self,
        graphene_info,
        dayRange=None,
        dayOffset=None,
        limit=None,
        cursor=None,
        statuses=None,
        beforeTimestamp=None,
        afterTimestamp=None,
    ):
        return get_instigation_ticks(
            graphene_info=graphene_info,
            instigator_type=self._instigator_state.instigator_type,
            instigator_origin_id=self._instigator_state.instigator_origin_id,
            selector_id=self._instigator_state.selector_id,
            batch_loader=self._batch_loader,
            dayRange=dayRange,
            dayOffset=dayOffset,
            limit=limit,
            cursor=cursor,
            status_strings=statuses,
            before=beforeTimestamp,
            after=afterTimestamp,
        )

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

    def __init__(self, target):
        super().__init__()
        self.name = check.str_param(target, "target")
        self.message = f"Could not find instigation state for `{target}`"


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
