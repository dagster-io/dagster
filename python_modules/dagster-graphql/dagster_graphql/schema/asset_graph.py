from typing import TYPE_CHECKING, Any, List, Optional, Sequence, Union, cast

import graphene
from dagster import (
    AssetKey,
    _check as check,
)
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.data_version import (
    NULL_DATA_VERSION,
    StaleCauseCategory,
    StaleStatus,
)
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.partition import CachingDynamicPartitionsLoader
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.host_representation import CodeLocation, ExternalRepository
from dagster._core.host_representation.external import ExternalJob
from dagster._core.host_representation.external_data import (
    ExternalAssetNode,
    ExternalDynamicPartitionsDefinitionData,
    ExternalMultiPartitionsDefinitionData,
    ExternalPartitionsDefinitionData,
    ExternalStaticPartitionsDefinitionData,
    ExternalTimeWindowPartitionsDefinitionData,
)
from dagster._core.snap.node import GraphDefSnap, OpDefSnap
from dagster._core.workspace.permissions import Permissions
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.implementation.fetch_assets import (
    get_asset_materializations,
    get_asset_observations,
)
from dagster_graphql.schema.config_types import GrapheneConfigTypeField
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.partition_sets import (
    GrapheneDimensionPartitionKeys,
    GraphenePartitionDefinition,
    GraphenePartitionDefinitionType,
)
from dagster_graphql.schema.solids import (
    GrapheneCompositeSolidDefinition,
    GrapheneResourceRequirement,
    GrapheneSolidDefinition,
)

from ..implementation.fetch_assets import (
    build_partition_statuses,
    get_freshness_info,
    get_partition_subsets,
)
from ..implementation.loader import (
    BatchMaterializationLoader,
    CrossRepoAssetDependedByLoader,
    StaleStatusLoader,
)
from . import external
from .asset_key import GrapheneAssetKey
from .auto_materialize_policy import GrapheneAutoMaterializePolicy
from .dagster_types import (
    GrapheneDagsterType,
    GrapheneListDagsterType,
    GrapheneNullableDagsterType,
    GrapheneRegularDagsterType,
    to_dagster_type,
)
from .errors import GrapheneAssetNotFoundError
from .freshness_policy import GrapheneAssetFreshnessInfo, GrapheneFreshnessPolicy
from .logs.events import GrapheneMaterializationEvent, GrapheneObservationEvent
from .pipelines.pipeline import (
    GrapheneAssetPartitionStatuses,
    GrapheneDefaultPartitions,
    GrapheneMultiPartitions,
    GraphenePartitionStats,
    GraphenePipeline,
    GrapheneRun,
    GrapheneTimePartitions,
)
from .util import ResolveInfo, non_null_list

if TYPE_CHECKING:
    from .external import GrapheneRepository

GrapheneAssetStaleStatus = graphene.Enum.from_enum(StaleStatus, name="StaleStatus")
GrapheneAssetStaleCauseCategory = graphene.Enum.from_enum(
    StaleCauseCategory, name="StaleCauseCategory"
)


class GrapheneAssetStaleCause(graphene.ObjectType):
    key = graphene.NonNull(GrapheneAssetKey)
    category = graphene.NonNull(GrapheneAssetStaleCauseCategory)
    reason = graphene.NonNull(graphene.String)
    dependency = graphene.Field(GrapheneAssetKey)

    class Meta:
        name = "StaleCause"


class GrapheneAssetDependency(graphene.ObjectType):
    class Meta:
        name = "AssetDependency"

    asset = graphene.NonNull("dagster_graphql.schema.asset_graph.GrapheneAssetNode")
    inputName = graphene.NonNull(graphene.String)

    def __init__(
        self,
        repository_location: CodeLocation,
        external_repository: ExternalRepository,
        input_name: Optional[str],
        asset_key: AssetKey,
        materialization_loader: Optional[BatchMaterializationLoader] = None,
        depended_by_loader: Optional[CrossRepoAssetDependedByLoader] = None,
    ):
        self._repository_location = check.inst_param(
            repository_location, "repository_location", CodeLocation
        )
        self._external_repository = check.inst_param(
            external_repository, "external_repository", ExternalRepository
        )
        self._asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        self._latest_materialization_loader = check.opt_inst_param(
            materialization_loader, "materialization_loader", BatchMaterializationLoader
        )
        self._depended_by_loader = check.opt_inst_param(
            depended_by_loader, "depended_by_loader", CrossRepoAssetDependedByLoader
        )
        super().__init__(inputName=input_name)

    def resolve_asset(self, _graphene_info: ResolveInfo):
        asset_node = self._external_repository.get_external_asset_node(self._asset_key)
        if not asset_node and self._depended_by_loader:
            # Only load from dependency loader if asset node cannot be found in current repository
            asset_node = self._depended_by_loader.get_sink_asset(self._asset_key)
        asset_node = check.not_none(asset_node)
        return GrapheneAssetNode(
            self._repository_location,
            self._external_repository,
            asset_node,
            self._latest_materialization_loader,
        )


