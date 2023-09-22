from typing import TYPE_CHECKING, Optional, Union

import dagster._check as check
import graphene
from dagster._core.events import AssetLineageInfo, DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.plan.objects import ErrorSource
from dagster._core.execution.stats import RunStepKeyStatsSnapshot

from dagster_graphql.schema.tags import GrapheneEventTag

from ...implementation.events import construct_basic_params
from ...implementation.fetch_runs import get_run_by_id, get_step_stats
from ...implementation.loader import BatchRunLoader
from ..asset_checks import GrapheneAssetCheckEvaluation
from ..asset_key import GrapheneAssetKey, GrapheneAssetLineageInfo
from ..errors import GraphenePythonError, GrapheneRunNotFoundError
from ..metadata import GrapheneMetadataEntry
from ..runs import GrapheneStepEventStatus
from ..util import ResolveInfo, non_null_list
from .log_level import GrapheneLogLevel

if TYPE_CHECKING:
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun


class GrapheneMessageEvent(graphene.Interface):
    runId = graphene.NonNull(graphene.String)
    message = graphene.NonNull(graphene.String)
    timestamp = graphene.NonNull(graphene.String)
    level = graphene.NonNull(GrapheneLogLevel)
    stepKey = graphene.Field(graphene.String)
    solidHandleID = graphene.Field(graphene.String)
    eventType = graphene.Field(graphene.Enum.from_enum(DagsterEventType))

    class Meta:
        name = "MessageEvent"


class GrapheneDisplayableEvent(graphene.Interface):
    label = graphene.String()
    description = graphene.String()
    metadataEntries = non_null_list(GrapheneMetadataEntry)

    class Meta:
        name = "DisplayableEvent"


class GrapheneMarkerEvent(graphene.Interface):
    markerStart = graphene.String()
    markerEnd = graphene.String()

    class Meta:
        name = "MarkerEvent"


class GrapheneErrorEvent(graphene.Interface):
    error = graphene.Field(GraphenePythonError)

    class Meta:
        name = "ErrorEvent"


class GrapheneMissingRunIdErrorEvent(graphene.ObjectType):
    invalidRunId = graphene.NonNull(graphene.String)

    class Meta:
        name = "MissingRunIdErrorEvent"


class GrapheneLogMessageEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent,)
        name = "LogMessageEvent"


class GrapheneRunEvent(graphene.Interface):
    pipelineName = graphene.NonNull(graphene.String)

    class Meta:
        name = "RunEvent"


class GrapheneRunEnqueuedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "RunEnqueuedEvent"


class GrapheneRunDequeuedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "RunDequeuedEvent"


class GrapheneRunStartingEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "RunStartingEvent"


class GrapheneRunCancelingEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "RunCancelingEvent"


class GrapheneRunCanceledEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "RunCanceledEvent"


class GrapheneRunStartEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "RunStartEvent"


class GrapheneRunSuccessEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "RunSuccessEvent"


class GrapheneRunFailureEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent, GrapheneErrorEvent)
        name = "RunFailureEvent"


class GrapheneAlertStartEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "AlertStartEvent"


class GrapheneAlertSuccessEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "AlertSuccessEvent"


class GrapheneAlertFailureEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)
        name = "AlertFailureEvent"


class GrapheneStepEvent(graphene.Interface):
    stepKey = graphene.Field(graphene.String)
    solidHandleID = graphene.Field(graphene.String)

    class Meta:
        name = "StepEvent"


class GrapheneExecutionStepStartEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepStartEvent"


class GrapheneExecutionStepRestartEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepRestartEvent"


class GrapheneExecutionStepUpForRetryEvent(graphene.ObjectType):
    secondsToWait = graphene.Field(graphene.Int)

    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent, GrapheneErrorEvent)
        name = "ExecutionStepUpForRetryEvent"


class GrapheneExecutionStepSkippedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepSkippedEvent"


class GrapheneObjectStoreOperationType(graphene.Enum):
    SET_OBJECT = "SET_OBJECT"
    GET_OBJECT = "GET_OBJECT"
    RM_OBJECT = "RM_OBJECT"
    CP_OBJECT = "CP_OBJECT"

    class Meta:
        name = "ObjectStoreOperationType"


class GrapheneObjectStoreOperationResult(graphene.ObjectType):
    op = graphene.NonNull(GrapheneObjectStoreOperationType)

    class Meta:
        interfaces = (GrapheneDisplayableEvent,)
        name = "ObjectStoreOperationResult"

    def resolve_metadataEntries(self, _graphene_info: ResolveInfo):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self.metadata)


