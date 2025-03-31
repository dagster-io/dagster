import graphene
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.events import DagsterEventType
from dagster._core.execution.backfill import BulkActionsFilter, BulkActionStatus
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._time import datetime_from_timestamp
from dagster._utils import check

from dagster_graphql.schema.pipelines.status import GrapheneRunStatus
from dagster_graphql.schema.runs import GrapheneRunConfigData
from dagster_graphql.schema.util import non_null_list


class GrapheneAssetKeyInput(graphene.InputObjectType):
    path = non_null_list(graphene.String)

    class Meta:
        name = "AssetKeyInput"

    def to_asset_key(self) -> AssetKey:
        return AssetKey(self.path)


class GrapheneAssetCheckHandleInput(graphene.InputObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKeyInput)
    name = graphene.NonNull(graphene.String)

    class Meta:
        name = "AssetCheckHandleInput"


class GrapheneExecutionTag(graphene.InputObjectType):
    key = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)

    class Meta:
        name = "ExecutionTag"


class GrapheneRunsFilter(graphene.InputObjectType):
    runIds = graphene.List(graphene.String)
    pipelineName = graphene.InputField(graphene.String)
    tags = graphene.List(graphene.NonNull(GrapheneExecutionTag))
    statuses = graphene.List(graphene.NonNull(GrapheneRunStatus))
    snapshotId = graphene.InputField(graphene.String)
    updatedAfter = graphene.InputField(graphene.Float)
    updatedBefore = graphene.InputField(graphene.Float)
    createdBefore = graphene.InputField(graphene.Float)
    createdAfter = graphene.InputField(graphene.Float)
    mode = graphene.InputField(graphene.String)

    class Meta:
        description = """This type represents a filter on Dagster runs."""
        name = "RunsFilter"

    def to_selector(self):
        if self.tags:
            # We are wrapping self.tags in a list because graphene.List is not marked as iterable
            tags = {tag["key"]: tag["value"] for tag in list(self.tags)}
        else:
            tags = None

        if self.statuses:
            statuses = [DagsterRunStatus[status.value] for status in self.statuses]
        else:
            statuses = None

        updated_before = datetime_from_timestamp(self.updatedBefore) if self.updatedBefore else None
        updated_after = datetime_from_timestamp(self.updatedAfter) if self.updatedAfter else None
        created_before = datetime_from_timestamp(self.createdBefore) if self.createdBefore else None
        created_after = datetime_from_timestamp(self.createdAfter) if self.createdAfter else None

        return RunsFilter(
            run_ids=self.runIds if self.runIds else None,
            job_name=self.pipelineName,
            tags=tags,
            statuses=statuses,
            snapshot_id=self.snapshotId,
            updated_before=updated_before,
            updated_after=updated_after,
            created_before=created_before,
            created_after=created_after,
        )


class GrapheneStepOutputHandle(graphene.InputObjectType):
    stepKey = graphene.NonNull(graphene.String)
    outputName = graphene.NonNull(graphene.String)

    class Meta:
        name = "StepOutputHandle"


class GraphenePipelineSelector(graphene.InputObjectType):
    pipelineName = graphene.NonNull(graphene.String)
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))
    assetSelection = graphene.List(graphene.NonNull(GrapheneAssetKeyInput))
    assetCheckSelection = graphene.List(graphene.NonNull(GrapheneAssetCheckHandleInput))

    class Meta:
        description = """This type represents the fields necessary to identify a
        pipeline or pipeline subset."""
        name = "PipelineSelector"


class GrapheneAssetGroupSelector(graphene.InputObjectType):
    groupName = graphene.NonNull(graphene.String)
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)

    class Meta:
        description = """This type represents the fields necessary to identify
        an asset group."""
        name = "AssetGroupSelector"


class GrapheneGraphSelector(graphene.InputObjectType):
    graphName = graphene.NonNull(graphene.String)
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)

    class Meta:
        description = """This type represents the fields necessary to identify a
        graph"""
        name = "GraphSelector"


class GrapheneJobOrPipelineSelector(graphene.InputObjectType):
    pipelineName = graphene.String()
    jobName = graphene.String()
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))
    assetSelection = graphene.List(graphene.NonNull(GrapheneAssetKeyInput))
    assetCheckSelection = graphene.List(graphene.NonNull(GrapheneAssetCheckHandleInput))

    class Meta:
        description = """This type represents the fields necessary to identify a job or pipeline"""
        name = "JobOrPipelineSelector"


class GrapheneRepositorySelector(graphene.InputObjectType):
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)

    class Meta:
        description = """This type represents the fields necessary to identify a repository."""
        name = "RepositorySelector"


