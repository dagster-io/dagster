import graphene
from dagster import check
from dagster.core.execution.stats import RunStepKeyStatsSnapshot

from ...implementation.fetch_runs import get_step_stats
from ..asset_key import GrapheneAssetKey
from ..errors import GraphenePythonError
from ..runs import GrapheneStepEventStatus
from ..util import non_null_list
from .log_level import GrapheneLogLevel


class GrapheneMessageEvent(graphene.Interface):
    runId = graphene.NonNull(graphene.String)
    message = graphene.NonNull(graphene.String)
    timestamp = graphene.NonNull(graphene.String)
    level = graphene.NonNull(GrapheneLogLevel)
    stepKey = graphene.Field(graphene.String)
    solidHandleID = graphene.Field(graphene.String)

    class Meta:
        name = "MessageEvent"


class GrapheneEventMetadataEntry(graphene.Interface):
    label = graphene.NonNull(graphene.String)
    description = graphene.String()

    class Meta:
        name = "EventMetadataEntry"


class GrapheneDisplayableEvent(graphene.Interface):
    label = graphene.NonNull(graphene.String)
    description = graphene.String()
    metadataEntries = non_null_list(GrapheneEventMetadataEntry)

    class Meta:
        name = "DisplayableEvent"


class GrapheneMissingRunIdErrorEvent(graphene.ObjectType):
    invalidRunId = graphene.NonNull(graphene.String)

    class Meta:
        name = "MissingRunIdErrorEvent"


class GrapheneLogMessageEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent,)
        name = "LogMessageEvent"


class GraphenePipelineEvent(graphene.Interface):
    pipelineName = graphene.NonNull(graphene.String)

    class Meta:
        name = "PipelineEvent"


class GraphenePipelineEnqueuedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GraphenePipelineEvent)
        name = "PipelineEnqueuedEvent"


class GraphenePipelineDequeuedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GraphenePipelineEvent)
        name = "PipelineDequeuedEvent"


class GraphenePipelineStartingEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GraphenePipelineEvent)
        name = "PipelineStartingEvent"


class GraphenePipelineCancelingEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GraphenePipelineEvent)
        name = "PipelineCancelingEvent"


class GraphenePipelineCanceledEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GraphenePipelineEvent)
        name = "PipelineCanceledEvent"


class GraphenePipelineStartEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GraphenePipelineEvent)
        name = "PipelineStartEvent"


class GraphenePipelineSuccessEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GraphenePipelineEvent)
        name = "PipelineSuccessEvent"


class GraphenePipelineFailureEvent(graphene.ObjectType):
    error = graphene.Field(GraphenePythonError)

    class Meta:
        interfaces = (GrapheneMessageEvent, GraphenePipelineEvent)
        name = "PipelineFailureEvent"


class GraphenePipelineInitFailureEvent(graphene.ObjectType):
    error = graphene.NonNull(GraphenePythonError)

    class Meta:
        interfaces = (GrapheneMessageEvent, GraphenePipelineEvent)
        name = "PipelineInitFailureEvent"


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
    error = graphene.NonNull(GraphenePythonError)
    secondsToWait = graphene.Field(graphene.Int)

    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepUpForRetryEvent"


class GrapheneExecutionStepSkippedEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepSkippedEvent"


class GrapheneEventPathMetadataEntry(graphene.ObjectType):
    path = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventPathMetadataEntry"


class GrapheneEventJsonMetadataEntry(graphene.ObjectType):
    jsonString = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventJsonMetadataEntry"


class GrapheneEventTextMetadataEntry(graphene.ObjectType):
    text = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventTextMetadataEntry"


class GrapheneEventUrlMetadataEntry(graphene.ObjectType):
    url = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventUrlMetadataEntry"


class GrapheneEventMarkdownMetadataEntry(graphene.ObjectType):
    md_str = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventMarkdownMetadataEntry"


class GrapheneEventPythonArtifactMetadataEntry(graphene.ObjectType):
    module = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventPythonArtifactMetadataEntry"


class GrapheneEventFloatMetadataEntry(graphene.ObjectType):
    floatValue = graphene.NonNull(graphene.Float)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventFloatMetadataEntry"


class GrapheneEventIntMetadataEntry(graphene.ObjectType):
    intValue = graphene.NonNull(graphene.Int)

    class Meta:
        interfaces = (GrapheneEventMetadataEntry,)
        name = "EventIntMetadataEntry"


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

    def resolve_metadataEntries(self, _graphene_info):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self.metadata_entries)  # pylint: disable=no-member


class GrapheneMaterialization(graphene.ObjectType):
    assetKey = graphene.Field(GrapheneAssetKey)

    class Meta:
        interfaces = (GrapheneDisplayableEvent,)
        name = "Materialization"

    def resolve_metadataEntries(self, _graphene_info):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self.metadata_entries)  # pylint: disable=no-member

    def resolve_assetKey(self, _graphene_info):
        asset_key = self.asset_key  # pylint: disable=no-member

        if not asset_key:
            return None

        return GrapheneAssetKey(path=asset_key.path)