class GrapheneExpectationResult(graphene.ObjectType):
    success = graphene.NonNull(graphene.Boolean)

    class Meta:
        interfaces = (GrapheneDisplayableEvent,)
        name = "ExpectationResult"

    def resolve_metadataEntries(self, _graphene_info: ResolveInfo):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self.metadata)


class GrapheneTypeCheck(graphene.ObjectType):
    success = graphene.NonNull(graphene.Boolean)

    class Meta:
        interfaces = (GrapheneDisplayableEvent,)
        name = "TypeCheck"

    def resolve_metadataEntries(self, _graphene_info: ResolveInfo):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self.metadata)


class GrapheneFailureMetadata(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneDisplayableEvent,)
        name = "FailureMetadata"

    def resolve_metadataEntries(self, _graphene_info: ResolveInfo):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self.metadata)


class GrapheneExecutionStepInputEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepInputEvent"

    input_name = graphene.NonNull(graphene.String)
    type_check = graphene.NonNull(GrapheneTypeCheck)


class GrapheneExecutionStepOutputEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent, GrapheneDisplayableEvent)
        name = "ExecutionStepOutputEvent"

    output_name = graphene.NonNull(graphene.String)
    type_check = graphene.NonNull(GrapheneTypeCheck)


class GrapheneExecutionStepSuccessEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepSuccessEvent"


class GrapheneExecutionStepFailureEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent, GrapheneErrorEvent)
        name = "ExecutionStepFailureEvent"

    errorSource = graphene.Field(graphene.Enum.from_enum(ErrorSource))
    failureMetadata = graphene.Field(GrapheneFailureMetadata)


class GrapheneHookCompletedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "HookCompletedEvent"


class GrapheneHookSkippedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "HookSkippedEvent"


class GrapheneHookErroredEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent, GrapheneErrorEvent)
        name = "HookErroredEvent"


class GrapheneLogsCapturedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent,)
        name = "LogsCapturedEvent"

    fileKey = graphene.NonNull(graphene.String)
    stepKeys = graphene.List(graphene.NonNull(graphene.String))
    externalUrl = graphene.String()
    externalStdoutUrl = graphene.String()
    externalStderrUrl = graphene.String()
    pid = graphene.Int()
    # legacy name for compute log file key... required for back-compat reasons, but has been
    # renamed to fileKey for newer versions of the Dagster UI
    logKey = graphene.NonNull(graphene.String)


def _construct_asset_event_metadata_params(event, metadata):
    metadata_params = {"label": metadata.label, "description": metadata.description}
    metadata_params.update(construct_basic_params(event))
    return metadata_params


class AssetEventMixin:
    assetKey = graphene.Field(GrapheneAssetKey)
    runOrError = graphene.NonNull("dagster_graphql.schema.pipelines.pipeline.GrapheneRunOrError")
    stepStats = graphene.NonNull(lambda: GrapheneRunStepStats)
    partition = graphene.Field(graphene.String)
    tags = non_null_list(GrapheneEventTag)

    def __init__(self, event, metadata):
        self._event = event
        self._metadata = metadata

    def resolve_assetKey(self, _graphene_info) -> Optional[GrapheneAssetKey]:
        asset_key = self._metadata.asset_key

        if not asset_key:
            return None

        return GrapheneAssetKey(path=asset_key.path)

    def resolve_runOrError(
        self,
        graphene_info,
    ) -> Union["GrapheneRun", GrapheneRunNotFoundError]:
        return get_run_by_id(graphene_info, self._event.run_id)

    def resolve_stepStats(self, graphene_info) -> "GrapheneRunStepStats":
        run_id = self.runId  # type: ignore  # (value obj access)
        step_key = self.stepKey  # type: ignore  # (value obj access)
        stats = get_step_stats(graphene_info, run_id, step_keys=[step_key])
        return stats[0]

    def resolve_metadataEntries(self, _graphene_info: ResolveInfo):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self._metadata.metadata)

    def resolve_partition(self, _graphene_info: ResolveInfo):
        return self._metadata.partition

    def resolve_tags(self, _graphene_info):
        if self._metadata.tags is None:
            return []
        else:
            return [
                GrapheneEventTag(key=key, value=value) for key, value in self._metadata.tags.items()
            ]


