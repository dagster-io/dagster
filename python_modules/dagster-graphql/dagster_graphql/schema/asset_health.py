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
    materializationStatus = graphene.Field(GrapheneAssetHealthStatus)
    assetChecksStatus = graphene.Field(GrapheneAssetHealthStatus)
    freshnessStatus = graphene.Field(GrapheneAssetHealthStatus)

    class Meta:
        name = "AssetHealth"

    def resolve_assetHealth(self, graphene_info: ResolveInfo):
        if not graphene_info.context.instance.asset_health_supported():
            return GrapheneAssetHealthStatus.UNKNOWN
        statuses = [
            self.resolve_materializationStatus(graphene_info),
            self.resolve_assetChecksStatus(graphene_info),
            self.resolve_freshnessStatus(graphene_info),
        ]
        if GrapheneAssetHealthStatus.DEGRADED in statuses:
            return GrapheneAssetHealthStatus.DEGRADED
        if GrapheneAssetHealthStatus.WARNING in statuses:
            return GrapheneAssetHealthStatus.WARNING
        if all(status == GrapheneAssetHealthStatus.UNKNOWN for status in statuses):
            return GrapheneAssetHealthStatus.UNKNOWN
        return GrapheneAssetHealthStatus.HEALTHY

    def resolve_materializationStatus(self, graphene_info: ResolveInfo):
        # if non-partitioned:
        # if latest materialization succeed, healthy
        # if latest materialization failed, degraded
        # no materialization, unknown
        # if partitioned:
        # if all partitions successfully materialized, healthy
        # if any partitions missing, warning
        # if any partitions failed, degraded
        if (
            not graphene_info.context.instance.asset_health_supported()
            or not graphene_info.context.instance.can_read_failure_events()
        ):
            # compute materialization status how we do today by checking the latest run the asset was materialized in (or using asset status cache for partitioned)
            pass
        else:
            # commpute the status based on the asset key table (or using asset status cache for partitioned)
            pass

        pass

    def resolve_assetChecksStatus(self, graphene_info: ResolveInfo):
        # all asset checks passed, health
        # any asset check warning, warning
        # any asset check failed, degraded
        if not graphene_info.context.instance.asset_health_supported():
            return GrapheneAssetHealthStatus.UNKNOWN

        pass

    def resolve_freshnessStatus(self, graphene_info: ResolveInfo):
        # if SLA is met, healthy
        # if SLA violated with warning, warning
        # if SLA violated with error, degraded
        if not graphene_info.context.instance.asset_health_supported():
            return GrapheneAssetHealthStatus.UNKNOWN

        pass