class GrapheneAssetLatestInfo(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)
    latestMaterialization = graphene.Field(GrapheneMaterializationEvent)
    unstartedRunIds = non_null_list(graphene.String)
    inProgressRunIds = non_null_list(graphene.String)
    latestRun = graphene.Field(GrapheneRun)

    class Meta:
        name = "AssetLatestInfo"


class GrapheneAssetNodeDefinitionCollision(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)
    repositories = non_null_list(lambda: external.GrapheneRepository)

    class Meta:
        name = "AssetNodeDefinitionCollision"


class GrapheneMaterializationUpstreamDataVersion(graphene.ObjectType):
    assetKey = graphene.NonNull(GrapheneAssetKey)
    downstreamAssetKey = graphene.NonNull(GrapheneAssetKey)
    timestamp = graphene.NonNull(graphene.String)

    class Meta:
        name = "MaterializationUpstreamDataVersion"


class GrapheneAssetNode(graphene.ObjectType):
    _depended_by_loader: Optional[CrossRepoAssetDependedByLoader]
    _external_asset_node: ExternalAssetNode
    _node_definition_snap: Optional[Union[GraphDefSnap, OpDefSnap]]
    _external_job: Optional[ExternalJob]
    _external_repository: ExternalRepository
    _latest_materialization_loader: Optional[BatchMaterializationLoader]
    _stale_status_loader: Optional[StaleStatusLoader]

    # NOTE: properties/resolvers are listed alphabetically
    assetKey = graphene.NonNull(GrapheneAssetKey)
    assetMaterializations = graphene.Field(
        non_null_list(GrapheneMaterializationEvent),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
        beforeTimestampMillis=graphene.String(),
        limit=graphene.Int(),
    )
    assetMaterializationUsedData = graphene.Field(
        non_null_list(GrapheneMaterializationUpstreamDataVersion),
        timestampMillis=graphene.NonNull(graphene.String),
    )
    assetObservations = graphene.Field(
        non_null_list(GrapheneObservationEvent),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
        beforeTimestampMillis=graphene.String(),
        limit=graphene.Int(),
    )
    computeKind = graphene.String()
    configField = graphene.Field(GrapheneConfigTypeField)
    currentDataVersion = graphene.String()
    dependedBy = non_null_list(GrapheneAssetDependency)
    dependedByKeys = non_null_list(GrapheneAssetKey)
    dependencies = non_null_list(GrapheneAssetDependency)
    dependencyKeys = non_null_list(GrapheneAssetKey)
    description = graphene.String()
    freshnessInfo = graphene.Field(GrapheneAssetFreshnessInfo)
    freshnessPolicy = graphene.Field(GrapheneFreshnessPolicy)
    autoMaterializePolicy = graphene.Field(GrapheneAutoMaterializePolicy)
    graphName = graphene.String()
    groupName = graphene.String()
    id = graphene.NonNull(graphene.ID)
    isObservable = graphene.NonNull(graphene.Boolean)
    isPartitioned = graphene.NonNull(graphene.Boolean)
    isSource = graphene.NonNull(graphene.Boolean)
    jobNames = non_null_list(graphene.String)
    jobs = non_null_list(GraphenePipeline)
    latestMaterializationByPartition = graphene.Field(
        graphene.NonNull(graphene.List(GrapheneMaterializationEvent)),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
    )
    latestRunForPartition = graphene.Field(GrapheneRun, partition=graphene.NonNull(graphene.String))
    assetPartitionStatuses = graphene.NonNull(GrapheneAssetPartitionStatuses)
    partitionStats = graphene.Field(GraphenePartitionStats)
    metadata_entries = non_null_list(GrapheneMetadataEntry)
    op = graphene.Field(GrapheneSolidDefinition)
    opName = graphene.String()
    opNames = non_null_list(graphene.String)
    opVersion = graphene.String()
    partitionDefinition = graphene.Field(GraphenePartitionDefinition)
    partitionKeys = non_null_list(graphene.String)
    partitionKeysByDimension = graphene.Field(
        non_null_list(GrapheneDimensionPartitionKeys),
        startIdx=graphene.Int(),
        endIdx=graphene.Int(),
    )
    repository = graphene.NonNull(lambda: external.GrapheneRepository)
    required_resources = non_null_list(GrapheneResourceRequirement)
    staleStatus = graphene.Field(GrapheneAssetStaleStatus)
    staleCauses = non_null_list(GrapheneAssetStaleCause)
    type = graphene.Field(GrapheneDagsterType)
    hasMaterializePermission = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "AssetNode"

    def __init__(
        self,
        repository_location: CodeLocation,
        external_repository: ExternalRepository,
        external_asset_node: ExternalAssetNode,
        materialization_loader: Optional[BatchMaterializationLoader] = None,
        depended_by_loader: Optional[CrossRepoAssetDependedByLoader] = None,
        stale_status_loader: Optional[StaleStatusLoader] = None,
        dynamic_partitions_loader: Optional[CachingDynamicPartitionsLoader] = None,
    ):
        from ..implementation.fetch_assets import get_unique_asset_id

        self._repository_location = check.inst_param(
            repository_location,
            "repository_location",
            CodeLocation,
        )
        self._external_repository = check.inst_param(
            external_repository, "external_repository", ExternalRepository
        )
        self._external_asset_node = check.inst_param(
            external_asset_node, "external_asset_node", ExternalAssetNode
        )
        self._latest_materialization_loader = check.opt_inst_param(
            materialization_loader, "materialization_loader", BatchMaterializationLoader
        )
        self._depended_by_loader = check.opt_inst_param(
            depended_by_loader, "depended_by_loader", CrossRepoAssetDependedByLoader
        )
        self._stale_status_loader = check.opt_inst_param(
            stale_status_loader,
            "stale_status_loader",
            StaleStatusLoader,
        )
        self._dynamic_partitions_loader = check.opt_inst_param(
            dynamic_partitions_loader, "dynamic_partitions_loader", CachingDynamicPartitionsLoader
        )
        self._external_job = None  # lazily loaded
        self._node_definition_snap = None  # lazily loaded

        super().__init__(
            id=get_unique_asset_id(
                external_asset_node.asset_key, repository_location.name, external_repository.name
            ),
            assetKey=external_asset_node.asset_key,
            description=external_asset_node.op_description,
            opName=external_asset_node.op_name,
            opVersion=external_asset_node.code_version,
            groupName=external_asset_node.group_name,
        )

    @property
    def repository_location(self) -> CodeLocation:
        return self._repository_location

    @property
    def external_repository(self) -> ExternalRepository:
        return self._external_repository

    @property
    def external_asset_node(self) -> ExternalAssetNode:
        return self._external_asset_node

    @property
    def stale_status_loader(self) -> StaleStatusLoader:
        loader = check.not_none(
            self._stale_status_loader,
            "stale_status_loader must exist in order to access data versioning information",
        )
        return loader

    def get_external_job(self) -> ExternalJob:
        if self._external_job is None:
            check.invariant(
                len(self._external_asset_node.job_names) >= 1,
                "Asset must be part of at least one job",
            )
            self._external_job = self._external_repository.get_full_external_job(
                self._external_asset_node.job_names[0]
            )
        return self._external_job

    def get_node_definition_snap(
        self,
    ) -> Union[GraphDefSnap, OpDefSnap]:
        if self._node_definition_snap is None and len(self._external_asset_node.job_names) > 0:
            node_key = check.not_none(
                self._external_asset_node.node_definition_name
                # nodes serialized using an older Dagster version may not have node_definition_name
                or self._external_asset_node.graph_name
                or self._external_asset_node.op_name
            )
            self._node_definition_snap = self.get_external_job().get_node_def_snap(node_key)
        # weird mypy bug causes mistyped _node_definition_snap
        return check.not_none(self._node_definition_snap)

    def get_partition_keys(
        self,
        partitions_def_data: Optional[ExternalPartitionsDefinitionData] = None,
        start_idx: Optional[int] = None,
        end_idx: Optional[int] = None,
    ) -> Sequence[str]:
        # TODO: Add functionality for dynamic partitions definition
        # Accepts an optional start_idx and end_idx to fetch a subset of time window partition keys

        check.opt_inst_param(
            partitions_def_data, "partitions_def_data", ExternalPartitionsDefinitionData
        )
        check.opt_int_param(start_idx, "start_idx")
        check.opt_int_param(end_idx, "end_idx")

        if not self._dynamic_partitions_loader:
            check.failed("dynamic_partitions_loader must be provided to get partition keys")

        partitions_def_data = (
            self._external_asset_node.partitions_def_data
            if not partitions_def_data
            else partitions_def_data
        )
        if partitions_def_data:
            if isinstance(
                partitions_def_data,
                (
                    ExternalStaticPartitionsDefinitionData,
                    ExternalTimeWindowPartitionsDefinitionData,
                    ExternalMultiPartitionsDefinitionData,
                ),
            ):
                if (
                    start_idx
                    and end_idx
                    and isinstance(partitions_def_data, ExternalTimeWindowPartitionsDefinitionData)
                ):
                    return partitions_def_data.get_partitions_definition().get_partition_keys_between_indexes(
                        start_idx, end_idx
                    )
                else:
                    return partitions_def_data.get_partitions_definition().get_partition_keys(
                        dynamic_partitions_store=self._dynamic_partitions_loader
                    )
            elif isinstance(partitions_def_data, ExternalDynamicPartitionsDefinitionData):
                return self._dynamic_partitions_loader.get_dynamic_partitions(
                    partitions_def_name=partitions_def_data.name
                )
            else:
                raise DagsterInvariantViolationError(
                    f"Unsupported partition definition type {partitions_def_data}"
                )
        return []

    def is_multipartitioned(self) -> bool:
        external_multipartitions_def = self._external_asset_node.partitions_def_data

        return external_multipartitions_def is not None and isinstance(
            external_multipartitions_def, ExternalMultiPartitionsDefinitionData
        )

    def get_required_resource_keys(
        self, node_def_snap: Union[GraphDefSnap, OpDefSnap]
    ) -> Sequence[str]:
        all_keys = self.get_required_resource_keys_rec(node_def_snap)
        return list(set(all_keys))

    def get_required_resource_keys_rec(
        self, node_def_snap: Union[GraphDefSnap, OpDefSnap]
    ) -> Sequence[str]:
        if isinstance(node_def_snap, GraphDefSnap):
            constituent_node_names = [
                inv.node_def_name
                for inv in node_def_snap.dep_structure_snapshot.node_invocation_snaps
            ]
            external_pipeline = self.get_external_job()
            constituent_resource_key_sets = [
                self.get_required_resource_keys_rec(external_pipeline.get_node_def_snap(name))
                for name in constituent_node_names
            ]
            return [key for res_key_set in constituent_resource_key_sets for key in res_key_set]
        else:
            return node_def_snap.required_resource_keys

    def is_graph_backed_asset(self) -> bool:
        return self.graphName is not None

    def is_source_asset(self) -> bool:
        return self._external_asset_node.is_source

    def resolve_hasMaterializePermission(
        self,
        graphene_info: ResolveInfo,
    ) -> bool:
        return graphene_info.context.has_permission_for_location(
            Permissions.LAUNCH_PIPELINE_EXECUTION, self._repository_location.name
        )

    def resolve_assetMaterializationUsedData(
        self,
        graphene_info: ResolveInfo,
        timestampMillis: str,
    ) -> Sequence[GrapheneMaterializationUpstreamDataVersion]:
        if not timestampMillis:
            return []

        instance = graphene_info.context.instance
        asset_graph = ExternalAssetGraph.from_external_repository(self._external_repository)
        asset_key = self._external_asset_node.asset_key

        # in the future, we can share this same CachingInstanceQueryer across all
        # GrapheneMaterializationEvent which share an external repository for improved performance
        instance_queryer = CachingInstanceQueryer(instance=graphene_info.context.instance)
        data_time_resolver = CachingDataTimeResolver(
            instance_queryer=instance_queryer, asset_graph=asset_graph
        )
        event_records = instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                before_timestamp=int(timestampMillis) / 1000.0 + 1,
                after_timestamp=int(timestampMillis) / 1000.0 - 1,
                asset_key=asset_key,
            ),
            limit=1,
        )

        if not event_records:
            return []

        if not asset_graph.has_non_source_parents(asset_key):
            return []

        used_data_times = data_time_resolver.get_data_time_by_key_for_record(
            record=next(iter(event_records)),
        )

        return [
            GrapheneMaterializationUpstreamDataVersion(
                assetKey=used_asset_key,
                downstreamAssetKey=asset_key,
                timestamp=int(materialization_time.timestamp() * 1000),
            )
            for used_asset_key, materialization_time in used_data_times.items()
            if materialization_time
        ]

    def resolve_assetMaterializations(
        self,
        graphene_info: ResolveInfo,
        partitions: Optional[Sequence[str]] = None,
        beforeTimestampMillis: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[GrapheneMaterializationEvent]:
        try:
            before_timestamp = (
                int(beforeTimestampMillis) / 1000.0 if beforeTimestampMillis else None
            )
        except ValueError:
            before_timestamp = None

        if (
            self._latest_materialization_loader
            and limit == 1
            and not partitions
            and not before_timestamp
        ):
            latest_materialization_event = (
                self._latest_materialization_loader.get_latest_materialization_for_asset_key(
                    self._external_asset_node.asset_key
                )
            )

            if not latest_materialization_event:
                return []

            return [GrapheneMaterializationEvent(event=latest_materialization_event)]

        return [
            GrapheneMaterializationEvent(event=event)
            for event in get_asset_materializations(
                graphene_info,
                self._external_asset_node.asset_key,
                partitions,
                before_timestamp=before_timestamp,
                limit=limit,
            )
        ]

    def resolve_assetObservations(
        self,
        graphene_info: ResolveInfo,
        partitions: Optional[Sequence[str]] = None,
        beforeTimestampMillis: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[GrapheneObservationEvent]:
        try:
            before_timestamp = (
                int(beforeTimestampMillis) / 1000.0 if beforeTimestampMillis else None
            )
        except ValueError:
            before_timestamp = None
        return [
            GrapheneObservationEvent(event=event)
            for event in get_asset_observations(
                graphene_info,
                self._external_asset_node.asset_key,
                partitions,
                before_timestamp=before_timestamp,
                limit=limit,
            )
        ]

    def resolve_configField(self, _graphene_info: ResolveInfo) -> Optional[GrapheneConfigTypeField]:
        if self.is_source_asset():
            return None
        external_pipeline = self.get_external_job()
        node_def_snap = self.get_node_definition_snap()
        return (
            GrapheneConfigTypeField(
                config_schema_snapshot=external_pipeline.config_schema_snapshot,
                field_snap=node_def_snap.config_field_snap,
            )
            if node_def_snap.config_field_snap
            else None
        )

    def resolve_computeKind(self, _graphene_info: ResolveInfo) -> Optional[str]:
        return self._external_asset_node.compute_kind

    def resolve_staleStatus(self, graphene_info: ResolveInfo) -> Any:  # (GrapheneAssetStaleStatus)
        return self.stale_status_loader.get_status(self._external_asset_node.asset_key)

    def resolve_staleCauses(self, graphene_info: ResolveInfo) -> Sequence[GrapheneAssetStaleCause]:
        causes = self.stale_status_loader.get_stale_root_causes(self._external_asset_node.asset_key)
        return [
            GrapheneAssetStaleCause(
                GrapheneAssetKey(path=cause.key.path),
                cause.category,
                cause.reason,
                GrapheneAssetKey(path=cause.dependency.path) if cause.dependency else None,
            )
            for cause in causes
        ]

    def resolve_currentDataVersion(self, graphene_info: ResolveInfo) -> Optional[str]:
        version = self.stale_status_loader.get_current_data_version(
            self._external_asset_node.asset_key
        )
        return None if version == NULL_DATA_VERSION else version.value

    def resolve_dependedBy(self, graphene_info: ResolveInfo) -> List[GrapheneAssetDependency]:
        # CrossRepoAssetDependedByLoader class loads cross-repo asset dependencies workspace-wide.
        # In order to avoid recomputing workspace-wide values per asset node, we add a loader
        # that batch loads all cross-repo dependencies for the whole workspace.
        _depended_by_loader = check.not_none(
            self._depended_by_loader,
            "depended_by_loader must exist in order to resolve dependedBy nodes",
        )

        depended_by_asset_nodes = [
            *_depended_by_loader.get_cross_repo_dependent_assets(
                self._repository_location.name,
                self._external_repository.name,
                self._external_asset_node.asset_key,
            ),
            *self._external_asset_node.depended_by,
        ]

        if not depended_by_asset_nodes:
            return []

        materialization_loader = BatchMaterializationLoader(
            instance=graphene_info.context.instance,
            asset_keys=[dep.downstream_asset_key for dep in depended_by_asset_nodes],
        )

        return [
            GrapheneAssetDependency(
                repository_location=self._repository_location,
                external_repository=self._external_repository,
                input_name=dep.input_name,
                asset_key=dep.downstream_asset_key,
                materialization_loader=materialization_loader,
                depended_by_loader=_depended_by_loader,
            )
            for dep in depended_by_asset_nodes
        ]

    def resolve_dependedByKeys(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneAssetKey]:
        # CrossRepoAssetDependedByLoader class loads all cross-repo asset dependencies workspace-wide.
        # In order to avoid recomputing workspace-wide values per asset node, we add a loader
        # that batch loads all cross-repo dependencies for the whole workspace.
        depended_by_loader = check.not_none(
            self._depended_by_loader,
            "depended_by_loader must exist in order to resolve dependedBy nodes",
        )

        depended_by_asset_nodes = [
            *depended_by_loader.get_cross_repo_dependent_assets(
                self._repository_location.name,
                self._external_repository.name,
                self._external_asset_node.asset_key,
            ),
            *self._external_asset_node.depended_by,
        ]

        return [
            GrapheneAssetKey(path=dep.downstream_asset_key.path) for dep in depended_by_asset_nodes
        ]

    def resolve_dependencyKeys(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneAssetKey]:
        return [
            GrapheneAssetKey(path=dep.upstream_asset_key.path)
            for dep in self._external_asset_node.dependencies
        ]

    def resolve_dependencies(self, graphene_info: ResolveInfo) -> Sequence[GrapheneAssetDependency]:
        if not self._external_asset_node.dependencies:
            return []

        materialization_loader = BatchMaterializationLoader(
            instance=graphene_info.context.instance,
            asset_keys=[dep.upstream_asset_key for dep in self._external_asset_node.dependencies],
        )
        return [
            GrapheneAssetDependency(
                repository_location=self._repository_location,
                external_repository=self._external_repository,
                input_name=dep.input_name,
                asset_key=dep.upstream_asset_key,
                materialization_loader=materialization_loader,
            )
            for dep in self._external_asset_node.dependencies
        ]

    def resolve_freshnessInfo(
        self, graphene_info: ResolveInfo
    ) -> Optional[GrapheneAssetFreshnessInfo]:
        if self._external_asset_node.freshness_policy:
            asset_graph = ExternalAssetGraph.from_external_repository(self._external_repository)
            return get_freshness_info(
                asset_key=self._external_asset_node.asset_key,
                # in the future, we can share this same CachingInstanceQueryer across all
                # GrapheneAssetNodes which share an external repository for improved performance
                data_time_resolver=CachingDataTimeResolver(
                    instance_queryer=CachingInstanceQueryer(
                        instance=graphene_info.context.instance
                    ),
                    asset_graph=asset_graph,
                ),
            )
        return None

    def resolve_freshnessPolicy(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GrapheneFreshnessPolicy]:
        if self._external_asset_node.freshness_policy:
            return GrapheneFreshnessPolicy(self._external_asset_node.freshness_policy)
        return None

    def resolve_autoMaterializePolicy(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GrapheneAutoMaterializePolicy]:
        if self._external_asset_node.auto_materialize_policy:
            return GrapheneAutoMaterializePolicy(self._external_asset_node.auto_materialize_policy)
        return None

    def resolve_jobNames(self, _graphene_info: ResolveInfo) -> Sequence[str]:
        return self._external_asset_node.job_names

    def resolve_jobs(self, _graphene_info: ResolveInfo) -> Sequence[GraphenePipeline]:
        job_names = self._external_asset_node.job_names or []
        return [
            GraphenePipeline(self._external_repository.get_full_external_job(job_name))
            for job_name in job_names
            if self._external_repository.has_external_job(job_name)
        ]

    def resolve_isSource(self, _graphene_info: ResolveInfo) -> bool:
        return self.is_source_asset()

    def resolve_isPartitioned(self, _graphene_info: ResolveInfo) -> bool:
        return self._external_asset_node.partitions_def_data is not None

    def resolve_isObservable(self, _graphene_info: ResolveInfo) -> bool:
        return self._external_asset_node.is_observable

    def resolve_latestMaterializationByPartition(
        self,
        graphene_info: ResolveInfo,
        partitions: Optional[Sequence[str]] = None,
    ) -> Sequence[Optional[GrapheneMaterializationEvent]]:
        get_partition = (
            lambda event: event.dagster_event.step_materialization_data.materialization.partition
        )

        partitions = partitions or self.get_partition_keys()

        events_for_partitions = get_asset_materializations(
            graphene_info,
            self._external_asset_node.asset_key,
            partitions,
        )

        latest_materialization_by_partition = {}
        for event in events_for_partitions:  # events are sorted in order of newest to oldest
            event_partition = get_partition(event)
            if event_partition not in latest_materialization_by_partition:
                latest_materialization_by_partition[event_partition] = event
            if len(latest_materialization_by_partition) == len(partitions):
                break

        # return materializations in the same order as the provided partitions, None if
        # materialization does not exist
        ordered_materializations = [
            latest_materialization_by_partition.get(partition) for partition in partitions
        ]

        return [
            GrapheneMaterializationEvent(event=event) if event else None
            for event in ordered_materializations
        ]

    def resolve_latestRunForPartition(
        self,
        graphene_info: ResolveInfo,
        partition: str,
    ) -> Optional[GrapheneRun]:
        event_records = list(
            graphene_info.context.instance.event_log_storage.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                    asset_key=self._external_asset_node.asset_key,
                    asset_partitions=[partition],
                ),
                limit=1,
            )
        )
        if not event_records:
            return None
        run_record = graphene_info.context.instance.get_run_record_by_id(event_records[0].run_id)
        return GrapheneRun(run_record) if run_record else None

    def resolve_assetPartitionStatuses(
        self, graphene_info: ResolveInfo
    ) -> Union["GrapheneTimePartitions", "GrapheneDefaultPartitions", "GrapheneMultiPartitions"]:
        asset_key = self._external_asset_node.asset_key

        if not self._dynamic_partitions_loader:
            check.failed("dynamic_partitions_loader must be provided to get partition keys")

        (
            materialized_partition_subset,
            failed_partition_subset,
            in_progress_subset,
        ) = get_partition_subsets(
            graphene_info.context.instance,
            asset_key,
            self._dynamic_partitions_loader,
            self._external_asset_node.partitions_def_data.get_partitions_definition()
            if self._external_asset_node.partitions_def_data
            else None,
        )

        return build_partition_statuses(
            self._dynamic_partitions_loader,
            materialized_partition_subset,
            failed_partition_subset,
            in_progress_subset,
        )

    def resolve_partitionStats(
        self, graphene_info: ResolveInfo
    ) -> Optional[GraphenePartitionStats]:
        partitions_def_data = self._external_asset_node.partitions_def_data
        if partitions_def_data:
            asset_key = self._external_asset_node.asset_key

            if not self._dynamic_partitions_loader:
                check.failed("dynamic_partitions_loader must be provided to get partition keys")

            (
                materialized_partition_subset,
                failed_partition_subset,
                in_progress_subset,
            ) = get_partition_subsets(
                graphene_info.context.instance,
                asset_key,
                self._dynamic_partitions_loader,
                self._external_asset_node.partitions_def_data.get_partitions_definition()
                if self._external_asset_node.partitions_def_data
                else None,
            )

            if (
                materialized_partition_subset is None
                or failed_partition_subset is None
                or in_progress_subset is None
            ):
                check.failed("Expected partitions subset for a partitioned asset")

            num_materialized = len(materialized_partition_subset)
            num_materialized_and_not_failed = num_materialized - len(
                [
                    k
                    for k in failed_partition_subset.get_partition_keys()
                    if k in materialized_partition_subset
                ]
            )
            num_materialized_and_not_failed_or_in_progress = num_materialized_and_not_failed - len(
                [
                    k
                    for k in in_progress_subset.get_partition_keys()
                    if k in materialized_partition_subset
                ]
            )

            return GraphenePartitionStats(
                numMaterialized=num_materialized_and_not_failed_or_in_progress,
                numPartitions=partitions_def_data.get_partitions_definition().get_num_partitions(
                    dynamic_partitions_store=self._dynamic_partitions_loader
                ),
                numFailed=len(failed_partition_subset),
                numMaterializing=len(in_progress_subset),
            )
        else:
            return None

    def resolve_metadata_entries(
        self, _graphene_info: ResolveInfo
    ) -> Sequence[GrapheneMetadataEntry]:
        return list(iterate_metadata_entries(self._external_asset_node.metadata))

    def resolve_op(
        self, _graphene_info: ResolveInfo
    ) -> Optional[Union[GrapheneSolidDefinition, GrapheneCompositeSolidDefinition]]:
        if self.is_source_asset():
            return None
        external_pipeline = self.get_external_job()
        node_def_snap = self.get_node_definition_snap()
        if isinstance(node_def_snap, OpDefSnap):
            return GrapheneSolidDefinition(external_pipeline, node_def_snap.name)

        if isinstance(node_def_snap, GraphDefSnap):
            return GrapheneCompositeSolidDefinition(external_pipeline, node_def_snap.name)

        check.failed(f"Unknown solid definition type {type(node_def_snap)}")

    def resolve_opNames(self, _graphene_info: ResolveInfo) -> Sequence[str]:
        return self._external_asset_node.op_names or []

    def resolve_graphName(self, _graphene_info: ResolveInfo) -> Optional[str]:
        return self._external_asset_node.graph_name

    def resolve_partitionKeysByDimension(
        self,
        _graphene_info: ResolveInfo,
        startIdx: Optional[int] = None,
        endIdx: Optional[int] = None,
    ) -> Sequence[GrapheneDimensionPartitionKeys]:
        # Accepts startIdx and endIdx arguments. This will be used to select a range of
        # time partitions. StartIdx is inclusive, endIdx is exclusive.
        # For non time partition definitions, these arguments will be ignored
        # and the full list of partition keys will be returned.
        if not self._external_asset_node.partitions_def_data:
            return []

        if self.is_multipartitioned():
            return [
                GrapheneDimensionPartitionKeys(
                    name=dimension.name,
                    partition_keys=self.get_partition_keys(
                        dimension.external_partitions_def_data,
                        startIdx,
                        endIdx,
                    ),
                    type=GraphenePartitionDefinitionType.from_partition_def_data(
                        dimension.external_partitions_def_data
                    ),
                )
                for dimension in cast(
                    ExternalMultiPartitionsDefinitionData,
                    self._external_asset_node.partitions_def_data,
                ).external_partition_dimension_definitions
            ]

        return [
            GrapheneDimensionPartitionKeys(
                name="default",
                type=GraphenePartitionDefinitionType.from_partition_def_data(
                    self._external_asset_node.partitions_def_data
                ),
                partition_keys=self.get_partition_keys(start_idx=startIdx, end_idx=endIdx),
            )
        ]

    def resolve_partitionKeys(self, _graphene_info: ResolveInfo) -> Sequence[str]:
        return self.get_partition_keys()

    def resolve_partitionDefinition(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GraphenePartitionDefinition]:
        partitions_def_data = self._external_asset_node.partitions_def_data
        if partitions_def_data:
            return GraphenePartitionDefinition(partitions_def_data)
        return None

    def resolve_repository(self, graphene_info: ResolveInfo) -> "GrapheneRepository":
        return external.GrapheneRepository(
            graphene_info.context.instance, self._external_repository, self._repository_location
        )

    def resolve_required_resources(
        self, _graphene_info: ResolveInfo
    ) -> Sequence[GrapheneResourceRequirement]:
        if self.is_source_asset():
            return []
        node_def_snap = self.get_node_definition_snap()
        all_unique_keys = self.get_required_resource_keys(node_def_snap)
        return [GrapheneResourceRequirement(key) for key in all_unique_keys]

    def resolve_type(
        self, _graphene_info: ResolveInfo
    ) -> Optional[
        Union[
            "GrapheneListDagsterType", "GrapheneNullableDagsterType", "GrapheneRegularDagsterType"
        ]
    ]:
        if self.is_source_asset():
            return None
        external_pipeline = self.get_external_job()
        output_name = self.external_asset_node.output_name
        if output_name:
            for output_def in self.get_node_definition_snap().output_def_snaps:
                if output_def.name == output_name:
                    return to_dagster_type(
                        external_pipeline.job_snapshot,
                        output_def.dagster_type_key,
                    )
        return None


class GrapheneAssetGroup(graphene.ObjectType):
    groupName = graphene.NonNull(graphene.String)
    assetKeys = non_null_list(GrapheneAssetKey)

    class Meta:
        name = "AssetGroup"


class GrapheneAssetNodeOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetNode, GrapheneAssetNotFoundError)
        name = "AssetNodeOrError"
