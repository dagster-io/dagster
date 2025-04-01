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


def compute_health_status_from_component_statuses(
    materialization_status: GrapheneAssetHealthStatus,
    check_status: GrapheneAssetHealthStatus,
    freshness_status: GrapheneAssetHealthStatus,
) -> GrapheneAssetHealthStatus:
    all_statuses = [
        materialization_status,
        check_status,
        freshness_status,
    ]

    if GrapheneAssetHealthStatus.DEGRADED in all_statuses:
        return GrapheneAssetHealthStatus.DEGRADED
    if GrapheneAssetHealthStatus.WARNING in all_statuses:
        return GrapheneAssetHealthStatus.WARNING
    # at this point, all statuses are HEALTHY, UNKNOWN, or NOT_APPLICABLE
    if materialization_status == GrapheneAssetHealthStatus.UNKNOWN:
        return GrapheneAssetHealthStatus.UNKNOWN
    if all(
        status == GrapheneAssetHealthStatus.UNKNOWN
        or status == GrapheneAssetHealthStatus.NOT_APPLICABLE
        for status in all_statuses
    ):
        return GrapheneAssetHealthStatus.UNKNOWN
    # at least one status must be HEALTHY
    return GrapheneAssetHealthStatus.HEALTHY


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

        return compute_health_status_from_component_statuses(
            materialization_status=self.materializationStatus,
            check_status=self.assetChecksStatus,
            freshness_status=self.freshnessStatus,
        )
