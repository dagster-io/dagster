from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING, Optional, Union, cast

import dagster._check as check
import graphene
from dagster import EventLogEntry
from dagster._core.definitions.asset_checks.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteAssetCheckNode
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionSnapshot,
)
from dagster._core.definitions.partitions.snap import MultiPartitionsSnap
from dagster._core.events import DagsterEventType
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionResolvedStatus,
)

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.schema.auto_materialize_policy import GrapheneAutoMaterializePolicy
from dagster_graphql.schema.automation_condition import GrapheneAutomationCondition
from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.errors import GrapheneError
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.util import ResolveInfo, non_null_list

if TYPE_CHECKING:
    from dagster_graphql.schema.partition_sets import (
        GrapheneDimensionPartitionKeys,
        GraphenePartitionDefinition,
    )

GrapheneAssetCheckExecutionResolvedStatus = graphene.Enum.from_enum(
    AssetCheckExecutionResolvedStatus
)


class GrapheneAssetCheckEvaluationTargetMaterializationData(graphene.ObjectType):
    storageId = graphene.NonNull(graphene.ID)
    runId = graphene.NonNull(graphene.String)
    timestamp = graphene.NonNull(graphene.Float)

    class Meta:
        name = "AssetCheckEvaluationTargetMaterializationData"

    def __init__(self, target_materialization_data: AssetCheckEvaluationTargetMaterializationData):
        self.storageId = target_materialization_data.storage_id
        self.runId = target_materialization_data.run_id
        self.timestamp = target_materialization_data.timestamp


GrapheneAssetCheckSeverity = graphene.Enum.from_enum(AssetCheckSeverity)


class GrapheneAssetCheckEvaluation(graphene.ObjectType):
    timestamp = graphene.Field(
        graphene.NonNull(graphene.Float), description="When the check evaluation was stored"
    )
    checkName = graphene.NonNull(graphene.String)
    assetKey = graphene.NonNull(GrapheneAssetKey)
    targetMaterialization = graphene.Field(GrapheneAssetCheckEvaluationTargetMaterializationData)
    metadataEntries = non_null_list(GrapheneMetadataEntry)
    severity = graphene.NonNull(GrapheneAssetCheckSeverity)
    description = graphene.String()
    partition = graphene.String()

    # NOTE: this should be renamed passed
    success = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "AssetCheckEvaluation"

    def __init__(self, evaluation_event: EventLogEntry):
        self.timestamp = evaluation_event.timestamp

        evaluation_data = cast(
            "AssetCheckEvaluation",
            check.not_none(evaluation_event.dagster_event).event_specific_data,
        )
        target_materialization_data = evaluation_data.target_materialization_data
        self.targetMaterialization = (
            GrapheneAssetCheckEvaluationTargetMaterializationData(target_materialization_data)
            if target_materialization_data
            else None
        )

        self.metadataEntries = list(iterate_metadata_entries(evaluation_data.metadata))
        self.severity = evaluation_data.severity
        self.success = evaluation_data.passed
        self.checkName = evaluation_data.check_name
        self.assetKey = evaluation_data.asset_key
        self.description = evaluation_data.description
        self.partition = evaluation_data.partition


class GrapheneAssetCheckExecution(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    runId = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneAssetCheckExecutionResolvedStatus)
    evaluation = graphene.Field(GrapheneAssetCheckEvaluation)
    timestamp = graphene.Field(
        graphene.NonNull(graphene.Float), description="When the check run started"
    )
    partition = graphene.Field(graphene.String)
    stepKey = graphene.Field(graphene.String)

    class Meta:
        name = "AssetCheckExecution"

    def __init__(self, execution: AssetCheckExecutionRecord):
        super().__init__()
        self._execution = execution
        self.id = str(execution.id)
        self.runId = execution.run_id
        self.evaluation = (
            GrapheneAssetCheckEvaluation(execution.event)
            if execution.event
            and execution.event.dagster_event_type == DagsterEventType.ASSET_CHECK_EVALUATION
            else None
        )
        self.timestamp = execution.create_timestamp
        self.stepKey = execution.event.step_key if execution.event else None
        self.partition = execution.partition

    async def resolve_status(
        self, graphene_info: "ResolveInfo"
    ) -> AssetCheckExecutionResolvedStatus:
        return await self._execution.resolve_status(graphene_info.context)


