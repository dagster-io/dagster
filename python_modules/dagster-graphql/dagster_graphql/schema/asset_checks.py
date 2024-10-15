from typing import Optional, Sequence, Union, cast

import dagster._check as check
import graphene
from dagster import EventLogEntry
from dagster._core.definitions.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSeverity
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.events import DagsterEventType
from dagster._core.remote_representation.external_data import AssetCheckNodeSnap
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionResolvedStatus,
)

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.schema.asset_key import GrapheneAssetKey
from dagster_graphql.schema.errors import GrapheneError
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.util import ResolveInfo, non_null_list

GrapheneAssetCheckExecutionResolvedStatus = graphene.Enum.from_enum(
    AssetCheckExecutionResolvedStatus
)


class GrapheneAssetCheckEvaluationTargetMaterializationData(graphene.ObjectType):
    storageId = graphene.NonNull(graphene.Int)
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

    # NOTE: this should be renamed passed
    success = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "AssetCheckEvaluation"

    def __init__(self, evaluation_event: EventLogEntry):
        self.timestamp = evaluation_event.timestamp

        evaluation_data = cast(
            AssetCheckEvaluation,
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


class GrapheneAssetCheckExecution(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    runId = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneAssetCheckExecutionResolvedStatus)
    evaluation = graphene.Field(GrapheneAssetCheckEvaluation)
    timestamp = graphene.Field(
        graphene.NonNull(graphene.Float), description="When the check run started"
    )
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

    def resolve_status(self, graphene_info: "ResolveInfo") -> AssetCheckExecutionResolvedStatus:
        return self._execution.resolve_status(graphene_info.context)


class GrapheneAssetCheckCanExecuteIndividually(graphene.Enum):
    class Meta:
        name = "AssetCheckCanExecuteIndividually"

    CAN_EXECUTE = "CAN_EXECUTE"
    REQUIRES_MATERIALIZATION = "REQUIRES_MATERIALIZATION"
    NEEDS_USER_CODE_UPGRADE = "NEEDS_USER_CODE_UPGRADE"


class GrapheneAssetCheck(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    assetKey = graphene.NonNull(GrapheneAssetKey)
    description = graphene.String()
    jobNames = non_null_list(graphene.String)
    executionForLatestMaterialization = graphene.Field(GrapheneAssetCheckExecution)
    canExecuteIndividually = graphene.NonNull(GrapheneAssetCheckCanExecuteIndividually)
    blocking = graphene.NonNull(graphene.Boolean)
    additionalAssetKeys = non_null_list(GrapheneAssetKey)

    class Meta:
        name = "AssetCheck"

    def __init__(self, asset_check: AssetCheckNodeSnap, can_execute_individually):
        self._asset_check = asset_check
        self._can_execute_individually = can_execute_individually

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

    def resolve_canExecuteIndividually(self, _) -> GrapheneAssetCheckCanExecuteIndividually:
        return self._can_execute_individually

    def resolve_blocking(self, _) -> bool:
        return self._asset_check.blocking

    def resolve_additionalAssetKeys(self, _) -> Sequence[GrapheneAssetKey]:
        return [
            GrapheneAssetKey(path=asset_key.path)
            for asset_key in self._asset_check.additional_asset_keys
        ]


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


class GrapheneAssetCheckHandle(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    assetKey = graphene.NonNull(GrapheneAssetKey)

    class Meta:
        name = "AssetCheckhandle"

    def __init__(self, handle: AssetCheckKey):
        super().__init__(name=handle.name, assetKey=GrapheneAssetKey(path=handle.asset_key.path))
