from typing import TYPE_CHECKING, Any, List, Optional, Sequence, Set, Union, cast

import graphene
from dagster import (
    AssetKey,
    _check as check,
)
from dagster._core.definitions.asset_graph_differ import AssetGraphDiffer, ChangeReason
from dagster._core.definitions.assets_job import ASSET_BASE_JOB_PREFIX
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.data_version import (
    NULL_DATA_VERSION,
    StaleCauseCategory,
    StaleStatus,
)
from dagster._core.definitions.partition import CachingDynamicPartitionsLoader, PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
from dagster._core.definitions.sensor_definition import (
    SensorType,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.remote_representation import CodeLocation, ExternalRepository
from dagster._core.remote_representation.external import ExternalJob, ExternalSensor
from dagster._core.remote_representation.external_data import (
    ExternalAssetNode,
    ExternalDynamicPartitionsDefinitionData,
    ExternalMultiPartitionsDefinitionData,
    ExternalPartitionsDefinitionData,
    ExternalStaticPartitionsDefinitionData,
    ExternalTimeWindowPartitionsDefinitionData,
)
from dagster._core.snap.node import GraphDefSnap, OpDefSnap
from dagster._core.utils import is_valid_email
from dagster._core.workspace.permissions import Permissions
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from dagster_graphql.implementation.asset_checks_loader import AssetChecksLoader
from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.implementation.fetch_asset_checks import has_asset_checks
from dagster_graphql.implementation.fetch_assets import (
    get_asset_materializations,
    get_asset_observations,
)
from dagster_graphql.implementation.loader import BatchRunLoader
from dagster_graphql.schema.config_types import GrapheneConfigTypeField
from dagster_graphql.schema.inputs import GraphenePipelineSelector
from dagster_graphql.schema.instigators import GrapheneInstigator
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.partition_sets import (
    GrapheneDimensionPartitionKeys,
    GraphenePartitionDefinition,
    GraphenePartitionDefinitionType,
)
from dagster_graphql.schema.schedules import GrapheneSchedule
from dagster_graphql.schema.sensors import GrapheneSensor
from dagster_graphql.schema.solids import (
    GrapheneCompositeSolidDefinition,
    GrapheneResourceRequirement,
    GrapheneSolidDefinition,
)
from dagster_graphql.schema.tags import GrapheneDefinitionTag

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
from ..schema.asset_checks import (
    AssetChecksOrErrorUnion,
    GrapheneAssetChecksOrError,
)
from . import external
from .asset_key import GrapheneAssetKey
from .auto_materialize_policy import GrapheneAutoMaterializePolicy
from .backfill import GrapheneBackfillPolicy
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
from .partition_mappings import GraphenePartitionMapping
from .pipelines.pipeline import (
    GrapheneAssetPartitionStatuses,
    GrapheneDefaultPartitionStatuses,
    GrapheneMultiPartitionStatuses,
    GraphenePartitionStats,
    GraphenePipeline,
    GrapheneRun,
    GrapheneTimePartitionStatuses,
)
from .util import ResolveInfo, non_null_list

if TYPE_CHECKING:
    from .external import GrapheneRepository

GrapheneAssetStaleStatus = graphene.Enum.from_enum(StaleStatus, name="StaleStatus")
GrapheneAssetStaleCauseCategory = graphene.Enum.from_enum(
    StaleCauseCategory, name="StaleCauseCategory"
)

GrapheneAssetChangedReason = graphene.Enum.from_enum(ChangeReason, name="ChangeReason")


class GrapheneUserAssetOwner(graphene.ObjectType):
    class Meta:
        name = "UserAssetOwner"

    email = graphene.NonNull(graphene.String)


class GrapheneTeamAssetOwner(graphene.ObjectType):
    class Meta:
        name = "TeamAssetOwner"

    team = graphene.NonNull(graphene.String)


class GrapheneAssetOwner(graphene.Union):
    class Meta:
        types = (
            GrapheneUserAssetOwner,
            GrapheneTeamAssetOwner,
        )
        name = "AssetOwner"


class GrapheneAssetStaleCause(graphene.ObjectType):
    key = graphene.NonNull(GrapheneAssetKey)
    partition_key = graphene.String()
    category = graphene.NonNull(GrapheneAssetStaleCauseCategory)
    reason = graphene.NonNull(graphene.String)
    dependency = graphene.Field(GrapheneAssetKey)
    dependency_partition_key = graphene.String()

    class Meta:
        name = "StaleCause"


class GrapheneAssetDependency(graphene.ObjectType):
    class Meta:
        name = "AssetDependency"

    asset = graphene.NonNull("dagster_graphql.schema.asset_graph.GrapheneAssetNode")
    inputName = graphene.NonNull(graphene.String)
    partitionMapping = graphene.Field(GraphenePartitionMapping)

    def __init__(
        self,
        repository_location: CodeLocation,
        external_repository: ExternalRepository,
        input_name: Optional[str],
        asset_key: AssetKey,
        asset_checks_loader: AssetChecksLoader,
        materialization_loader: Optional[BatchMaterializationLoader] = None,
        depended_by_loader: Optional[CrossRepoAssetDependedByLoader] = None,
        partition_mapping: Optional[PartitionMapping] = None,
    ):
        self._repository_location = check.inst_param(
            repository_location, "repository_location", CodeLocation
        )
        self._external_repository = check.inst_param(
            external_repository, "external_repository", ExternalRepository
        )
        self._asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        self._asset_checks_loader = check.inst_param(
            asset_checks_loader, "asset_checks_loader", AssetChecksLoader
        )
        self._latest_materialization_loader = check.opt_inst_param(
            materialization_loader, "materialization_loader", BatchMaterializationLoader
        )
        self._depended_by_loader = check.opt_inst_param(
            depended_by_loader, "depended_by_loader", CrossRepoAssetDependedByLoader
        )
        self._partition_mapping = check.opt_inst_param(
            partition_mapping, "partition_mapping", PartitionMapping
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
            asset_checks_loader=self._asset_checks_loader,
            materialization_loader=self._latest_materialization_loader,
        )

    def resolve_partitionMapping(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GraphenePartitionMapping]:
        if self._partition_mapping:
            return GraphenePartitionMapping(self._partition_mapping)
        return None


class GrapheneAssetLatestInfo(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
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
    _asset_checks_loader: AssetChecksLoader
    _asset_graph_differ: Optional[AssetGraphDiffer]

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
    backfillPolicy = graphene.Field(GrapheneBackfillPolicy)
    changedReasons = graphene.Field(non_null_list(GrapheneAssetChangedReason))
    computeKind = graphene.String()
    configField = graphene.Field(GrapheneConfigTypeField)
    dataVersion = graphene.Field(graphene.String(), partition=graphene.String())
    dataVersionByPartition = graphene.Field(
        graphene.NonNull(graphene.List(graphene.String)),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
    )
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
    owners = non_null_list(GrapheneAssetOwner)
    id = graphene.NonNull(graphene.ID)
    isExecutable = graphene.NonNull(graphene.Boolean)
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
    tags = non_null_list(GrapheneDefinitionTag)
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
    staleStatus = graphene.Field(GrapheneAssetStaleStatus, partition=graphene.String())
    staleStatusByPartition = graphene.Field(
        non_null_list(GrapheneAssetStaleStatus),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
    )
    staleCauses = graphene.Field(
        non_null_list(GrapheneAssetStaleCause), partition=graphene.String()
    )
    staleCausesByPartition = graphene.Field(
        graphene.List((non_null_list(GrapheneAssetStaleCause))),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
    )
    type = graphene.Field(GrapheneDagsterType)
    hasMaterializePermission = graphene.NonNull(graphene.Boolean)
    # the acutal checks are listed in the assetChecksOrError resolver. We use this boolean
    # to show/hide the checks tab. We plan to remove this field once we always show the checks tab.
    hasAssetChecks = graphene.NonNull(graphene.Boolean)
    assetChecksOrError = graphene.Field(
        graphene.NonNull(GrapheneAssetChecksOrError),
        limit=graphene.Argument(graphene.Int),
        pipeline=graphene.Argument(GraphenePipelineSelector),
    )
    currentAutoMaterializeEvaluationId = graphene.Int()
    targetingInstigators = non_null_list(GrapheneInstigator)

    class Meta:
        name = "AssetNode"

    def __init__(
        self,
        repository_location: CodeLocation,
        external_repository: ExternalRepository,
        external_asset_node: ExternalAssetNode,
        asset_checks_loader: AssetChecksLoader,
        materialization_loader: Optional[BatchMaterializationLoader] = None,
        depended_by_loader: Optional[CrossRepoAssetDependedByLoader] = None,
        stale_status_loader: Optional[StaleStatusLoader] = None,
        dynamic_partitions_loader: Optional[CachingDynamicPartitionsLoader] = None,
        asset_graph_differ: Optional[AssetGraphDiffer] = None,
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
        self._asset_checks_loader = check.inst_param(
            asset_checks_loader, "asset_checks_loader", AssetChecksLoader
        )
        self._asset_graph_differ = check.opt_inst_param(
            asset_graph_differ, "asset_graph_differ", AssetGraphDiffer
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
            owners=[
                GrapheneUserAssetOwner(email=owner)
                if is_valid_email(owner)
                else GrapheneTeamAssetOwner(team=owner)
                for owner in (external_asset_node.owners or [])
            ],
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

    @property
    def asset_graph_differ(self) -> Optional[AssetGraphDiffer]:
        return self._asset_graph_differ

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
        asset_graph = self._external_repository.asset_graph
        asset_key = self._external_asset_node.asset_key

        # in the future, we can share this same CachingInstanceQueryer across all
        # GrapheneMaterializationEvent which share an external repository for improved performance
        instance_queryer = CachingInstanceQueryer(
            instance=graphene_info.context.instance, asset_graph=asset_graph
        )
        data_time_resolver = CachingDataTimeResolver(instance_queryer=instance_queryer)
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

        if not asset_graph.has_materializable_parents(asset_key):
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

    def resolve_changedReasons(
        self, graphene_info: ResolveInfo
    ) -> Sequence[Any]:  # Sequence[GrapheneAssetChangedReason]
        if self.asset_graph_differ is None:
            # asset_graph_differ is None when not in a branch deployment
            return []
        return self.asset_graph_differ.get_changes_for_asset(self._external_asset_node.asset_key)

    def resolve_staleStatus(
        self, graphene_info: ResolveInfo, partition: Optional[str] = None
    ) -> Any:  # (GrapheneAssetStaleStatus)
        if partition:
            self._validate_partitions_existence()
        return self.stale_status_loader.get_status(self._external_asset_node.asset_key, partition)

    def resolve_staleStatusByPartition(
        self,
        graphene_info: ResolveInfo,
        partitions: Optional[Sequence[str]] = None,
    ) -> Sequence[Any]:  # (GrapheneAssetStaleStatus)
        if partitions is None:
            partitions = self._get_partitions_def().get_partition_keys()
        else:
            self._validate_partitions_existence()
        return [
            self.stale_status_loader.get_status(self._external_asset_node.asset_key, partition)
            for partition in partitions
        ]

    def resolve_staleCauses(
        self, graphene_info: ResolveInfo, partition: Optional[str] = None
    ) -> Sequence[GrapheneAssetStaleCause]:
        if partition:
            self._validate_partitions_existence()
        return self._get_staleCauses(partition)

    def resolve_staleCausesByPartition(
        self,
        graphene_info: ResolveInfo,
        partitions: Optional[Sequence[str]] = None,
    ) -> Sequence[Sequence[GrapheneAssetStaleCause]]:
        if partitions is None:
            partitions = self._get_partitions_def().get_partition_keys()
        else:
            self._validate_partitions_existence()
        return [self._get_staleCauses(partition) for partition in partitions]

    def _get_staleCauses(
        self, partition: Optional[str] = None
    ) -> Sequence[GrapheneAssetStaleCause]:
        causes = self.stale_status_loader.get_stale_root_causes(
            self._external_asset_node.asset_key, partition
        )
        return [
            GrapheneAssetStaleCause(
                GrapheneAssetKey(path=cause.asset_key.path),
                cause.partition_key,
                cause.category,
                cause.reason,
                (
                    GrapheneAssetKey(path=cause.dependency.asset_key.path)
                    if cause.dependency
                    else None
                ),
                cause.dependency_partition_key,
            )
            for cause in causes
        ]

    def resolve_dataVersion(
        self, graphene_info: ResolveInfo, partition: Optional[str] = None
    ) -> Optional[str]:
        if partition:
            self._validate_partitions_existence()
        version = self.stale_status_loader.get_current_data_version(
            self._external_asset_node.asset_key, partition
        )
        return None if version == NULL_DATA_VERSION else version.value

    def resolve_dataVersionByPartition(
        self, graphene_info: ResolveInfo, partitions: Optional[Sequence[str]] = None
    ) -> Sequence[Optional[str]]:
        if partitions is None:
            partitions = self._get_partitions_def().get_partition_keys()
        else:
            self._validate_partitions_existence()
        data_versions = [
            self.stale_status_loader.get_current_data_version(
                self._external_asset_node.asset_key, partition
            )
            for partition in partitions
        ]
        return [
            None if version == NULL_DATA_VERSION else version.value for version in data_versions
        ]

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
        asset_checks_loader = AssetChecksLoader(
            context=graphene_info.context,
            asset_keys=[dep.downstream_asset_key for dep in depended_by_asset_nodes],
        )

        return [
            GrapheneAssetDependency(
                repository_location=self._repository_location,
                external_repository=self._external_repository,
                input_name=dep.input_name,
                asset_key=dep.downstream_asset_key,
                asset_checks_loader=asset_checks_loader,
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
        asset_checks_loader = AssetChecksLoader(
            context=graphene_info.context,
            asset_keys=[dep.upstream_asset_key for dep in self._external_asset_node.dependencies],
        )
        return [
            GrapheneAssetDependency(
                repository_location=self._repository_location,
                external_repository=self._external_repository,
                input_name=dep.input_name,
                asset_key=dep.upstream_asset_key,
                materialization_loader=materialization_loader,
                asset_checks_loader=asset_checks_loader,
                partition_mapping=dep.partition_mapping,
            )
            for dep in self._external_asset_node.dependencies
        ]

    def resolve_freshnessInfo(
        self, graphene_info: ResolveInfo
    ) -> Optional[GrapheneAssetFreshnessInfo]:
        if self._external_asset_node.freshness_policy:
            asset_graph = self._external_repository.asset_graph
            return get_freshness_info(
                asset_key=self._external_asset_node.asset_key,
                # in the future, we can share this same CachingInstanceQueryer across all
                # GrapheneAssetNodes which share an external repository for improved performance
                data_time_resolver=CachingDataTimeResolver(
                    instance_queryer=CachingInstanceQueryer(
                        instance=graphene_info.context.instance,
                        asset_graph=asset_graph,
                    ),
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

    def _sensor_targets_asset(
        self, sensor: ExternalSensor, asset_graph: RemoteAssetGraph, job_names: Set[str]
    ) -> bool:
        asset_key = self._external_asset_node.asset_key

        if sensor.asset_selection is not None and (
            asset_key in sensor.asset_selection.resolve(asset_graph)
        ):
            return True

        return any(target.job_name in job_names for target in sensor.get_external_targets())

    def resolve_targetingInstigators(self, graphene_info) -> Sequence[GrapheneSensor]:
        external_sensors = self._external_repository.get_external_sensors()
        external_schedules = self._external_repository.get_external_schedules()

        asset_graph = self._external_repository.asset_graph

        job_names = {
            job_name
            for job_name in self._external_asset_node.job_names
            if not job_name.startswith(ASSET_BASE_JOB_PREFIX)
        }

        results = []
        for external_sensor in external_sensors:
            if not self._sensor_targets_asset(external_sensor, asset_graph, job_names):
                continue

            sensor_state = graphene_info.context.instance.get_instigator_state(
                external_sensor.get_external_origin_id(),
                external_sensor.selector_id,
            )
            results.append(GrapheneSensor(external_sensor, self._external_repository, sensor_state))

        for external_schedule in external_schedules:
            if external_schedule.job_name in job_names:
                schedule_state = graphene_info.context.instance.get_instigator_state(
                    external_schedule.get_external_origin_id(),
                    external_schedule.selector_id,
                )
                results.append(GrapheneSchedule(external_schedule, schedule_state))

        return results

    def _get_auto_materialize_external_sensor(self) -> Optional[ExternalSensor]:
        asset_graph = self._external_repository.asset_graph

        asset_key = self._external_asset_node.asset_key
        matching_sensors = [
            sensor
            for sensor in self._external_repository.get_external_sensors()
            if sensor.sensor_type == SensorType.AUTO_MATERIALIZE
            and asset_key in check.not_none(sensor.asset_selection).resolve(asset_graph)
        ]
        check.invariant(
            len(matching_sensors) <= 1,
            f"More than one automation policy sensor targeting asset key {asset_key}",
        )
        if not matching_sensors:
            return None

        return matching_sensors[0]

    def resolve_currentAutoMaterializeEvaluationId(self, graphene_info):
        from dagster._daemon.asset_daemon import get_current_evaluation_id

        instance = graphene_info.context.instance
        if instance.auto_materialize_use_sensors:
            external_sensor = self._get_auto_materialize_external_sensor()
            if not external_sensor:
                return None

            return get_current_evaluation_id(
                graphene_info.context.instance, external_sensor.get_external_origin()
            )
        else:
            return get_current_evaluation_id(graphene_info.context.instance, None)

    def resolve_backfillPolicy(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GrapheneBackfillPolicy]:
        if self._external_asset_node.backfill_policy:
            return GrapheneBackfillPolicy(self._external_asset_node.backfill_policy)
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

    def resolve_isExecutable(self, _graphene_info: ResolveInfo) -> bool:
        return self._external_asset_node.is_executable

    def resolve_latestMaterializationByPartition(
        self,
        graphene_info: ResolveInfo,
        partitions: Optional[Sequence[str]] = None,
    ) -> Sequence[Optional[GrapheneMaterializationEvent]]:
        get_partition = (
            lambda event: event.dagster_event.step_materialization_data.materialization.partition
        )

        query_all_partitions = partitions is None
        partitions = self.get_partition_keys() if query_all_partitions else partitions

        if query_all_partitions or len(partitions) > 1000:
            # when there are many partitions, it's much more efficient to grab the latest storage
            # id for all partitions and then query for the materialization events based on those
            # storage ids
            latest_storage_ids = sorted(
                (
                    graphene_info.context.instance.event_log_storage.get_latest_storage_id_by_partition(
                        self._external_asset_node.asset_key, DagsterEventType.ASSET_MATERIALIZATION
                    )
                ).values()
            )
            events_for_partitions = get_asset_materializations(
                graphene_info,
                asset_key=self._external_asset_node.asset_key,
                storage_ids=latest_storage_ids,
            )
            latest_materialization_by_partition = {
                get_partition(event): event for event in events_for_partitions
            }
        else:
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

        run_ids = [event.run_id for event in ordered_materializations if event]
        loader = BatchRunLoader(graphene_info.context.instance, run_ids) if run_ids else None

        return [
            GrapheneMaterializationEvent(event=event, loader=loader) if event else None
            for event in ordered_materializations
        ]

    def resolve_latestRunForPartition(
        self,
        graphene_info: ResolveInfo,
        partition: str,
    ) -> Optional[GrapheneRun]:
        planned_info = graphene_info.context.instance.get_latest_planned_materialization_info(
            asset_key=self._external_asset_node.asset_key, partition=partition
        )
        if not planned_info:
            return None
        run_record = graphene_info.context.instance.get_run_record_by_id(planned_info.run_id)
        return GrapheneRun(run_record) if run_record else None

    def resolve_assetPartitionStatuses(
        self, graphene_info: ResolveInfo
    ) -> Union[
        "GrapheneTimePartitionStatuses",
        "GrapheneDefaultPartitionStatuses",
        "GrapheneMultiPartitionStatuses",
    ]:
        asset_key = self._external_asset_node.asset_key

        if not self._dynamic_partitions_loader:
            check.failed("dynamic_partitions_loader must be provided to get partition keys")

        partitions_def = (
            self._external_asset_node.partitions_def_data.get_partitions_definition()
            if self._external_asset_node.partitions_def_data
            else None
        )

        (
            materialized_partition_subset,
            failed_partition_subset,
            in_progress_subset,
        ) = get_partition_subsets(
            graphene_info.context.instance,
            asset_key,
            self._dynamic_partitions_loader,
            partitions_def,
        )

        return build_partition_statuses(
            self._dynamic_partitions_loader,
            materialized_partition_subset,
            failed_partition_subset,
            in_progress_subset,
            partitions_def,
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
                (
                    self._external_asset_node.partitions_def_data.get_partitions_definition()
                    if self._external_asset_node.partitions_def_data
                    else None
                ),
            )

            if (
                materialized_partition_subset is None
                or failed_partition_subset is None
                or in_progress_subset is None
            ):
                check.failed("Expected partitions subset for a partitioned asset")

            failed_keys = failed_partition_subset.get_partition_keys()
            in_progress_keys = in_progress_subset.get_partition_keys()
            failed_and_in_progress_keys = {*failed_keys, *in_progress_keys}

            num_materialized_and_not_failed_or_in_progress = len(
                materialized_partition_subset
            ) - len([k for k in failed_and_in_progress_keys if k in materialized_partition_subset])

            num_failed_and_not_in_progress = len(
                [k for k in failed_keys if k not in in_progress_subset]
            )

            return GraphenePartitionStats(
                numMaterialized=num_materialized_and_not_failed_or_in_progress,
                numPartitions=partitions_def_data.get_partitions_definition().get_num_partitions(
                    dynamic_partitions_store=self._dynamic_partitions_loader
                ),
                numFailed=num_failed_and_not_in_progress,
                numMaterializing=len(in_progress_subset),
            )
        else:
            return None

    def resolve_metadata_entries(
        self, _graphene_info: ResolveInfo
    ) -> Sequence[GrapheneMetadataEntry]:
        return list(iterate_metadata_entries(self._external_asset_node.metadata))

    def resolve_tags(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneDefinitionTag]:
        return [
            GrapheneDefinitionTag(key, value)
            for key, value in (self._external_asset_node.tags or {}).items()
        ]

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
            graphene_info.context, self._external_repository, self._repository_location
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

    def _get_partitions_def(self) -> PartitionsDefinition:
        if not self._external_asset_node.partitions_def_data:
            check.failed("Asset node has no partitions definition")
        return self._external_asset_node.partitions_def_data.get_partitions_definition()

    def _validate_partitions_existence(self) -> None:
        if not self._external_asset_node.partitions_def_data:
            check.failed("Asset node has no partitions definition")

    def resolve_hasAssetChecks(self, graphene_info: ResolveInfo) -> bool:
        return has_asset_checks(graphene_info, self._external_asset_node.asset_key)

    def resolve_assetChecksOrError(
        self,
        graphene_info: ResolveInfo,
        limit=None,
        pipeline: Optional[GraphenePipelineSelector] = None,
    ) -> AssetChecksOrErrorUnion:
        return self._asset_checks_loader.get_checks_for_asset(
            self._external_asset_node.asset_key, limit, pipeline
        )


class GrapheneAssetGroup(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    groupName = graphene.NonNull(graphene.String)
    assetKeys = non_null_list(GrapheneAssetKey)

    class Meta:
        name = "AssetGroup"


class GrapheneAssetNodeOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetNode, GrapheneAssetNotFoundError)
        name = "AssetNodeOrError"
