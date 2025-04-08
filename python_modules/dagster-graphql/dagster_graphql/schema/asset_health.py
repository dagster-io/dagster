import graphene

from dagster_graphql.schema.util import ResolveInfo


class GrapheneAssetHealthStatus(graphene.Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"

    class Meta:
        name = "AssetHealthStatus"


class GrapheneAssetHealth(graphene.ObjectType):
    assetHealth = graphene.NonNull(GrapheneAssetHealthStatus)
    materializationStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    materializationStatusMessage = graphene.String()
    assetChecksStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    assetChecksStatusMessage = graphene.String()
    freshnessStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    freshnessStatusMessage = graphene.String()

    class Meta:
        name = "AssetHealth"

    def resolve_assetHealth(self, graphene_info: ResolveInfo):
        if not graphene_info.context.instance.dagster_observe_supported():
            return GrapheneAssetHealthStatus.UNKNOWN
        statuses = [
            self.materializationStatus,
            self.assetChecksStatus,
            self.freshnessStatus,
        ]
        if GrapheneAssetHealthStatus.DEGRADED in statuses:
            return GrapheneAssetHealthStatus.DEGRADED
        if GrapheneAssetHealthStatus.WARNING in statuses:
            return GrapheneAssetHealthStatus.WARNING
        # at this point, all statuses are HEALTHY, UNKNOWN, or NOT_APPLICABLE
        if self.materializationStatus == GrapheneAssetHealthStatus.UNKNOWN:
            return GrapheneAssetHealthStatus.UNKNOWN
        if all(
            status == GrapheneAssetHealthStatus.UNKNOWN
            or status == GrapheneAssetHealthStatus.NOT_APPLICABLE
            for status in statuses
        ):
            return GrapheneAssetHealthStatus.UNKNOWN
        # at least one status must be HEALTHY
        return GrapheneAssetHealthStatus.HEALTHY
