from collections.abc import Sequence
from typing import TYPE_CHECKING, AbstractSet, Optional  # noqa: UP035

import dagster._check as check
import graphene
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.time_window_partitions import PartitionRangeStatus
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.event_api import EventLogCursor
from dagster._core.events import DagsterEventType
from dagster._core.remote_representation.external import RemoteExecutionPlan, RemoteJob
from dagster._core.remote_representation.external_data import (
    DEFAULT_MODE_NAME,
    PartitionExecutionErrorSnap,
    PresetSnap,
)
from dagster._core.remote_representation.represented import RepresentedJob
from dagster._core.storage.dagster_run import (
    DagsterRunStatsSnapshot,
    DagsterRunStatus,
    RunRecord,
    RunsFilter,
)
from dagster._core.storage.tags import REPOSITORY_LABEL_TAG, RUN_METRIC_TAGS, TagType, get_tag_type
from dagster._core.workspace.permissions import Permissions
from dagster._utils.tags import get_boolean_tag_value
from dagster_shared.yaml_utils import dump_run_config_yaml

from dagster_graphql.implementation.events import from_event_record, iterate_metadata_entries
from dagster_graphql.implementation.fetch_asset_checks import get_asset_checks_for_run_id
from dagster_graphql.implementation.fetch_assets import get_assets_for_run, get_unique_asset_id
from dagster_graphql.implementation.fetch_pipelines import get_job_reference_or_raise
from dagster_graphql.implementation.fetch_runs import get_runs, get_stats, get_step_stats
from dagster_graphql.implementation.fetch_schedules import get_schedules_for_job
from dagster_graphql.implementation.fetch_sensors import get_sensors_for_job
from dagster_graphql.implementation.utils import (
    UserFacingGraphQLError,
    apply_cursor_limit_reverse,
    capture_error,
)
from dagster_graphql.schema.dagster_types import (
    GrapheneDagsterType,
    GrapheneDagsterTypeOrError,
    GrapheneDagsterTypeUnion,
    to_dagster_type,
)
from dagster_graphql.schema.entity_key import GrapheneAssetCheckHandle, GrapheneAssetKey
from dagster_graphql.schema.errors import (
    GrapheneDagsterTypeNotFoundError,
    GraphenePythonError,
    GrapheneRunNotFoundError,
)
from dagster_graphql.schema.execution import GrapheneExecutionPlan
from dagster_graphql.schema.inputs import GrapheneAssetKeyInput
from dagster_graphql.schema.logs.compute_logs import GrapheneCapturedLogs, from_captured_log_data
from dagster_graphql.schema.logs.events import (
    GrapheneAssetMaterializationEventType,
    GrapheneDagsterRunEvent,
    GrapheneFailedToMaterializeEvent,
    GrapheneMaterializationEvent,
    GrapheneObservationEvent,
    GrapheneRunStepStats,
)
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.partition_keys import GraphenePartitionKeys
from dagster_graphql.schema.pipelines.mode import GrapheneMode
from dagster_graphql.schema.pipelines.pipeline_ref import GraphenePipelineReference
from dagster_graphql.schema.pipelines.pipeline_run_stats import GrapheneRunStatsSnapshotOrError
from dagster_graphql.schema.pipelines.status import GrapheneRunStatus
from dagster_graphql.schema.repository_origin import GrapheneRepositoryOrigin
from dagster_graphql.schema.runs import GrapheneRunConfigData
from dagster_graphql.schema.runs_feed import GrapheneRunsFeedEntry
from dagster_graphql.schema.schedules.schedules import GrapheneSchedule
from dagster_graphql.schema.sensors import GrapheneSensor
from dagster_graphql.schema.solids import (
    GrapheneSolid,
    GrapheneSolidContainer,
    GrapheneSolidHandle,
    build_solid_handles,
    build_solids,
)
from dagster_graphql.schema.tags import GraphenePipelineTag
from dagster_graphql.schema.util import ResolveInfo, get_compute_log_manager, non_null_list

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_graph import GrapheneAssetNode
    from dagster_graphql.schema.partition_sets import GrapheneJobSelectionPartition

UNSTARTED_STATUSES = [
    DagsterRunStatus.QUEUED,
    DagsterRunStatus.NOT_STARTED,
    DagsterRunStatus.STARTING,
]

STARTED_STATUSES = {
    DagsterRunStatus.STARTED,
    DagsterRunStatus.SUCCESS,
    DagsterRunStatus.FAILURE,
    DagsterRunStatus.CANCELED,
}

COMPLETED_STATUSES = {
    DagsterRunStatus.FAILURE,
    DagsterRunStatus.SUCCESS,
    DagsterRunStatus.CANCELED,
}


def parse_timestamp(timestamp: Optional[str] = None) -> Optional[float]:
    try:
        return int(timestamp) / 1000.0 if timestamp else None
    except ValueError:
        return None


GraphenePartitionRangeStatus = graphene.Enum.from_enum(PartitionRangeStatus)


class GrapheneTimePartitionRange(graphene.ObjectType):
    startTime = graphene.NonNull(graphene.Float)
    endTime = graphene.NonNull(graphene.Float)
    startKey = graphene.NonNull(graphene.String)
    endKey = graphene.NonNull(graphene.String)

    class Meta:
        name = "TimePartitionRange"


class GrapheneTimePartitionRangeStatus(GrapheneTimePartitionRange):
    status = graphene.NonNull(GraphenePartitionRangeStatus)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        name = "TimePartitionRangeStatus"


class GrapheneTimePartitionStatuses(graphene.ObjectType):
    ranges = non_null_list(GrapheneTimePartitionRangeStatus)

    class Meta:
        name = "TimePartitionStatuses"


