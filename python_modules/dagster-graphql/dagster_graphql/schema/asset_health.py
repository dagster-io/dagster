import graphene

from dagster_graphql.schema.util import ResolveInfo


class GrapheneAssetHealthStatus(graphene.Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"

    class Meta:
        name = "AssetHealthStatus"


class GrapheneAssetHealth(graphene.ObjectType):
    assetHealth = graphene.NonNull(GrapheneAssetHealthStatus)
    materializationStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    assetChecksStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    freshnessStatus = graphene.NonNull(GrapheneAssetHealthStatus)

    class Meta:
        name = "AssetHealth"

    def resolve_assetHealth(self, graphene_info: ResolveInfo):
        if not graphene_info.context.instance.dagster_observe_supported():
            return GrapheneAssetHealthStatus.UNKNOWN
        statuses = [
            self.materializationStatus(graphene_info),
            self.assetChecksStatus(graphene_info),
            self.freshnessStatus(graphene_info),
        ]
        if GrapheneAssetHealthStatus.DEGRADED in statuses:
            return GrapheneAssetHealthStatus.DEGRADED
        if GrapheneAssetHealthStatus.WARNING in statuses:
            return GrapheneAssetHealthStatus.WARNING
        if all(status == GrapheneAssetHealthStatus.UNKNOWN for status in statuses):
            return GrapheneAssetHealthStatus.UNKNOWN
        return GrapheneAssetHealthStatus.HEALTHY
