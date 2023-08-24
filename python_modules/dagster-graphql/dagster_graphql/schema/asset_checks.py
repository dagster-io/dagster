import graphene
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionStatus

from dagster_graphql.schema.errors import GrapheneError
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.util import non_null_list
from .util import ResolveInfo
from .asset_key import GrapheneAssetKey

GrapheneAssetCheckExecutionStatus = graphene.Enum.from_enum(AssetCheckExecutionStatus)


class GrapheneAssetCheckEvaluationTargetMaterializationData(graphene.ObjectType):
    storageId = graphene.NonNull(graphene.Int)
    runId = graphene.NonNull(graphene.String)
    timestamp = graphene.NonNull(graphene.Float)

    class Meta:
        name = "AssetCheckEvaluationTargetMaterializationData"


class GrapheneAssetCheckEvaluation(graphene.ObjectType):
    timestamp = graphene.NonNull(graphene.Float)
    targetMaterialization = graphene.Field(GrapheneAssetCheckEvaluationTargetMaterializationData)
    metadataEntries = non_null_list(GrapheneMetadataEntry)

    class Meta:
        name = "AssetCheckEvaluation"


class GrapheneAssetCheckExecution(graphene.ObjectType):
    id = graphene.NonNull(graphene.Int)
    runId = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneAssetCheckExecutionStatus)
    evaluation = graphene.Field(GrapheneAssetCheckEvaluation)

    class Meta:
        name = "AssetCheckExecution"


class GrapheneAssetCheck(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    assetKey = graphene.NonNull(GrapheneAssetKey)
    description = graphene.String()
    executions = graphene.Field(
        non_null_list(GrapheneAssetCheckExecution),
        limit=graphene.NonNull(graphene.Int),
        cursor=graphene.NonNull(graphene.String),
    )

    class Meta:
        name = "AssetCheck"

    def resolve_executions(self, graphene_info: ResolveInfo, **kwargs):
        graphene_info.context.instance.event_log_storage.get_asset_check_executions(
            asset_key=AssetKey(self.assetKey.path),
            check_name=self.name,
            limit=kwargs["limit"],
            cursor=kwargs["cursor"],
        )
        # TODO


class GrapheneAssetChecks(graphene.ObjectType):
    checks = non_null_list(GrapheneAssetCheck)

    class Meta:
        name = "AssetChecks"


class GrapheneAssetCheckNeedsMigrationError(graphene.ObjectType):
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneError,)
        name = "AssetCheckNeedsMigrationError"


class GrapheneAssetChecksOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetChecks,
            GrapheneAssetCheckNeedsMigrationError,
        )
        name = "AssetChecksOrError"