class GrapheneExpectationResult(graphene.ObjectType):
    success = graphene.NonNull(graphene.Boolean)

    class Meta:
        interfaces = (GrapheneDisplayableEvent,)
        name = "ExpectationResult"

    def resolve_metadataEntries(self, _graphene_info):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self.metadata_entries)  # pylint: disable=no-member


class GrapheneTypeCheck(graphene.ObjectType):
    success = graphene.NonNull(graphene.Boolean)

    class Meta:
        interfaces = (GrapheneDisplayableEvent,)
        name = "TypeCheck"

    def resolve_metadataEntries(self, _graphene_info):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self.metadata_entries)  # pylint: disable=no-member


class GrapheneFailureMetadata(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneDisplayableEvent,)
        name = "FailureMetadata"

    def resolve_metadataEntries(self, _graphene_info):
        from ...implementation.events import _to_metadata_entries

        return _to_metadata_entries(self.metadata_entries)  # pylint: disable=no-member


class GrapheneExecutionStepInputEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepInputEvent"

    input_name = graphene.NonNull(graphene.String)
    type_check = graphene.NonNull(GrapheneTypeCheck)


class GrapheneExecutionStepOutputEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepOutputEvent"

    output_name = graphene.NonNull(graphene.String)
    type_check = graphene.NonNull(GrapheneTypeCheck)


class GrapheneExecutionStepSuccessEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepSuccessEvent"


class GrapheneExecutionStepFailureEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "ExecutionStepFailureEvent"

    error = graphene.NonNull(GraphenePythonError)
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
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "HookErroredEvent"

    error = graphene.NonNull(GraphenePythonError)


class GrapheneStepMaterializationEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "StepMaterializationEvent"

    materialization = graphene.NonNull(GrapheneMaterialization)
    stepStats = graphene.NonNull(lambda: GraphenePipelineRunStepStats)

    def resolve_stepStats(self, graphene_info):
        run_id = self.runId  # pylint: disable=no-member
        step_key = self.stepKey  # pylint: disable=no-member
        stats = get_step_stats(graphene_info, run_id, step_keys=[step_key])
        return stats[0]


class GrapheneHandledOutputEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "HandledOutputEvent"

    output_name = graphene.NonNull(graphene.String)
    manager_key = graphene.NonNull(graphene.String)


class GrapheneLoadedInputEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
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
        interfaces = (GrapheneMessageEvent, GrapheneDisplayableEvent, GrapheneStepEvent)
        name = "EngineEvent"

    error = graphene.Field(GraphenePythonError)
    marker_start = graphene.Field(graphene.String)
    marker_end = graphene.Field(graphene.String)


class GrapheneStepExpectationResultEvent(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneMessageEvent, GrapheneStepEvent)
        name = "StepExpectationResultEvent"

    expectation_result = graphene.NonNull(GrapheneExpectationResult)


# Should be a union of all possible events
class GraphenePipelineRunEvent(graphene.Union):
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
            GraphenePipelineFailureEvent,
            GraphenePipelineInitFailureEvent,
            GraphenePipelineStartEvent,
            GraphenePipelineEnqueuedEvent,
            GraphenePipelineDequeuedEvent,
            GraphenePipelineStartingEvent,
            GraphenePipelineCancelingEvent,
            GraphenePipelineCanceledEvent,
            GraphenePipelineSuccessEvent,
            GrapheneHandledOutputEvent,
            GrapheneLoadedInputEvent,
            GrapheneObjectStoreOperationEvent,
            GrapheneStepExpectationResultEvent,
            GrapheneStepMaterializationEvent,
            GrapheneEngineEvent,
            GrapheneHookCompletedEvent,
            GrapheneHookSkippedEvent,
            GrapheneHookErroredEvent,
        )
        name = "PipelineRunEvent"


class GraphenePipelineRunStepStats(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)
    stepKey = graphene.NonNull(graphene.String)
    status = graphene.Field(GrapheneStepEventStatus)
    startTime = graphene.Field(graphene.Float)
    endTime = graphene.Field(graphene.Float)
    materializations = non_null_list(GrapheneMaterialization)
    expectationResults = non_null_list(GrapheneExpectationResult)

    class Meta:
        name = "PipelineRunStepStats"

    def __init__(self, stats):
        self._stats = check.inst_param(stats, "stats", RunStepKeyStatsSnapshot)
        super().__init__(
            runId=stats.run_id,
            stepKey=stats.step_key,
            status=stats.status,
            startTime=stats.start_time,
            endTime=stats.end_time,
            materializations=stats.materializations,
            expectationResults=stats.expectation_results,
        )