class GrapheneMaterializationEvent(graphene.ObjectType, AssetEventMixin):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent, GrapheneDisplayableEvent)
        name = "MaterializationEvent"

    assetLineage = non_null_list(GrapheneAssetLineageInfo)

    def __init__(self, event: EventLogEntry, assetLineage=None, loader=None):
        self._asset_lineage = check.opt_list_param(assetLineage, "assetLineage", AssetLineageInfo)
        self._batch_run_loader = check.opt_inst_param(loader, "loader", BatchRunLoader)

        dagster_event = check.not_none(event.dagster_event)
        materialization = dagster_event.step_materialization_data.materialization
        super().__init__(**_construct_asset_event_metadata_params(event, materialization))
        AssetEventMixin.__init__(
            self,
            event=event,
            metadata=materialization,
        )

    def resolve_runOrError(self, graphene_info: ResolveInfo):
        from ..pipelines.pipeline import GrapheneRun

        if self._batch_run_loader:
            record = self._batch_run_loader.get_run_record_by_run_id(self._event.run_id)
            if not record:
                return GrapheneRunNotFoundError(self._event.run_id)

            return GrapheneRun(record)

        return super().resolve_runOrError(graphene_info)

    def resolve_assetLineage(self, _graphene_info: ResolveInfo):
        return [
            GrapheneAssetLineageInfo(
                assetKey=lineage_info.asset_key,
                partitions=lineage_info.partitions,
            )
            for lineage_info in self._asset_lineage
        ]


class GrapheneObservationEvent(graphene.ObjectType, AssetEventMixin):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent, GrapheneDisplayableEvent)
        name = "ObservationEvent"

    def __init__(self, event):
        observation = event.dagster_event.asset_observation_data.asset_observation
        super().__init__(**_construct_asset_event_metadata_params(event, observation))
        AssetEventMixin.__init__(
            self,
            event=event,
            metadata=observation,
        )


class GrapheneAssetMaterializationPlannedEvent(graphene.ObjectType):
    assetKey = graphene.Field(GrapheneAssetKey)
    runOrError = graphene.NonNull("dagster_graphql.schema.pipelines.pipeline.GrapheneRunOrError")

    class Meta:
        name = "AssetMaterializationPlannedEvent"
        interfaces = (GrapheneMessageEvent, GrapheneRunEvent)

    def __init__(self, event):
        self._event = event
        super().__init__(**construct_basic_params(event))

    def resolve_assetKey(self, _graphene_info: ResolveInfo):
        return self._event.dagster_event.asset_materialization_planned_data.asset_key

    def resolve_runOrError(self, graphene_info: ResolveInfo):
        return get_run_by_id(graphene_info, self._event.run_id)


class GrapheneHandledOutputEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent, GrapheneDisplayableEvent)
        name = "HandledOutputEvent"

    output_name = graphene.NonNull(graphene.String)
    manager_key = graphene.NonNull(graphene.String)


class GrapheneLoadedInputEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent, GrapheneDisplayableEvent)
        name = "LoadedInputEvent"

    input_name = graphene.NonNull(graphene.String)
    manager_key = graphene.NonNull(graphene.String)
    upstream_output_name = graphene.Field(graphene.String)
    upstream_step_key = graphene.Field(graphene.String)


class GrapheneObjectStoreOperationEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ObjectStoreOperationEvent"

    operation_result = graphene.NonNull(GrapheneObjectStoreOperationResult)


class GrapheneEngineEvent(graphene.ObjectType):
    class Meta:
        interfaces = (
            GrapheneMessageEvent,
            GrapheneDisplayableEvent,
            GrapheneStepEvent,
            GrapheneMarkerEvent,
            GrapheneErrorEvent,
        )
        name = "EngineEvent"


class GrapheneResourceInitFailureEvent(graphene.ObjectType):
    class Meta:
        interfaces = (
            GrapheneMessageEvent,
            GrapheneDisplayableEvent,
            GrapheneStepEvent,
            GrapheneMarkerEvent,
            GrapheneErrorEvent,
        )
        name = "ResourceInitFailureEvent"


class GrapheneResourceInitStartedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (
            GrapheneMessageEvent,
            GrapheneDisplayableEvent,
            GrapheneStepEvent,
            GrapheneMarkerEvent,
        )
        name = "ResourceInitStartedEvent"


class GrapheneResourceInitSuccessEvent(graphene.ObjectType):
    class Meta:
        interfaces = (
            GrapheneMessageEvent,
            GrapheneDisplayableEvent,
            GrapheneStepEvent,
            GrapheneMarkerEvent,
        )
        name = "ResourceInitSuccessEvent"


class GrapheneStepWorkerStartedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (
            GrapheneMessageEvent,
            GrapheneDisplayableEvent,
            GrapheneStepEvent,
            GrapheneMarkerEvent,
        )
        name = "StepWorkerStartedEvent"


class GrapheneStepWorkerStartingEvent(graphene.ObjectType):
    class Meta:
        interfaces = (
            GrapheneMessageEvent,
            GrapheneDisplayableEvent,
            GrapheneStepEvent,
            GrapheneMarkerEvent,
        )
        name = "StepWorkerStartingEvent"


class GrapheneStepExpectationResultEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "StepExpectationResultEvent"

    expectation_result = graphene.NonNull(GrapheneExpectationResult)


class GrapheneAssetCheckEvaluationPlannedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "AssetCheckEvaluationPlannedEvent"

    assetKey = graphene.NonNull(GrapheneAssetKey)
    checkName = graphene.NonNull(graphene.String)


class GrapheneAssetCheckEvaluationEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "AssetCheckEvaluationEvent"

    evaluation = graphene.NonNull(GrapheneAssetCheckEvaluation)


# Should be a union of all possible events
class GrapheneDagsterRunEvent(graphene.Union):
    class Meta:
        types = (
            GrapheneExecutionStepFailureEvent,
            GrapheneExecutionStepInputEvent,
            GrapheneExecutionStepOutputEvent,
            GrapheneExecutionStepSkippedEvent,
            GrapheneExecutionStepStartEvent,
            GrapheneExecutionStepSuccessEvent,
            GrapheneExecutionStepUpForRetryEvent,
            GrapheneExecutionStepRestartEvent,
            GrapheneLogMessageEvent,
            GrapheneResourceInitFailureEvent,
            GrapheneResourceInitStartedEvent,
            GrapheneResourceInitSuccessEvent,
            GrapheneRunFailureEvent,
            GrapheneRunStartEvent,
            GrapheneRunEnqueuedEvent,
            GrapheneRunDequeuedEvent,
            GrapheneRunStartingEvent,
            GrapheneRunCancelingEvent,
            GrapheneRunCanceledEvent,
            GrapheneRunSuccessEvent,
            GrapheneStepWorkerStartedEvent,
            GrapheneStepWorkerStartingEvent,
            GrapheneHandledOutputEvent,
            GrapheneLoadedInputEvent,
            GrapheneLogsCapturedEvent,
            GrapheneObjectStoreOperationEvent,
            GrapheneStepExpectationResultEvent,
            GrapheneMaterializationEvent,
            GrapheneObservationEvent,
            GrapheneEngineEvent,
            GrapheneHookCompletedEvent,
            GrapheneHookSkippedEvent,
            GrapheneHookErroredEvent,
            GrapheneAlertStartEvent,
            GrapheneAlertSuccessEvent,
            GrapheneAlertFailureEvent,
            GrapheneAssetMaterializationPlannedEvent,
            GrapheneAssetCheckEvaluationPlannedEvent,
            GrapheneAssetCheckEvaluationEvent,
        )
        name = "DagsterRunEvent"


class GraphenePipelineRunStepStats(graphene.Interface):
    runId = graphene.NonNull(graphene.String)
    stepKey = graphene.NonNull(graphene.String)
    status = graphene.Field(GrapheneStepEventStatus)
    startTime = graphene.Field(graphene.Float)
    endTime = graphene.Field(graphene.Float)
    materializations = non_null_list(GrapheneMaterializationEvent)
    expectationResults = non_null_list(GrapheneExpectationResult)

    class Meta:
        name = "PipelineRunStepStats"


class GrapheneRunMarker(graphene.ObjectType):
    startTime = graphene.Field(graphene.Float)
    endTime = graphene.Field(graphene.Float)

    class Meta:
        name = "RunMarker"


class GrapheneRunStepStats(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)
    stepKey = graphene.NonNull(graphene.String)
    status = graphene.Field(GrapheneStepEventStatus)
    startTime = graphene.Field(graphene.Float)
    endTime = graphene.Field(graphene.Float)
    materializations = non_null_list(GrapheneMaterializationEvent)
    expectationResults = non_null_list(GrapheneExpectationResult)
    attempts = non_null_list(GrapheneRunMarker)
    markers = non_null_list(GrapheneRunMarker)

    class Meta:
        interfaces = (GraphenePipelineRunStepStats,)
        name = "RunStepStats"

    def __init__(self, stats):
        self._stats = check.inst_param(stats, "stats", RunStepKeyStatsSnapshot)
        super().__init__(
            runId=stats.run_id,
            stepKey=stats.step_key,
            status=stats.status.value,
            startTime=stats.start_time,
            endTime=stats.end_time,
            materializations=stats.materialization_events,
            expectationResults=stats.expectation_results,
            attempts=[
                GrapheneRunMarker(startTime=attempt.start_time, endTime=attempt.end_time)
                for attempt in stats.attempts_list
            ],
            markers=[
                GrapheneRunMarker(startTime=marker.start_time, endTime=marker.end_time)
                for marker in stats.markers
            ],
        )