class GrapheneDefaultPartitionStatuses(graphene.ObjectType):
    materializedPartitions = non_null_list(graphene.String)
    failedPartitions = non_null_list(graphene.String)
    unmaterializedPartitions = non_null_list(graphene.String)
    materializingPartitions = non_null_list(graphene.String)

    class Meta:
        name = "DefaultPartitionStatuses"


class GraphenePartitionStatus1D(graphene.Union):
    class Meta:
        types = (GrapheneTimePartitionStatuses, GrapheneDefaultPartitionStatuses)
        name = "PartitionStatus1D"


class GrapheneMultiPartitionRangeStatuses(graphene.ObjectType):
    """The primary dimension of a multipartitioned asset is the time-partitioned dimension.
    If both dimensions of the asset are static or time-partitioned, the primary dimension is
    the first defined dimension.
    """

    primaryDimStartKey = graphene.NonNull(graphene.String)
    primaryDimEndKey = graphene.NonNull(graphene.String)
    primaryDimStartTime = graphene.Field(graphene.Float)
    primaryDimEndTime = graphene.Field(graphene.Float)
    secondaryDim = graphene.NonNull(GraphenePartitionStatus1D)

    class Meta:
        name = "MaterializedPartitionRangeStatuses2D"


class GrapheneMultiPartitionStatuses(graphene.ObjectType):
    ranges = non_null_list(GrapheneMultiPartitionRangeStatuses)
    primaryDimensionName = graphene.NonNull(graphene.String)

    class Meta:
        name = "MultiPartitionStatuses"


class GrapheneAssetPartitionStatuses(graphene.Union):
    class Meta:
        types = (
            GrapheneDefaultPartitionStatuses,
            GrapheneMultiPartitionStatuses,
            GrapheneTimePartitionStatuses,
        )
        name = "AssetPartitionStatuses"


class GraphenePartitionStats(graphene.ObjectType):
    numMaterialized = graphene.NonNull(graphene.Int)
    numPartitions = graphene.NonNull(graphene.Int)
    numFailed = graphene.NonNull(graphene.Int)
    numMaterializing = graphene.NonNull(graphene.Int)

    class Meta:
        name = "PartitionStats"


class GrapheneMaterializationHistoryEventTypeSelector(graphene.Enum):
    MATERIALIZATION = "MATERIALIZATION"
    FAILED_TO_MATERIALIZE = "FAILED_TO_MATERIALIZE"
    ALL = "ALL"

    class Meta:
        name = "MaterializationHistoryEventTypeSelector"


class GrapheneMaterializationHistoryConnection(graphene.ObjectType):
    class Meta:
        name = "MaterializationHistoryConnection"

    results = non_null_list(GrapheneAssetMaterializationEventType)
    cursor = graphene.NonNull(graphene.String)


