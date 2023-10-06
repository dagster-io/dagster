from typing import List, Optional, cast

import dagster._check as check
import graphene
from dagster import EventLogEntry
from dagster._core.definitions.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSeverity
from dagster._core.host_representation.external_data import ExternalAssetCheck
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionResolvedStatus,
)

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.schema.errors import GrapheneError
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.util import non_null_list

from .asset_key import GrapheneAssetKey
from .util import ResolveInfo

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


class GrapheneAssetCheckExecution(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    runId = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneAssetCheckExecutionResolvedStatus)
    evaluation = graphene.Field(GrapheneAssetCheckEvaluation)
    timestamp = graphene.Field(
        graphene.NonNull(graphene.Float), description="When the check run started"
    )

    class Meta:
        name = "AssetCheckExecution"

    def __init__(
        self,
        execution: AssetCheckExecutionRecord,
        status: AssetCheckExecutionResolvedStatus,
    ):
        super().__init__()
        self.id = str(execution.id)
        self.runId = execution.run_id
        self.status = status
        self.evaluation = (
            GrapheneAssetCheckEvaluation(execution.evaluation_event)
            if execution.evaluation_event
            else None
        )
        self.timestamp = execution.create_timestamp


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
    executions = graphene.Field(
        non_null_list(GrapheneAssetCheckExecution),
        limit=graphene.NonNull(graphene.Int),
        cursor=graphene.String(),
    )
    executionForLatestMaterialization = graphene.Field(GrapheneAssetCheckExecution)
    canExecuteIndividually = graphene.NonNull(GrapheneAssetCheckCanExecuteIndividually)

    class Meta:
        name = "AssetCheck"

    def __init__(
        self,
        asset_check: ExternalAssetCheck,
        can_execute_individually,
    ):
        self._asset_check = asset_check
        self._can_execute_individually = can_execute_individually

    def resolve_assetKey(self, _):
        return self._asset_check.asset_key

    def resolve_name(self, _) -> str:
        return self._asset_check.name

    def resolve_description(self, _) -> Optional[str]:
        return self._asset_check.description

    def resolve_executions(
        self, graphene_info: ResolveInfo, **kwargs
    ) -> List[GrapheneAssetCheckExecution]:
        from dagster_graphql.implementation.fetch_asset_checks import (
            fetch_executions,
        )

        return fetch_executions(
            graphene_info.context.instance, self._asset_check, kwargs["limit"], kwargs.get("cursor")
        )

    def resolve_executionForLatestMaterialization(
        self, graphene_info: ResolveInfo
    ) -> Optional[GrapheneAssetCheckExecution]:
        from dagster_graphql.implementation.fetch_asset_checks import (
            fetch_execution_for_latest_materialization,
        )

        return fetch_execution_for_latest_materialization(
            graphene_info.context.instance, self._asset_check
        )

    def resolve_canExecuteIndividually(self, _) -> GrapheneAssetCheckCanExecuteIndividually:
        return self._can_execute_individually


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