class GraphenePartitionSetSelector(graphene.InputObjectType):
    partitionSetName = graphene.NonNull(graphene.String)
    repositorySelector = graphene.NonNull(GrapheneRepositorySelector)

    class Meta:
        description = """This type represents the fields necessary to identify a
        pipeline or pipeline subset."""
        name = "PartitionSetSelector"


class GraphenePartitionRangeSelector(graphene.InputObjectType):
    start = graphene.NonNull(graphene.String)
    end = graphene.NonNull(graphene.String)

    class Meta:
        description = """This type represents a partition range selection with start and end."""
        name = "PartitionRangeSelector"


class GraphenePartitionsSelector(graphene.InputObjectType):
    range = graphene.InputField(GraphenePartitionRangeSelector)
    ranges = graphene.InputField(graphene.List(graphene.NonNull(GraphenePartitionRangeSelector)))

    class Meta:
        description = """This type represents a partitions selection."""
        name = "PartitionsSelector"


class GraphenePartitionsByAssetSelector(graphene.InputObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKeyInput)
    partitions = graphene.InputField(GraphenePartitionsSelector)

    class Meta:
        description = """This type represents a partitions selection for an asset."""
        name = "PartitionsByAssetSelector"


class GrapheneAssetBackfillPreviewParams(graphene.InputObjectType):
    partitionNames = graphene.InputField(non_null_list(graphene.String))
    assetSelection = graphene.InputField(non_null_list(GrapheneAssetKeyInput))

    class Meta:
        name = "AssetBackfillPreviewParams"


class GrapheneLaunchBackfillParams(graphene.InputObjectType):
    selector = graphene.InputField(GraphenePartitionSetSelector)
    partitionNames = graphene.List(graphene.NonNull(graphene.String))
    partitionsByAssets = graphene.List(GraphenePartitionsByAssetSelector)
    reexecutionSteps = graphene.List(graphene.NonNull(graphene.String))
    assetSelection = graphene.InputField(graphene.List(graphene.NonNull(GrapheneAssetKeyInput)))
    fromFailure = graphene.Boolean()
    allPartitions = graphene.Boolean()
    tags = graphene.List(graphene.NonNull(GrapheneExecutionTag))
    forceSynchronousSubmission = graphene.Boolean()
    title = graphene.String()
    description = graphene.String()

    class Meta:
        name = "LaunchBackfillParams"


class GrapheneRunlessAssetEventType(graphene.Enum):
    """The event type of an asset event."""

    ASSET_MATERIALIZATION = "ASSET_MATERIALIZATION"
    ASSET_OBSERVATION = "ASSET_OBSERVATION"

    class Meta:
        name = "AssetEventType"

    def to_dagster_event_type(self) -> DagsterEventType:
        if self == GrapheneRunlessAssetEventType.ASSET_MATERIALIZATION:
            return DagsterEventType.ASSET_MATERIALIZATION
        elif self == GrapheneRunlessAssetEventType.ASSET_OBSERVATION:
            return DagsterEventType.ASSET_OBSERVATION
        else:
            check.assert_never(self)


class GrapheneReportRunlessAssetEventsParams(graphene.InputObjectType):
    eventType = graphene.NonNull(GrapheneRunlessAssetEventType)
    assetKey = graphene.NonNull(GrapheneAssetKeyInput)
    partitionKeys = graphene.InputField(graphene.List(graphene.String))
    description = graphene.String()

    class Meta:
        name = "ReportRunlessAssetEventsParams"


class GrapheneSensorSelector(graphene.InputObjectType):
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)
    sensorName = graphene.NonNull(graphene.String)

    class Meta:
        description = """This type represents the fields necessary to identify a sensor."""
        name = "SensorSelector"


class GrapheneScheduleSelector(graphene.InputObjectType):
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)
    scheduleName = graphene.NonNull(graphene.String)

    class Meta:
        description = """This type represents the fields necessary to identify a schedule."""
        name = "ScheduleSelector"


class GrapheneResourceSelector(graphene.InputObjectType):
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)
    resourceName = graphene.NonNull(graphene.String)

    class Meta:
        description = (
            """This type represents the fields necessary to identify a top-level resource."""
        )
        name = "ResourceSelector"


class GrapheneExecutionMetadata(graphene.InputObjectType):
    tags = graphene.List(graphene.NonNull(GrapheneExecutionTag))
    rootRunId = graphene.String(
        description="""The ID of the run at the root of the run group. All partial /
        full re-executions should use the first run as the rootRunID so they are
        grouped together."""
    )
    parentRunId = graphene.String(
        description="""The ID of the run serving as the parent within the run group.
        For the first re-execution, this will be the same as the `rootRunId`. For
        subsequent runs, the root or a previous re-execution could be the parent run."""
    )

    class Meta:
        name = "ExecutionMetadata"