class GrapheneAssetCheckCanExecuteIndividually(graphene.Enum):
    class Meta:
        name = "AssetCheckCanExecuteIndividually"

    CAN_EXECUTE = "CAN_EXECUTE"
    REQUIRES_MATERIALIZATION = "REQUIRES_MATERIALIZATION"
    NEEDS_USER_CODE_UPGRADE = "NEEDS_USER_CODE_UPGRADE"


# Enum for asset check partition range status
class AssetCheckPartitionRangeStatus(Enum):
    """Status for asset check partition ranges."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"
    SKIPPED = "SKIPPED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


GrapheneAssetCheckPartitionRangeStatus = graphene.Enum.from_enum(AssetCheckPartitionRangeStatus)


# Time partition types
class GrapheneAssetCheckTimePartitionRangeStatus(graphene.ObjectType):
    """Time range with associated check status.

    Uses the same fields as GrapheneTimePartitionRange but with check-specific status.
    """

    startTime = graphene.NonNull(graphene.Float)
    endTime = graphene.NonNull(graphene.Float)
    startKey = graphene.NonNull(graphene.String)
    endKey = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneAssetCheckPartitionRangeStatus)

    class Meta:
        name = "AssetCheckTimePartitionRangeStatus"


class GrapheneAssetCheckTimePartitionStatuses(graphene.ObjectType):
    """Time-partitioned asset check statuses with range compression.

    Each range represents a contiguous set of partitions with the same status.
    Unlike assets, asset checks expose all 6 statuses as separate ranges.
    """

    ranges = non_null_list(GrapheneAssetCheckTimePartitionRangeStatus)

    class Meta:
        name = "AssetCheckTimePartitionStatuses"


# Default partition type
class GrapheneAssetCheckDefaultPartitionStatuses(graphene.ObjectType):
    """Static-partitioned asset check statuses as partition key lists.

    Each field contains the list of partition keys with that status.
    """

    succeededPartitions = non_null_list(graphene.String)
    failedPartitions = non_null_list(graphene.String)
    inProgressPartitions = non_null_list(graphene.String)
    skippedPartitions = non_null_list(graphene.String)
    executionFailedPartitions = non_null_list(graphene.String)

    class Meta:
        name = "AssetCheckDefaultPartitionStatuses"


# Multi-partition types
class GrapheneAssetCheckPartitionStatus1D(graphene.Union):
    """Union for secondary dimension (can be Time or Default)."""

    class Meta:
        types = (
            GrapheneAssetCheckTimePartitionStatuses,
            GrapheneAssetCheckDefaultPartitionStatuses,
        )
        name = "AssetCheckPartitionStatus1D"


class GrapheneAssetCheckMultiPartitionRangeStatuses(graphene.ObjectType):
    """Range in primary dimension with secondary dimension statuses.

    The primary dimension is compressed using run-length encoding (consecutive primary
    partitions with identical secondary dimension status patterns are grouped).
    """

    primaryDimStartKey = graphene.NonNull(graphene.String)
    primaryDimEndKey = graphene.NonNull(graphene.String)
    primaryDimStartTime = graphene.Field(graphene.Float)
    primaryDimEndTime = graphene.Field(graphene.Float)
    secondaryDim = graphene.NonNull(GrapheneAssetCheckPartitionStatus1D)

    class Meta:
        name = "AssetCheckMultiPartitionRangeStatuses"


class GrapheneAssetCheckMultiPartitionStatuses(graphene.ObjectType):
    """Multi-partitioned asset check statuses with 2D run-length encoding."""

    ranges = non_null_list(GrapheneAssetCheckMultiPartitionRangeStatuses)
    primaryDimensionName = graphene.NonNull(graphene.String)

    class Meta:
        name = "AssetCheckMultiPartitionStatuses"


# Union type (replaces old ObjectType)
class GrapheneAssetCheckPartitionStatuses(graphene.Union):
    """Union type for asset check partition statuses.

    The concrete type returned depends on the partitions definition:
    - TimeWindowPartitionsDefinition -> AssetCheckTimePartitionStatuses
    - MultiPartitionsDefinition -> AssetCheckMultiPartitionStatuses
    - Other (Static, Dynamic) -> AssetCheckDefaultPartitionStatuses
    """

    class Meta:
        types = (
            GrapheneAssetCheckDefaultPartitionStatuses,
            GrapheneAssetCheckMultiPartitionStatuses,
            GrapheneAssetCheckTimePartitionStatuses,
        )
        name = "AssetCheckPartitionStatuses"


class GrapheneAssetCheck(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    assetKey = graphene.NonNull(GrapheneAssetKey)
    description = graphene.String()
    jobNames = non_null_list(graphene.String)
    executionForLatestMaterialization = graphene.Field(GrapheneAssetCheckExecution)
    canExecuteIndividually = graphene.NonNull(GrapheneAssetCheckCanExecuteIndividually)
    blocking = graphene.NonNull(graphene.Boolean)
    additionalAssetKeys = non_null_list(GrapheneAssetKey)
    automationCondition = graphene.Field(GrapheneAutomationCondition)
    partitionDefinition = graphene.Field(
        "dagster_graphql.schema.partition_sets.GraphenePartitionDefinition"
    )
    partitionKeysByDimension = graphene.Field(
        non_null_list("dagster_graphql.schema.partition_sets.GrapheneDimensionPartitionKeys"),
        startIdx=graphene.Int(),
        endIdx=graphene.Int(),
    )
    partitionStatuses = graphene.Field(GrapheneAssetCheckPartitionStatuses)

    class Meta:
        name = "AssetCheck"

    def __init__(
        self,
        remote_node: RemoteAssetCheckNode,
    ):
        self._remote_node = remote_node
        self._asset_check = remote_node.asset_check

    def resolve_assetKey(self, _) -> AssetKey:
        return self._asset_check.asset_key

    def resolve_name(self, _) -> str:
        return self._asset_check.name

    def resolve_description(self, _) -> Optional[str]:
        return self._asset_check.description

    def resolve_jobNames(self, _) -> Sequence[str]:
        return self._asset_check.job_names

    async def resolve_executionForLatestMaterialization(
        self, graphene_info: ResolveInfo
    ) -> Optional[GrapheneAssetCheckExecution]:
        record = await AssetCheckExecutionRecord.gen(graphene_info.context, self._asset_check.key)
        return (
            GrapheneAssetCheckExecution(record)
            if record and await record.targets_latest_materialization(graphene_info.context)
            else None
        )

    def resolve_canExecuteIndividually(self, _: ResolveInfo):
        return (
            GrapheneAssetCheckCanExecuteIndividually.CAN_EXECUTE
            if len(self._remote_node.execution_set_entity_keys) <= 1
            # NOTE: once we support multi checks, we'll need to add a case for
            # non subsettable multi checks
            else GrapheneAssetCheckCanExecuteIndividually.REQUIRES_MATERIALIZATION
        )

    def resolve_blocking(self, _) -> bool:
        return self._asset_check.blocking

    def resolve_additionalAssetKeys(self, _) -> Sequence[GrapheneAssetKey]:
        return [
            GrapheneAssetKey(path=asset_key.path)
            for asset_key in self._asset_check.additional_asset_keys
        ]

    def resolve_automationCondition(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GrapheneAutoMaterializePolicy]:
        automation_condition = (
            self._asset_check.automation_condition_snapshot
            or self._asset_check.automation_condition
        )
        if automation_condition:
            return GrapheneAutomationCondition(
                # we only store one of automation_condition or automation_condition_snapshot
                automation_condition
                if isinstance(automation_condition, AutomationConditionSnapshot)
                else automation_condition.get_snapshot()
            )
        return None

    def resolve_partitionDefinition(
        self, _graphene_info: ResolveInfo
    ) -> Optional["GraphenePartitionDefinition"]:
        from dagster_graphql.schema.partition_sets import GraphenePartitionDefinition

        partitions_snap = self._asset_check.partitions_def_snapshot
        if partitions_snap:
            return GraphenePartitionDefinition(partitions_snap)
        return None

    def resolve_partitionKeysByDimension(
        self,
        graphene_info: ResolveInfo,
        startIdx: Optional[int] = None,
        endIdx: Optional[int] = None,
    ) -> Sequence["GrapheneDimensionPartitionKeys"]:
        from dagster_graphql.schema.partition_sets import (
            GrapheneDimensionPartitionKeys,
            GraphenePartitionDefinitionType,
            get_partition_keys_from_snap,
        )

        # Accepts startIdx and endIdx arguments. This will be used to select a range of
        # time partitions. StartIdx is inclusive, endIdx is exclusive.
        # For non time partition definitions, these arguments will be ignored
        # and the full list of partition keys will be returned.
        if not self._asset_check.partitions_def_snapshot:
            return []

        dynamic_partitions_loader = graphene_info.context.dynamic_partitions_loader
        if isinstance(self._asset_check.partitions_def_snapshot, MultiPartitionsSnap):
            return [
                GrapheneDimensionPartitionKeys(
                    name=dimension.name,
                    partition_keys=get_partition_keys_from_snap(
                        dimension.partitions,
                        dynamic_partitions_loader,
                        startIdx,
                        endIdx,
                    ),
                    type=GraphenePartitionDefinitionType.from_partition_def_data(
                        dimension.partitions
                    ),
                )
                for dimension in cast(
                    "MultiPartitionsSnap",
                    self._asset_check.partitions_def_snapshot,
                ).partition_dimensions
            ]

        return [
            GrapheneDimensionPartitionKeys(
                name="default",
                type=GraphenePartitionDefinitionType.from_partition_def_data(
                    self._asset_check.partitions_def_snapshot
                ),
                partition_keys=get_partition_keys_from_snap(
                    partitions_snap=self._asset_check.partitions_def_snapshot,
                    dynamic_partitions_loader=dynamic_partitions_loader,
                    start_idx=startIdx,
                    end_idx=endIdx,
                ),
            )
        ]

    async def resolve_partitionStatuses(
        self, graphene_info: ResolveInfo
    ) -> Optional[
        Union[
            "GrapheneAssetCheckTimePartitionStatuses",
            "GrapheneAssetCheckDefaultPartitionStatuses",
            "GrapheneAssetCheckMultiPartitionStatuses",
        ]
    ]:
        """Resolve partition statuses using union type with efficient representation."""
        from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
        from dagster._core.storage.asset_check_state import AssetCheckState

        from dagster_graphql.implementation.fetch_asset_checks import (
            build_asset_check_partition_statuses,
        )

        # Only return partition statuses for partitioned checks
        if not self._asset_check.partitions_def_snapshot:
            return None

        check_key = AssetCheckKey(
            asset_key=self._asset_check.asset_key, name=self._asset_check.name
        )

        # Get current partition definition
        current_partition_def = (
            self._asset_check.partitions_def_snapshot.get_partitions_definition()
        )

        # Get partition status cache using the cache service (handles storage + reconciliation)
        partition_status = await AssetCheckState.gen(
            graphene_info.context, (check_key, current_partition_def)
        )
        if not partition_status:
            return None

        # Use builder function to construct appropriate union type
        return build_asset_check_partition_statuses(
            key=check_key,
            asset_check_state=partition_status,
            partitions_def=current_partition_def,
            dynamic_partitions_store=graphene_info.context.instance,
        )


class GrapheneAssetChecks(graphene.ObjectType):
    checks = non_null_list(GrapheneAssetCheck)

    class Meta:
        name = "AssetChecks"


class GrapheneAssetCheckNeedsMigrationError(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneError,)
        name = "AssetCheckNeedsMigrationError"


class GrapheneAssetCheckNeedsAgentUpgradeError(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneError,)
        name = "AssetCheckNeedsAgentUpgradeError"


class GrapheneAssetCheckNeedsUserCodeUpgrade(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneError,)
        name = "AssetCheckNeedsUserCodeUpgrade"


AssetChecksOrErrorUnion = Union[
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
    GrapheneAssetCheckNeedsAgentUpgradeError,
    GrapheneAssetChecks,
]


class GrapheneAssetChecksOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetChecks,
            GrapheneAssetCheckNeedsMigrationError,
            GrapheneAssetCheckNeedsUserCodeUpgrade,
            GrapheneAssetCheckNeedsAgentUpgradeError,
        )
        name = "AssetChecksOrError"


class GrapheneAssetCheckNotFoundError(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneError,)
        name = "AssetCheckNotFoundError"


class GrapheneAssetCheckOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetCheck,
            GrapheneAssetCheckNotFoundError,
            GrapheneAssetCheckNeedsMigrationError,
            GrapheneAssetCheckNeedsUserCodeUpgrade,
            GrapheneAssetCheckNeedsAgentUpgradeError,
        )
        name = "AssetCheckOrError"
