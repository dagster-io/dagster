import asyncio

import graphene

from dagster_graphql.implementation.fetch_asset_health import (
    get_asset_check_status_and_metadata,
    get_freshness_status_and_metadata,
    get_materialization_status_and_metadata,
)
from dagster_graphql.schema.util import ResolveInfo


class GrapheneAssetHealthStatus(graphene.Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"

    class Meta:
        name = "AssetHealthStatus"


class GrapheneAssetHealthCheckDegradedMeta(graphene.ObjectType):
    numFailedChecks = graphene.NonNull(graphene.Int)
    numWarningChecks = graphene.NonNull(graphene.Int)
    totalNumChecks = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthCheckDegradedMeta"


class GrapheneAssetHealthCheckWarningMeta(graphene.ObjectType):
    numWarningChecks = graphene.NonNull(graphene.Int)
    totalNumChecks = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthCheckWarningMeta"


class GrapheneAssetHealthCheckUnknownMeta(graphene.ObjectType):
    numNotExecutedChecks = graphene.NonNull(graphene.Int)
    totalNumChecks = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthCheckUnknownMeta"


class GrapheneAssetHealthCheckMeta(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetHealthCheckDegradedMeta,
            GrapheneAssetHealthCheckWarningMeta,
            GrapheneAssetHealthCheckUnknownMeta,
        )
        name = "AssetHealthCheckMeta"


class GrapheneAssetHealthMaterializationDegradedPartitionedMeta(graphene.ObjectType):
    numFailedPartitions = graphene.NonNull(graphene.Int)
    numMissingPartitions = graphene.NonNull(graphene.Int)
    totalNumPartitions = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthMaterializationDegradedPartitionedMeta"


class GrapheneAssetHealthMaterializationHealthyPartitionedMeta(graphene.ObjectType):
    numMissingPartitions = graphene.NonNull(graphene.Int)
    totalNumPartitions = graphene.NonNull(graphene.Int)

    class Meta:
        name = "AssetHealthMaterializationHealthyPartitionedMeta"


class GrapheneAssetHealthMaterializationDegradedNotPartitionedMeta(graphene.ObjectType):
    failedRunId = graphene.NonNull(graphene.String)

    class Meta:
        name = "AssetHealthMaterializationDegradedNotPartitionedMeta"


class GrapheneAssetHealthMaterializationMeta(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetHealthMaterializationDegradedPartitionedMeta,
            GrapheneAssetHealthMaterializationHealthyPartitionedMeta,
            GrapheneAssetHealthMaterializationDegradedNotPartitionedMeta,
        )
        name = "AssetHealthMaterializationMeta"


class GrapheneAssetHealthFreshnessMeta(graphene.ObjectType):
    lastMaterializedTimestamp = graphene.Field(graphene.Float)

    class Meta:
        name = "AssetHealthFreshnessMeta"


class GrapheneAssetHealth(graphene.ObjectType):
    assetHealth = graphene.NonNull(GrapheneAssetHealthStatus)
    materializationStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    materializationStatusMetadata = graphene.Field(GrapheneAssetHealthMaterializationMeta)
    assetChecksStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    assetChecksStatusMetadata = graphene.Field(GrapheneAssetHealthCheckMeta)
    freshnessStatus = graphene.NonNull(GrapheneAssetHealthStatus)
    freshnessStatusMetadata = graphene.Field(GrapheneAssetHealthFreshnessMeta)

    class Meta:
        name = "AssetHealth"

    def __init__(self, asset_node_snap, dynamic_partitions_loader):
        super().__init__()
        self._asset_node_snap = asset_node_snap
        self._dynamic_partitions_loader = dynamic_partitions_loader
        self.materialization_status_task = None
        self.asset_check_status_task = None
        self.freshness_status_task = None

    async def resolve_materializationStatus(self, graphene_info: ResolveInfo) -> str:
        if self.materialization_status_task is None:
            self.materialization_status_task = asyncio.create_task(
                get_materialization_status_and_metadata(
                    graphene_info, self._asset_node_snap.asset_key
                )
            )
        materialization_status, _ = await self.materialization_status_task
        return materialization_status

    async def resolve_materializationStatusMetadata(
        self, graphene_info: ResolveInfo
    ) -> GrapheneAssetHealthMaterializationMeta:
        if self.materialization_status_task is None:
            self.materialization_status_task = asyncio.create_task(
                get_materialization_status_and_metadata(
                    graphene_info, self._asset_node_snap.asset_key
                )
            )
        _, materialization_status_metadata = await self.materialization_status_task
        return materialization_status_metadata

    async def resolve_assetChecksStatus(self, graphene_info: ResolveInfo) -> str:
        if self.asset_check_status_task is None:
            self.asset_check_status_task = asyncio.create_task(
                get_asset_check_status_and_metadata(graphene_info, self._asset_node_snap.asset_key)
            )

        asset_checks_status, _ = await self.asset_check_status_task
        return asset_checks_status

    async def resolve_assetChecksStatusMetadata(
        self, graphene_info: ResolveInfo
    ) -> GrapheneAssetHealthCheckMeta:
        if self.asset_check_status_task is None:
            self.asset_check_status_task = asyncio.create_task(
                get_asset_check_status_and_metadata(graphene_info, self._asset_node_snap.asset_key)
            )

        _, asset_checks_status_metadata = await self.asset_check_status_task
        return asset_checks_status_metadata

    async def resolve_freshnessStatus(self, graphene_info: ResolveInfo) -> str:
        if self.freshness_status_task is None:
            self.freshness_status_task = asyncio.create_task(
                get_freshness_status_and_metadata(graphene_info, self._asset_node_snap.asset_key)
            )

        freshness_status, _ = await self.freshness_status_task
        return freshness_status

    async def resolve_freshnessStatusMetadata(
        self, graphene_info: ResolveInfo
    ) -> GrapheneAssetHealthFreshnessMeta:
        if self.freshness_status_task is None:
            self.freshness_status_task = asyncio.create_task(
                get_freshness_status_and_metadata(graphene_info, self._asset_node_snap.asset_key)
            )

        _, freshness_status_metadata = await self.freshness_status_task
        return freshness_status_metadata

    async def resolve_assetHealth(self, graphene_info: ResolveInfo):
        if not graphene_info.context.instance.dagster_observe_supported():
            return GrapheneAssetHealthStatus.UNKNOWN
        if self.materialization_status_task is None:
            self.materialization_status_task = asyncio.create_task(
                get_materialization_status_and_metadata(
                    graphene_info, self._asset_node_snap.asset_key
                )
            )
        materialization_status, _ = await self.materialization_status_task
        if self.asset_check_status_task is None:
            self.asset_check_status_task = asyncio.create_task(
                get_asset_check_status_and_metadata(graphene_info, self._asset_node_snap.asset_key)
            )
        asset_checks_status, _ = await self.asset_check_status_task
        if self.freshness_status_task is None:
            self.freshness_status_task = asyncio.create_task(
                get_freshness_status_and_metadata(graphene_info, self._asset_node_snap.asset_key)
            )
        freshness_status, _ = await self.freshness_status_task
        statuses = [
            materialization_status,
            asset_checks_status,
            freshness_status,
        ]
        if GrapheneAssetHealthStatus.DEGRADED in statuses:
            return GrapheneAssetHealthStatus.DEGRADED
        if GrapheneAssetHealthStatus.WARNING in statuses:
            return GrapheneAssetHealthStatus.WARNING
        # at this point, all statuses are HEALTHY, UNKNOWN, or NOT_APPLICABLE
        if materialization_status == GrapheneAssetHealthStatus.UNKNOWN:
            return GrapheneAssetHealthStatus.UNKNOWN
        if all(
            status == GrapheneAssetHealthStatus.UNKNOWN
            or status == GrapheneAssetHealthStatus.NOT_APPLICABLE
            for status in statuses
        ):
            return GrapheneAssetHealthStatus.UNKNOWN
        # at least one status must be HEALTHY
        return GrapheneAssetHealthStatus.HEALTHY