class GrapheneExecutionParams(graphene.InputObjectType):
    selector = graphene.NonNull(
        GrapheneJobOrPipelineSelector,
        description="""Defines the job / pipeline and solid subset that should be executed.
        All subsequent executions in the same run group (for example, a single-step
        re-execution) are scoped to the original run's selector and solid
        subset.""",
    )
    runConfigData = graphene.InputField(GrapheneRunConfigData)
    mode = graphene.InputField(graphene.String)
    executionMetadata = graphene.InputField(
        GrapheneExecutionMetadata,
        description="""Defines run tags and parent / root relationships.\n\nNote: To
        'restart from failure', provide a `parentRunId` and pass the
        'dagster/is_resume_retry' tag. Dagster's automatic step key selection will
        override any stepKeys provided.""",
    )
    stepKeys = graphene.InputField(
        graphene.List(graphene.NonNull(graphene.String)),
        description="""Defines step keys to execute within the execution plan defined
        by the pipeline `selector`. To execute the entire execution plan, you can omit
        this parameter, provide an empty array, or provide every step name.""",
    )
    preset = graphene.InputField(graphene.String)

    class Meta:
        name = "ExecutionParams"


class GrapheneReexecutionStrategy(graphene.Enum):
    FROM_FAILURE = "FROM_FAILURE"
    ALL_STEPS = "ALL_STEPS"

    class Meta:
        name = "ReexecutionStrategy"


class GrapheneReexecutionParams(graphene.InputObjectType):
    parentRunId = graphene.NonNull(graphene.String)
    strategy = graphene.NonNull(GrapheneReexecutionStrategy)
    extraTags = graphene.List(
        graphene.NonNull(GrapheneExecutionTag),
        description="""When re-executing a single run, pass new tags which will upsert over tags on the parent run.""",
    )
    useParentRunTags = graphene.Boolean(
        description="""When re-executing a single run, pass false to avoid adding the parent run tags by default."""
    )

    class Meta:
        name = "ReexecutionParams"


class GrapheneMarshalledInput(graphene.InputObjectType):
    input_name = graphene.NonNull(graphene.String)
    key = graphene.NonNull(graphene.String)

    class Meta:
        name = "MarshalledInput"


class GrapheneMarshalledOutput(graphene.InputObjectType):
    output_name = graphene.NonNull(graphene.String)
    key = graphene.NonNull(graphene.String)

    class Meta:
        name = "MarshalledOutput"


class GrapheneStepExecution(graphene.InputObjectType):
    stepKey = graphene.NonNull(graphene.String)
    marshalledInputs = graphene.List(graphene.NonNull(GrapheneMarshalledInput))
    marshalledOutputs = graphene.List(graphene.NonNull(GrapheneMarshalledOutput))

    class Meta:
        name = "StepExecution"


class GrapheneInstigationSelector(graphene.InputObjectType):
    class Meta:
        name = "InstigationSelector"
        description = (
            """This type represents the fields necessary to identify a schedule or sensor."""
        )

    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)
    name = graphene.NonNull(graphene.String)


class GrapheneTagInput(graphene.InputObjectType):
    key = graphene.NonNull(graphene.String)
    value = graphene.NonNull(graphene.String)

    class Meta:
        name = "TagInput"


class GrapheneBulkActionsFilter(graphene.InputObjectType):
    statuses = graphene.List(
        graphene.NonNull("dagster_graphql.schema.backfill.GrapheneBulkActionStatus")
    )
    createdBefore = graphene.InputField(graphene.Float)
    createdAfter = graphene.InputField(graphene.Float)

    class Meta:
        description = """This type represents a filter on Dagster Bulk Actions (backfills)."""
        name = "BulkActionsFilter"

    def to_selector(self):
        statuses = (
            [BulkActionStatus[status.value] for status in self.statuses] if self.statuses else None
        )
        created_before = datetime_from_timestamp(self.createdBefore) if self.createdBefore else None
        created_after = datetime_from_timestamp(self.createdAfter) if self.createdAfter else None

        return BulkActionsFilter(
            statuses=statuses,
            created_before=created_before,
            created_after=created_after,
        )


types = [
    GrapheneAssetKeyInput,
    GrapheneExecutionMetadata,
    GrapheneExecutionParams,
    GrapheneExecutionTag,
    GrapheneInstigationSelector,
    GrapheneMarshalledInput,
    GrapheneMarshalledOutput,
    GrapheneLaunchBackfillParams,
    GraphenePartitionSetSelector,
    GraphenePartitionsByAssetSelector,
    GrapheneRunsFilter,
    GraphenePipelineSelector,
    GrapheneRepositorySelector,
    GrapheneResourceSelector,
    GrapheneScheduleSelector,
    GrapheneSensorSelector,
    GrapheneStepExecution,
    GrapheneStepOutputHandle,
    GrapheneTagInput,
    GrapheneReportRunlessAssetEventsParams,
    GrapheneBulkActionsFilter,
]
