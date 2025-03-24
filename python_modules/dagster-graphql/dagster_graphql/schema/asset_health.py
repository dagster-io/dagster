import graphene


class GrapheneAssetHealthStatus(graphene.Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"

    class Meta:
        name = "AssetHealthStatus"


class GrapheneAssetHealth(graphene.ObjectType):
    assetHealth = graphene.NonNull(GrapheneAssetHealthStatus)
    latestMaterializationAttemptStatus = graphene.Field(GrapheneAssetHealthStatus)
    assetChecksStatus = graphene.Field(GrapheneAssetHealthStatus)
    freshnessStatus = graphene.Field(GrapheneAssetHealthStatus)

    class Meta:
        name = "AssetHealth"

    def resolve_assetHealth(self, graphene_info):
        statuses = [
            self.resolve_latestMaterializationAttemptStatus(graphene_info),
            self.resolve_assetChecksStatus(graphene_info),
            self.resolve_freshnessStatus(graphene_info),
        ]
        if GrapheneAssetHealthStatus.DEGRADED in statuses:
            return GrapheneAssetHealthStatus.DEGRADED
        if GrapheneAssetHealthStatus.WARNING in statuses:
            return GrapheneAssetHealthStatus.WARNING
        if all(statuses == GrapheneAssetHealthStatus.HEALTHY for status in statuses):
            return GrapheneAssetHealthStatus.HEALTHY
        return GrapheneAssetHealthStatus.UNKNOWN

    def resolve_latestMaterializationAttemptStatus(self, graphene_info):
        # if non-partitioned:
        # if latest materialization succeed, healthy
        # if latest materialization failed, degraded
        # no materialization, unknown
        # if partitioned:
        # if all partitions successfully materialized, healthy
        # if any partitions missing, warning
        # if any partitions failed, degraded
        pass

    def resolve_assetChecksStatus(self, graphene_info):
        # all asset checks passed, health
        # any asset check warning, warning
        # any asset check failed, degraded
        pass

    def resolve_freshnessStatus(self, graphene_info):
        # if SLA is met, healthy
        # if SLA violated with warning, warning
        # if SLA violated with error, degraded
        pass
