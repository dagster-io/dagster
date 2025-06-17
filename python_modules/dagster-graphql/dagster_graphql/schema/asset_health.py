import asyncio

import graphene
from dagster._streamline.asset_health import (
    AssetHealthStatus,
    overall_status_from_component_statuses,
)

from dagster_graphql.implementation.fetch_asset_health import (
    get_asset_check_status_and_metadata,
    get_freshness_status_and_metadata,
    get_materialization_status_and_metadata,
)
from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.util import ResolveInfo

GrapheneAssetHealthStatus = graphene.Enum.from_enum(AssetHealthStatus)


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

    def __init__(self, asset_key: GrapheneAssetKey, dynamic_partitions_loader):
        super().__init__()
        self._asset_key = asset_key
        self._dynamic_partitions_loader = dynamic_partitions_loader
        self.materialization_status_task = None
        self.asset_check_status_task = None
        self.freshness_status_task = None

    async def resolve_materializationStatus(self, graphene_info: ResolveInfo) -> AssetHealthStatus:
        if self.materialization_status_task is None:
            self.materialization_status_task = asyncio.create_task(
                get_materialization_status_and_metadata(graphene_info.context, self._asset_key)
            )
        materialization_status, _ = await self.materialization_status_task
        return materialization_status

    async def resolve_materializationStatusMetadata(
        self, graphene_info: ResolveInfo
    ) -> GrapheneAssetHealthMaterializationMeta:
        if self.materialization_status_task is None:
            self.materialization_status_task = asyncio.create_task(
                get_materialization_status_and_metadata(graphene_info.context, self._asset_key)
            )
        _, materialization_status_metadata = await self.materialization_status_task
        return materialization_status_metadata

    async def resolve_assetChecksStatus(self, graphene_info: ResolveInfo) -> AssetHealthStatus:
        if self.asset_check_status_task is None:
            self.asset_check_status_task = asyncio.create_task(
                get_asset_check_status_and_metadata(graphene_info.context, self._asset_key)
            )

        asset_checks_status, _ = await self.asset_check_status_task
        return asset_checks_status

    async def resolve_assetChecksStatusMetadata(
        self, graphene_info: ResolveInfo
    ) -> GrapheneAssetHealthCheckMeta:
        if self.asset_check_status_task is None:
            self.asset_check_status_task = asyncio.create_task(
                get_asset_check_status_and_metadata(graphene_info.context, self._asset_key)
            )

        _, asset_checks_status_metadata = await self.asset_check_status_task
        return asset_checks_status_metadata

    async def resolve_freshnessStatus(self, graphene_info: ResolveInfo) -> AssetHealthStatus:
        if self.freshness_status_task is None:
            self.freshness_status_task = asyncio.create_task(
                get_freshness_status_and_metadata(graphene_info.context, self._asset_key)
            )

        freshness_status, _ = await self.freshness_status_task
        return freshness_status

    async def resolve_freshnessStatusMetadata(
        self, graphene_info: ResolveInfo
    ) -> GrapheneAssetHealthFreshnessMeta:
        if self.freshness_status_task is None:
            self.freshness_status_task = asyncio.create_task(
                get_freshness_status_and_metadata(graphene_info.context, self._asset_key)
            )

        _, freshness_status_metadata = await self.freshness_status_task
        return freshness_status_metadata

    async def resolve_assetHealth(self, graphene_info: ResolveInfo) -> AssetHealthStatus:
        if not graphene_info.context.instance.dagster_asset_health_queries_supported():
            return AssetHealthStatus.UNKNOWN
        if self.materialization_status_task is None:
            self.materialization_status_task = asyncio.create_task(
                get_materialization_status_and_metadata(graphene_info.context, self._asset_key)
            )
        materialization_status, _ = await self.materialization_status_task
        if self.asset_check_status_task is None:
            self.asset_check_status_task = asyncio.create_task(
                get_asset_check_status_and_metadata(graphene_info.context, self._asset_key)
            )
        asset_checks_status, _ = await self.asset_check_status_task
        if self.freshness_status_task is None:
            self.freshness_status_task = asyncio.create_task(
                get_freshness_status_and_metadata(graphene_info.context, self._asset_key)
            )
        freshness_status, _ = await self.freshness_status_task

        return overall_status_from_component_statuses(
            asset_checks_status=asset_checks_status,
            materialization_status=materialization_status,
            freshness_status=freshness_status,
        )