class GrapheneAsset(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    key = graphene.NonNull(GrapheneAssetKey)
    assetMaterializations = graphene.Field(
        non_null_list(GrapheneMaterializationEvent),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
        partitionInLast=graphene.Int(),
        beforeTimestampMillis=graphene.String(),
        afterTimestampMillis=graphene.String(),
        limit=graphene.Int(),
    )
    assetObservations = graphene.Field(
        non_null_list(GrapheneObservationEvent),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
        partitionInLast=graphene.Int(),
        beforeTimestampMillis=graphene.String(),
        afterTimestampMillis=graphene.String(),
        limit=graphene.Int(),
    )
    assetMaterializationHistory = graphene.Field(
        graphene.NonNull(GrapheneMaterializationHistoryConnection),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
        partitionInLast=graphene.Int(),
        beforeTimestampMillis=graphene.String(),
        afterTimestampMillis=graphene.String(),
        limit=graphene.Int(),
        eventTypeSelector=graphene.Argument(GrapheneMaterializationHistoryEventTypeSelector),
        cursor=graphene.String(),
    )
    definition = graphene.Field("dagster_graphql.schema.asset_graph.GrapheneAssetNode")

    class Meta:
        name = "Asset"

    def __init__(self, key, definition: Optional["GrapheneAssetNode"] = None):
        super().__init__(key=key, definition=definition)
        self._definition = definition

    def resolve_id(self, _) -> str:
        # If the asset is not a SDA asset (has no definition), the id is the asset key
        # Else, return a unique identifier containing the repository location and name
        if self._definition:
            return self._definition.id
        return get_unique_asset_id(self.key)

    def resolve_assetMaterializations(
        self,
        graphene_info: ResolveInfo,
        partitions: Optional[Sequence[str]] = None,
        partitionInLast: Optional[int] = None,
        beforeTimestampMillis: Optional[str] = None,
        afterTimestampMillis: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[GrapheneMaterializationEvent]:
        from dagster_graphql.implementation.fetch_assets import get_asset_materializations

        before_timestamp = parse_timestamp(beforeTimestampMillis)
        after_timestamp = parse_timestamp(afterTimestampMillis)
        if partitionInLast and self._definition:
            partitions = self._definition.get_partition_keys()[-int(partitionInLast) :]

        events = get_asset_materializations(
            graphene_info,
            self.key,
            partitions=partitions,
            before_timestamp=before_timestamp,
            after_timestamp=after_timestamp,
            limit=limit,
        )
        return [GrapheneMaterializationEvent(event=event) for event in events]

    def resolve_assetMaterializationHistory(
        self,
        graphene_info: ResolveInfo,
        eventTypeSelector: Optional[GrapheneMaterializationHistoryEventTypeSelector] = None,
        partitions: Optional[Sequence[str]] = None,
        partitionInLast: Optional[int] = None,
        beforeTimestampMillis: Optional[str] = None,
        afterTimestampMillis: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence[GrapheneMaterializationHistoryConnection]:
        from dagster_graphql.implementation.fetch_assets import (
            get_asset_failed_to_materialize_event_records,
            get_asset_materialization_event_records,
        )

        eventTypeSelector = eventTypeSelector or GrapheneMaterializationHistoryEventTypeSelector.ALL

        before_timestamp = parse_timestamp(beforeTimestampMillis)
        after_timestamp = parse_timestamp(afterTimestampMillis)
        if partitionInLast and self._definition:
            partitions = self._definition.get_partition_keys()[-int(partitionInLast) :]

        failure_events = []
        success_events = []
        if (
            eventTypeSelector
            == GrapheneMaterializationHistoryEventTypeSelector.FAILED_TO_MATERIALIZE
            or eventTypeSelector == GrapheneMaterializationHistoryEventTypeSelector.ALL
        ):
            failure_events = [
                (record.storage_id, GrapheneFailedToMaterializeEvent(event=record.event_log_entry))
                for record in get_asset_failed_to_materialize_event_records(
                    graphene_info,
                    self.key,
                    partitions=partitions,
                    before_timestamp=before_timestamp,
                    after_timestamp=after_timestamp,
                    limit=limit,
                    cursor=cursor,
                )
            ]
        if (
            eventTypeSelector == GrapheneMaterializationHistoryEventTypeSelector.MATERIALIZATION
            or eventTypeSelector == GrapheneMaterializationHistoryEventTypeSelector.ALL
        ):
            success_events = [
                (record.storage_id, GrapheneMaterializationEvent(event=record.event_log_entry))
                for record in get_asset_materialization_event_records(
                    graphene_info,
                    self.key,
                    partitions=partitions,
                    before_timestamp=before_timestamp,
                    after_timestamp=after_timestamp,
                    limit=limit,
                    cursor=cursor,
                )
            ]

        combined = failure_events + success_events
        sorted_combined = sorted(combined, key=lambda event_tuple: event_tuple[0], reverse=True)[
            :limit
        ]
        new_cursor = (
            EventLogCursor.from_storage_id(sorted_combined[-1][0]).to_string()
            if sorted_combined
            else None
        )
        return GrapheneMaterializationHistoryConnection(
            results=[event_tuple[1] for event_tuple in sorted_combined],
            cursor=new_cursor,
        )

    def resolve_assetObservations(
        self,
        graphene_info: ResolveInfo,
        partitions: Optional[Sequence[str]] = None,
        partitionInLast: Optional[int] = None,
        beforeTimestampMillis: Optional[str] = None,
        afterTimestampMillis: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[GrapheneObservationEvent]:
        from dagster_graphql.implementation.fetch_assets import get_asset_observations

        before_timestamp = parse_timestamp(beforeTimestampMillis)
        after_timestamp = parse_timestamp(afterTimestampMillis)
        if partitionInLast and self._definition:
            partitions = self._definition.get_partition_keys()[-int(partitionInLast) :]

        return [
            GrapheneObservationEvent(event=event)
            for event in get_asset_observations(
                graphene_info,
                self.key,
                partitions=partitions,
                before_timestamp=before_timestamp,
                after_timestamp=after_timestamp,
                limit=limit,
            )
        ]


class GrapheneEventConnection(graphene.ObjectType):
    class Meta:
        name = "EventConnection"

    events = non_null_list(GrapheneDagsterRunEvent)
    cursor = graphene.NonNull(graphene.String)
    hasMore = graphene.NonNull(graphene.Boolean)


class GrapheneEventConnectionOrError(graphene.Union):
    class Meta:
        types = (GrapheneEventConnection, GrapheneRunNotFoundError, GraphenePythonError)
        name = "EventConnectionOrError"


class GraphenePipelineRun(graphene.Interface):
    id = graphene.NonNull(graphene.ID)
    runId = graphene.NonNull(graphene.String)
    # Nullable because of historical runs
    pipelineSnapshotId = graphene.String()
    repositoryOrigin = graphene.Field(GrapheneRepositoryOrigin)
    status = graphene.NonNull(GrapheneRunStatus)
    pipeline = graphene.NonNull(GraphenePipelineReference)
    pipelineName = graphene.NonNull(graphene.String)
    jobName = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))
    stats = graphene.NonNull(GrapheneRunStatsSnapshotOrError)
    stepStats = non_null_list(GrapheneRunStepStats)
    capturedLogs = graphene.Field(
        graphene.NonNull(GrapheneCapturedLogs),
        fileKey=graphene.Argument(graphene.NonNull(graphene.String)),
        description="""
        Captured logs are the stdout/stderr logs for a given file key within the run
        """,
    )
    executionPlan = graphene.Field(GrapheneExecutionPlan)
    stepKeysToExecute = graphene.List(graphene.NonNull(graphene.String))
    runConfigYaml = graphene.NonNull(graphene.String)
    runConfig = graphene.NonNull(GrapheneRunConfigData)
    mode = graphene.NonNull(graphene.String)
    tags = non_null_list(GraphenePipelineTag)
    rootRunId = graphene.Field(graphene.String)
    parentRunId = graphene.Field(graphene.String)
    canTerminate = graphene.NonNull(graphene.Boolean)
    assets = non_null_list(GrapheneAsset)
    eventConnection = graphene.Field(
        graphene.NonNull(GrapheneEventConnection),
        afterCursor=graphene.Argument(graphene.String),
        limit=graphene.Argument(graphene.Int),
    )

    class Meta:
        name = "PipelineRun"


class GrapheneRun(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    runId = graphene.NonNull(graphene.String)
    # Nullable because of historical runs
    pipelineSnapshotId = graphene.String()
    parentPipelineSnapshotId = graphene.String()
    repositoryOrigin = graphene.Field(GrapheneRepositoryOrigin)
    status = graphene.NonNull(GrapheneRunStatus)
    runStatus = graphene.Field(
        graphene.NonNull(GrapheneRunStatus),
        description="Included to comply with RunsFeedEntry interface. Duplicate of status.",
    )
    pipeline = graphene.NonNull(GraphenePipelineReference)
    pipelineName = graphene.NonNull(graphene.String)
    jobName = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))
    assetSelection = graphene.List(graphene.NonNull(GrapheneAssetKey))
    assetCheckSelection = graphene.List(graphene.NonNull(GrapheneAssetCheckHandle))
    resolvedOpSelection = graphene.List(graphene.NonNull(graphene.String))
    stats = graphene.NonNull(GrapheneRunStatsSnapshotOrError)
    stepStats = non_null_list(GrapheneRunStepStats)
    executionPlan = graphene.Field(GrapheneExecutionPlan)
    stepKeysToExecute = graphene.List(graphene.NonNull(graphene.String))
    runConfigYaml = graphene.NonNull(graphene.String)
    runConfig = graphene.NonNull(GrapheneRunConfigData)
    mode = graphene.NonNull(graphene.String)
    tags = non_null_list(GraphenePipelineTag)
    rootRunId = graphene.Field(graphene.String)
    parentRunId = graphene.Field(graphene.String)
    canTerminate = graphene.NonNull(graphene.Boolean)
    assetMaterializations = non_null_list(GrapheneMaterializationEvent)
    assets = non_null_list(GrapheneAsset)
    assetChecks = graphene.List(graphene.NonNull(GrapheneAssetCheckHandle))
    eventConnection = graphene.Field(
        graphene.NonNull(GrapheneEventConnection),
        afterCursor=graphene.Argument(graphene.String),
        limit=graphene.Argument(graphene.Int),
    )
    creationTime = graphene.NonNull(graphene.Float)
    startTime = graphene.Float()
    endTime = graphene.Float()
    updateTime = graphene.Float()
    hasReExecutePermission = graphene.NonNull(graphene.Boolean)
    hasTerminatePermission = graphene.NonNull(graphene.Boolean)
    hasDeletePermission = graphene.NonNull(graphene.Boolean)
    hasConcurrencyKeySlots = graphene.NonNull(graphene.Boolean)
    rootConcurrencyKeys = graphene.List(graphene.NonNull(graphene.String))
    allPools = graphene.List(graphene.NonNull(graphene.String))
    hasUnconstrainedRootNodes = graphene.NonNull(graphene.Boolean)
    hasRunMetricsEnabled = graphene.NonNull(graphene.Boolean)

    class Meta:
        interfaces = (GraphenePipelineRun, GrapheneRunsFeedEntry)
        name = "Run"

    def __init__(self, record: RunRecord):
        check.inst_param(record, "record", RunRecord)
        dagster_run = record.dagster_run
        super().__init__(
            runId=dagster_run.run_id,
            status=dagster_run.status.value,
            runStatus=dagster_run.status.value,
            mode=DEFAULT_MODE_NAME,
        )
        self.dagster_run = dagster_run
        self._run_record = record
        self._run_stats: Optional[DagsterRunStatsSnapshot] = None

    def _get_permission_value(self, permission: Permissions, graphene_info: ResolveInfo) -> bool:
        location_name = (
            self.dagster_run.remote_job_origin.location_name
            if self.dagster_run.remote_job_origin
            else None
        )

        return (
            graphene_info.context.has_permission_for_location(permission, location_name)
            if location_name
            else graphene_info.context.has_permission(permission)
        )

    @property
    def creation_timestamp(self) -> float:
        return self._run_record.create_timestamp.timestamp()

    def resolve_hasReExecutePermission(self, graphene_info: ResolveInfo):
        return self._get_permission_value(Permissions.LAUNCH_PIPELINE_REEXECUTION, graphene_info)

    def resolve_hasTerminatePermission(self, graphene_info: ResolveInfo):
        return self._get_permission_value(Permissions.TERMINATE_PIPELINE_EXECUTION, graphene_info)

    def resolve_hasDeletePermission(self, graphene_info: ResolveInfo):
        return self._get_permission_value(Permissions.DELETE_PIPELINE_RUN, graphene_info)

    def resolve_id(self, _graphene_info: ResolveInfo):
        return self.dagster_run.run_id

    def resolve_repositoryOrigin(self, _graphene_info: ResolveInfo):
        return (
            GrapheneRepositoryOrigin(self.dagster_run.remote_job_origin.repository_origin)
            if self.dagster_run.remote_job_origin
            else None
        )

    def resolve_pipeline(self, graphene_info: ResolveInfo):
        return get_job_reference_or_raise(graphene_info, self.dagster_run)

    def resolve_pipelineName(self, _graphene_info: ResolveInfo):
        return self.dagster_run.job_name

    def resolve_jobName(self, _graphene_info: ResolveInfo):
        return self.dagster_run.job_name

    def resolve_solidSelection(self, _graphene_info: ResolveInfo):
        return self.dagster_run.op_selection

    def resolve_assetSelection(self, _graphene_info: ResolveInfo):
        return self.dagster_run.asset_selection

    def resolve_assetCheckSelection(self, _graphene_info: ResolveInfo):
        return (
            [GrapheneAssetCheckHandle(handle) for handle in self.dagster_run.asset_check_selection]
            if self.dagster_run.asset_check_selection is not None
            else None
        )

    def resolve_resolvedOpSelection(self, _graphene_info: ResolveInfo):
        return self.dagster_run.resolved_op_selection

    def resolve_pipelineSnapshotId(self, _graphene_info: ResolveInfo):
        return self.dagster_run.job_snapshot_id

    def resolve_parentPipelineSnapshotId(self, graphene_info: ResolveInfo):
        pipeline_snapshot_id = self.dagster_run.job_snapshot_id
        if pipeline_snapshot_id is not None and graphene_info.context.instance.has_job_snapshot(
            pipeline_snapshot_id
        ):
            snapshot = graphene_info.context.instance.get_job_snapshot(pipeline_snapshot_id)
            if snapshot.lineage_snapshot is not None:
                return snapshot.lineage_snapshot.parent_snapshot_id
        return None

    @capture_error
    def resolve_stats(self, graphene_info: ResolveInfo):
        return get_stats(graphene_info, self.run_id)

    def resolve_stepStats(self, graphene_info: ResolveInfo):
        return get_step_stats(graphene_info, self.run_id)

    def resolve_capturedLogs(self, graphene_info: ResolveInfo, fileKey):
        compute_log_manager = get_compute_log_manager(graphene_info)
        log_key = compute_log_manager.build_log_key_for_run(self.run_id, fileKey)
        log_data = compute_log_manager.get_log_data(log_key)
        return from_captured_log_data(log_data)

    def resolve_executionPlan(self, graphene_info: ResolveInfo):
        if not (self.dagster_run.execution_plan_snapshot_id and self.dagster_run.job_snapshot_id):
            return None

        instance = graphene_info.context.instance

        execution_plan_snapshot = instance.get_execution_plan_snapshot(
            self.dagster_run.execution_plan_snapshot_id
        )
        return (
            GrapheneExecutionPlan(
                RemoteExecutionPlan(execution_plan_snapshot=execution_plan_snapshot)
            )
            if execution_plan_snapshot
            else None
        )

    def resolve_stepKeysToExecute(self, _graphene_info: ResolveInfo):
        return self.dagster_run.step_keys_to_execute

    def resolve_runConfigYaml(self, _graphene_info: ResolveInfo):
        return dump_run_config_yaml(self.dagster_run.run_config)

    def resolve_runConfig(self, _graphene_info: ResolveInfo):
        return self.dagster_run.run_config

    def resolve_tags(self, _graphene_info: ResolveInfo):
        return [
            GraphenePipelineTag(key=key, value=value)
            for key, value in self.dagster_run.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]

    def resolve_rootRunId(self, _graphene_info: ResolveInfo):
        return self.dagster_run.root_run_id

    def resolve_parentRunId(self, _graphene_info: ResolveInfo):
        return self.dagster_run.parent_run_id

    @property
    def run_id(self):
        return self.runId

    def resolve_canTerminate(self, _graphene_info: ResolveInfo):
        # short circuit if the pipeline run is in a terminal state
        if self.dagster_run.is_finished:
            return False
        return (
            self.dagster_run.status == DagsterRunStatus.QUEUED
            or self.dagster_run.status == DagsterRunStatus.STARTED
        )

    def resolve_assets(self, graphene_info: ResolveInfo):
        return get_assets_for_run(graphene_info, self.dagster_run)

    def resolve_assetChecks(self, graphene_info: ResolveInfo):
        return get_asset_checks_for_run_id(graphene_info, self.run_id)

    def resolve_assetMaterializations(self, graphene_info: ResolveInfo):
        # convenience field added for users querying directly via GraphQL
        return [
            GrapheneMaterializationEvent(event=event)
            for event in graphene_info.context.instance.all_logs(
                self.run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION
            )
        ]

    def resolve_eventConnection(self, graphene_info: ResolveInfo, afterCursor=None, limit=None):
        conn = graphene_info.context.instance.get_records_for_run(
            self.run_id, cursor=afterCursor, limit=limit
        )
        return GrapheneEventConnection(
            events=[
                from_event_record(record.event_log_entry, self.dagster_run.job_name)
                for record in conn.records
            ],
            cursor=conn.cursor,
            hasMore=conn.has_more,
        )

    def resolve_startTime(self, graphene_info: ResolveInfo):
        # If a user has not migrated in 0.13.15, then run_record will not have start_time and end_time. So it will be necessary to fill this data using the run_stats. Since we potentially make this call multiple times, we cache the result.
        if self._run_record.start_time is None and self.dagster_run.status in STARTED_STATUSES:
            # Short-circuit if pipeline failed to start, so it has an end time but no start time
            if self._run_record.end_time is not None:
                return self._run_record.end_time

            if self._run_stats is None or self._run_stats.start_time is None:
                self._run_stats = graphene_info.context.instance.get_run_stats(self.runId)

            if self._run_stats.start_time is None and self._run_stats.end_time:
                return self._run_stats.end_time

            return self._run_stats.start_time
        return self._run_record.start_time

    def resolve_endTime(self, graphene_info: ResolveInfo):
        if self._run_record.end_time is None and self.dagster_run.status in COMPLETED_STATUSES:
            if self._run_stats is None or self._run_stats.end_time is None:
                self._run_stats = graphene_info.context.instance.get_run_stats(self.runId)
            return self._run_stats.end_time
        return self._run_record.end_time

    def resolve_updateTime(self, graphene_info: ResolveInfo):
        return self._run_record.update_timestamp.timestamp()

    def resolve_creationTime(self, graphene_info: ResolveInfo):
        return self.creation_timestamp

    def resolve_hasConcurrencyKeySlots(self, graphene_info: ResolveInfo):
        instance = graphene_info.context.instance
        if not instance.event_log_storage.supports_global_concurrency_limits:
            return False

        active_run_ids = instance.event_log_storage.get_concurrency_run_ids()
        return self.runId in active_run_ids

    def resolve_hasUnconstrainedRootNodes(self, graphene_info: ResolveInfo):
        if not self.dagster_run.run_op_concurrency:
            return True

        if self.dagster_run.run_op_concurrency.has_unconstrained_root_nodes:
            return True

        return False

    def resolve_allPools(self, graphene_info: ResolveInfo):
        if not self.dagster_run.run_op_concurrency:
            return None

        return (
            list(self.dagster_run.run_op_concurrency.all_pools)
            if self.dagster_run.run_op_concurrency.all_pools
            else []
        )

    def resolve_rootConcurrencyKeys(self, graphene_info: ResolveInfo):
        if not self.dagster_run.run_op_concurrency:
            return None

        root_concurrency_keys = []
        for concurrency_key, count in self.dagster_run.run_op_concurrency.root_key_counts.items():
            root_concurrency_keys.extend([concurrency_key] * count)
        return root_concurrency_keys

    def resolve_hasRunMetricsEnabled(self, graphene_info: ResolveInfo):
        if self.dagster_run.status in UNSTARTED_STATUSES:
            return False

        run_tags = self.dagster_run.tags
        return any(get_boolean_tag_value(run_tags.get(tag)) for tag in RUN_METRIC_TAGS)


class GrapheneIPipelineSnapshotMixin:
    # Mixin this class to implement IPipelineSnapshot
    #
    # Graphene has some strange properties that make it so that you cannot
    # implement ABCs nor use properties in an overridable way. So the way
    # the mixin works is that the target classes have to have a method
    # get_represented_job()
    #
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    id = graphene.NonNull(graphene.ID)
    pipeline_snapshot_id = graphene.NonNull(graphene.String)
    dagster_types = non_null_list(GrapheneDagsterType)
    dagster_type_or_error = graphene.Field(
        graphene.NonNull(GrapheneDagsterTypeOrError),
        dagsterTypeName=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    solids = non_null_list(GrapheneSolid)
    modes = non_null_list(GrapheneMode)
    solid_handles = graphene.Field(
        non_null_list(GrapheneSolidHandle), parentHandleID=graphene.String()
    )
    solid_handle = graphene.Field(
        GrapheneSolidHandle,
        handleID=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    tags = non_null_list(GraphenePipelineTag)
    run_tags = non_null_list(GraphenePipelineTag)
    metadata_entries = non_null_list(GrapheneMetadataEntry)
    runs = graphene.Field(
        non_null_list(GrapheneRun),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )
    schedules = non_null_list(GrapheneSchedule)
    sensors = non_null_list(GrapheneSensor)
    parent_snapshot_id = graphene.String()
    graph_name = graphene.NonNull(graphene.String)

    class Meta:
        name = "IPipelineSnapshotMixin"

    def get_represented_job(self) -> RepresentedJob:
        raise NotImplementedError()

    def resolve_pipeline_snapshot_id(self, _graphene_info: ResolveInfo):
        return self.get_represented_job().identifying_job_snapshot_id

    def resolve_id(self, _graphene_info: ResolveInfo):
        return self.get_represented_job().identifying_job_snapshot_id

    def resolve_name(self, _graphene_info: ResolveInfo):
        return self.get_represented_job().name

    def resolve_description(self, _graphene_info: ResolveInfo):
        return self.get_represented_job().description

    def resolve_dagster_types(self, _graphene_info: ResolveInfo):
        represented_pipeline = self.get_represented_job()
        return sorted(
            list(
                map(
                    lambda dt: to_dagster_type(
                        represented_pipeline.job_snapshot.dagster_type_namespace_snapshot.get_dagster_type_snap,
                        represented_pipeline.job_snapshot.config_schema_snapshot.get_config_snap,
                        dt.key,
                    ),
                    [t for t in represented_pipeline.dagster_type_snaps if t.name],
                )
            ),
            key=lambda dagster_type: dagster_type.name,
        )

    @capture_error
    def resolve_dagster_type_or_error(
        self, _graphene_info: ResolveInfo, dagsterTypeName: str
    ) -> GrapheneDagsterTypeUnion:
        represented_pipeline = self.get_represented_job()

        if not represented_pipeline.has_dagster_type_named(dagsterTypeName):
            raise UserFacingGraphQLError(
                GrapheneDagsterTypeNotFoundError(dagster_type_name=dagsterTypeName)
            )

        return to_dagster_type(
            represented_pipeline.job_snapshot.dagster_type_namespace_snapshot.get_dagster_type_snap,
            represented_pipeline.job_snapshot.config_schema_snapshot.get_config_snap,
            represented_pipeline.get_dagster_type_by_name(dagsterTypeName).key,
        )

    def resolve_solids(self, _graphene_info: ResolveInfo):
        represented_pipeline = self.get_represented_job()
        return build_solids(
            represented_pipeline,
            represented_pipeline.dep_structure_index,
        )

    def resolve_modes(self, graphene_info: ResolveInfo):
        represented_pipeline = self.get_represented_job()
        return [
            GrapheneMode(
                represented_pipeline.config_schema_snapshot.get_config_snap,
                self.resolve_id(graphene_info),
                mode_def_snap,
            )
            for mode_def_snap in sorted(
                represented_pipeline.mode_def_snaps, key=lambda item: item.name
            )
        ]

    def resolve_solid_handle(
        self, _graphene_info: ResolveInfo, handleID: str
    ) -> Optional[GrapheneSolidHandle]:
        return build_solid_handles(self.get_represented_job()).get(handleID)

    def resolve_solid_handles(
        self, _graphene_info: ResolveInfo, parentHandleID: Optional[str] = None
    ) -> Sequence[GrapheneSolidHandle]:
        handles = build_solid_handles(self.get_represented_job())

        if parentHandleID == "":
            handles = {key: handle for key, handle in handles.items() if not handle.parent}
        elif parentHandleID is not None:
            handles = {
                key: handle
                for key, handle in handles.items()
                if handle.parent and str(handle.parent.handleID) == parentHandleID
            }

        return [handles[key] for key in sorted(handles)]

    def resolve_tags(self, _graphene_info: ResolveInfo):
        represented_pipeline = self.get_represented_job()
        return [
            GraphenePipelineTag(key=key, value=value)
            for key, value in represented_pipeline.job_snapshot.tags.items()
        ]

    def resolve_run_tags(self, _graphene_info: ResolveInfo):
        represented_pipeline = self.get_represented_job()
        return [
            GraphenePipelineTag(key=key, value=value)
            for key, value in (represented_pipeline.job_snapshot.run_tags or {}).items()
        ]

    def resolve_metadata_entries(self, _graphene_info: ResolveInfo) -> list[GrapheneMetadataEntry]:
        represented_pipeline = self.get_represented_job()
        return list(iterate_metadata_entries(represented_pipeline.job_snapshot.metadata))

    def resolve_solidSelection(self, _graphene_info: ResolveInfo):
        return self.get_represented_job().op_selection

    def resolve_runs(
        self, graphene_info: ResolveInfo, cursor: Optional[str] = None, limit: Optional[int] = None
    ) -> Sequence[GrapheneRun]:
        pipeline = self.get_represented_job()
        if isinstance(pipeline, RemoteJob):
            runs_filter = RunsFilter(
                job_name=pipeline.name,
                tags={
                    REPOSITORY_LABEL_TAG: (
                        pipeline.get_remote_origin().repository_origin.get_label()
                    )
                },
            )
        else:
            runs_filter = RunsFilter(job_name=pipeline.name)
        return get_runs(graphene_info, runs_filter, cursor, limit)

    def resolve_schedules(self, graphene_info: ResolveInfo):
        represented_pipeline = self.get_represented_job()
        if not isinstance(represented_pipeline, RemoteJob):
            # this is an historical pipeline snapshot, so there are not any associated running
            # schedules
            return []

        pipeline_selector = represented_pipeline.handle.to_selector()
        schedules = get_schedules_for_job(graphene_info, pipeline_selector)
        return schedules

    def resolve_sensors(self, graphene_info: ResolveInfo):
        represented_pipeline = self.get_represented_job()
        if not isinstance(represented_pipeline, RemoteJob):
            # this is an historical pipeline snapshot, so there are not any associated running
            # sensors
            return []

        pipeline_selector = represented_pipeline.handle.to_selector()
        sensors = get_sensors_for_job(graphene_info, pipeline_selector)
        return sensors

    def resolve_parent_snapshot_id(self, _graphene_info: ResolveInfo):
        lineage_snapshot = self.get_represented_job().job_snapshot.lineage_snapshot
        if lineage_snapshot:
            return lineage_snapshot.parent_snapshot_id
        else:
            return None

    def resolve_graph_name(self, _graphene_info: ResolveInfo):
        return self.get_represented_job().get_graph_name()


class GrapheneIPipelineSnapshot(graphene.Interface):
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    pipeline_snapshot_id = graphene.NonNull(graphene.String)
    dagster_types = non_null_list(GrapheneDagsterType)
    dagster_type_or_error = graphene.Field(
        graphene.NonNull(GrapheneDagsterTypeOrError),
        dagsterTypeName=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    solids = non_null_list(GrapheneSolid)
    modes = non_null_list(GrapheneMode)
    solid_handles = graphene.Field(
        non_null_list(GrapheneSolidHandle), parentHandleID=graphene.String()
    )
    solid_handle = graphene.Field(
        GrapheneSolidHandle,
        handleID=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    tags = non_null_list(GraphenePipelineTag)
    metadata_entries = non_null_list(GrapheneMetadataEntry)
    runs = graphene.Field(
        non_null_list(GrapheneRun),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )
    schedules = non_null_list(GrapheneSchedule)
    sensors = non_null_list(GrapheneSensor)
    parent_snapshot_id = graphene.String()
    graph_name = graphene.NonNull(graphene.String)

    class Meta:
        name = "IPipelineSnapshot"


class GraphenePipelinePreset(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    solidSelection = graphene.List(graphene.NonNull(graphene.String))
    runConfigYaml = graphene.NonNull(graphene.String)
    mode = graphene.NonNull(graphene.String)
    tags = non_null_list(GraphenePipelineTag)

    class Meta:
        name = "PipelinePreset"

    def __init__(self, active_preset_data, pipeline_name):
        super().__init__()
        self._active_preset_data = check.inst_param(
            active_preset_data, "active_preset_data", PresetSnap
        )
        self._job_name = check.str_param(pipeline_name, "pipeline_name")

    def resolve_name(self, _graphene_info: ResolveInfo):
        return self._active_preset_data.name

    def resolve_solidSelection(self, _graphene_info: ResolveInfo):
        return self._active_preset_data.op_selection

    def resolve_runConfigYaml(self, _graphene_info: ResolveInfo):
        return dump_run_config_yaml(self._active_preset_data.run_config) or ""

    def resolve_mode(self, _graphene_info: ResolveInfo):
        return self._active_preset_data.mode

    def resolve_tags(self, _graphene_info: ResolveInfo):
        return [
            GraphenePipelineTag(key=key, value=value)
            for key, value in self._active_preset_data.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]


class GraphenePipeline(GrapheneIPipelineSnapshotMixin, graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    presets = non_null_list(GraphenePipelinePreset)
    isJob = graphene.NonNull(graphene.Boolean)
    isAssetJob = graphene.NonNull(graphene.Boolean)
    repository = graphene.NonNull("dagster_graphql.schema.external.GrapheneRepository")
    partitionKeysOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionKeys),
        cursor=graphene.String(),
        limit=graphene.Int(),
        reverse=graphene.Boolean(),
        selected_asset_keys=graphene.Argument(
            graphene.List(graphene.NonNull(GrapheneAssetKeyInput))
        ),
    )
    partition = graphene.Field(
        "dagster_graphql.schema.partition_sets.GrapheneJobSelectionPartition",
        partition_name=graphene.NonNull(graphene.String),
        selected_asset_keys=graphene.Argument(
            graphene.List(graphene.NonNull(GrapheneAssetKeyInput))
        ),
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        interfaces = (GrapheneSolidContainer, GrapheneIPipelineSnapshot)
        name = "Pipeline"

    def __init__(self, remote_job: RemoteJob):
        super().__init__()
        self._remote_job = check.inst_param(remote_job, "remote_job", RemoteJob)

    def resolve_id(self, _graphene_info: ResolveInfo):
        return self._remote_job.get_remote_origin_id()

    def get_represented_job(self) -> RepresentedJob:
        return self._remote_job

    def resolve_presets(self, _graphene_info: ResolveInfo):
        return [
            GraphenePipelinePreset(preset, self._remote_job.name)
            for preset in sorted(self._remote_job.active_presets, key=lambda item: item.name)
        ]

    def resolve_isJob(self, _graphene_info: ResolveInfo):
        return True

    def resolve_isAssetJob(self, graphene_info: ResolveInfo):
        handle = self._remote_job.repository_handle
        location = graphene_info.context.get_code_location(handle.location_name)
        repository = location.get_repository(handle.repository_name)
        return bool(repository.get_asset_node_snaps(self._remote_job.name))

    def resolve_repository(self, graphene_info: ResolveInfo):
        from dagster_graphql.schema.external import GrapheneRepository

        return GrapheneRepository(self._remote_job.repository_handle)

    def resolve_partitionKeysOrError(
        self,
        graphene_info: ResolveInfo,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        reverse: Optional[bool] = None,
        selected_asset_keys: Optional[list[GrapheneAssetKeyInput]] = None,
    ) -> GraphenePartitionKeys:
        result = graphene_info.context.get_partition_names(
            repository_handle=self._remote_job.repository_handle,
            job_name=self._remote_job.name,
            selected_asset_keys=_asset_key_input_list_to_asset_key_set(selected_asset_keys),
            instance=graphene_info.context.instance,
        )

        if isinstance(result, PartitionExecutionErrorSnap):
            raise DagsterUserCodeProcessError.from_error_info(result.error)

        all_partition_keys = result.partition_names

        return GraphenePartitionKeys(
            partitionKeys=apply_cursor_limit_reverse(
                all_partition_keys, cursor=cursor, limit=limit, reverse=reverse or False
            )
        )

    def resolve_partition(
        self,
        graphene_info: ResolveInfo,
        partition_name: str,
        selected_asset_keys: Optional[list[GrapheneAssetKeyInput]] = None,
    ) -> "GrapheneJobSelectionPartition":
        from dagster_graphql.schema.partition_sets import GrapheneJobSelectionPartition

        return GrapheneJobSelectionPartition(
            remote_job=self._remote_job,
            partition_name=partition_name,
            selected_asset_keys=_asset_key_input_list_to_asset_key_set(selected_asset_keys),
        )


class GrapheneJob(GraphenePipeline):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        interfaces = (GrapheneSolidContainer, GrapheneIPipelineSnapshot)
        name = "Job"

    # doesn't inherit from base class
    def __init__(self, remote_job):
        super().__init__()  # pyright: ignore[reportCallIssue]
        self._remote_job = check.inst_param(remote_job, "remote_job", RemoteJob)


class GrapheneGraph(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneSolidContainer,)
        name = "Graph"

    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    description = graphene.String()
    solid_handle = graphene.Field(
        GrapheneSolidHandle,
        handleID=graphene.Argument(graphene.NonNull(graphene.String)),
    )
    solid_handles = graphene.Field(
        non_null_list(GrapheneSolidHandle), parentHandleID=graphene.String()
    )
    modes = non_null_list(GrapheneMode)

    def __init__(self, remote_job: RemoteJob, solid_handle_id=None):
        self._remote_job = check.inst_param(remote_job, "remote_job", RemoteJob)
        self._solid_handle_id = check.opt_str_param(solid_handle_id, "solid_handle_id")
        super().__init__()

    def resolve_id(self, _graphene_info: ResolveInfo):
        if self._solid_handle_id:
            return f"{self._remote_job.get_remote_origin_id()}:solid:{self._solid_handle_id}"
        return f"graph:{self._remote_job.get_remote_origin_id()}"

    def resolve_name(self, _graphene_info: ResolveInfo):
        return self._remote_job.get_graph_name()

    def resolve_description(self, _graphene_info: ResolveInfo):
        return self._remote_job.description

    def resolve_solid_handle(
        self, _graphene_info: ResolveInfo, handleID: str
    ) -> Optional[GrapheneSolidHandle]:
        return build_solid_handles(self._remote_job).get(handleID)

    def resolve_solid_handles(
        self, _graphene_info: ResolveInfo, parentHandleID: Optional[str] = None
    ) -> Sequence[GrapheneSolidHandle]:
        handles = build_solid_handles(self._remote_job)

        if parentHandleID == "":
            handles = {key: handle for key, handle in handles.items() if not handle.parent}
        elif parentHandleID is not None:
            handles = {
                key: handle
                for key, handle in handles.items()
                if handle.parent and str(handle.parent.handleID) == parentHandleID
            }

        return [handles[key] for key in sorted(handles)]

    def resolve_modes(self, _graphene_info: ResolveInfo):
        # returns empty list... graphs don't have modes, this is a vestige of the old
        # pipeline explorer, which expected all solid containers to be pipelines
        return []


class GrapheneRunOrError(graphene.Union):
    class Meta:
        types = (GrapheneRun, GrapheneRunNotFoundError, GraphenePythonError)
        name = "RunOrError"


def _asset_key_input_list_to_asset_key_set(
    asset_keys: Optional[list[GrapheneAssetKeyInput]],
) -> Optional[AbstractSet[AssetKey]]:
    return (
        {key_input.to_asset_key() for key_input in asset_keys} if asset_keys is not None else None
    )
