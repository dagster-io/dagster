from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional, Union, cast

import graphene
from dagster import (
    AssetKey,
    _check as check,
)
from dagster._core.definitions.asset_graph_differ import AssetDefinitionChangeType, AssetGraphDiffer
from dagster._core.definitions.data_version import (
    NULL_DATA_VERSION,
    StaleCauseCategory,
    StaleStatus,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionSnapshot,
)
from dagster._core.definitions.partition import CachingDynamicPartitionsLoader, PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.remote_asset_graph import RemoteAssetNode, RemoteWorkspaceAssetNode
from dagster._core.definitions.selector import JobSelector
from dagster._core.definitions.sensor_definition import SensorType
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import AssetRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.remote_representation.external import RemoteJob, RemoteSensor
from dagster._core.remote_representation.external_data import (
    AssetNodeSnap,
    DynamicPartitionsSnap,
    MultiPartitionsSnap,
    PartitionsSnap,
    StaticPartitionsSnap,
    TimeWindowPartitionsSnap,
)
from dagster._core.snap.node import GraphDefSnap, OpDefSnap
from dagster._core.storage.asset_check_execution_record import AssetCheckInstanceSupport
from dagster._core.storage.event_log.base import AssetRecord
from dagster._core.storage.tags import KIND_PREFIX
from dagster._core.utils import is_valid_email
from dagster._core.workspace.permissions import Permissions
from packaging import version

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.implementation.fetch_asset_checks import has_asset_checks
from dagster_graphql.implementation.fetch_assets import (
    build_partition_statuses,
    get_asset_materializations,
    get_asset_observations,
    get_freshness_info,
    get_partition_subsets,
)
from dagster_graphql.implementation.loader import StaleStatusLoader
from dagster_graphql.schema import external
from dagster_graphql.schema.asset_checks import (
    AssetChecksOrErrorUnion,
    GrapheneAssetCheck,
    GrapheneAssetCheckNeedsAgentUpgradeError,
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
    GrapheneAssetChecks,
    GrapheneAssetChecksOrError,
)
from dagster_graphql.schema.auto_materialize_policy import GrapheneAutoMaterializePolicy
from dagster_graphql.schema.automation_condition import GrapheneAutomationCondition
from dagster_graphql.schema.backfill import GrapheneBackfillPolicy
from dagster_graphql.schema.config_types import GrapheneConfigTypeField
from dagster_graphql.schema.dagster_types import (
    GrapheneDagsterType,
    GrapheneListDagsterType,
    GrapheneNullableDagsterType,
    GrapheneRegularDagsterType,
    to_dagster_type,
)
from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.errors import GrapheneAssetNotFoundError
from dagster_graphql.schema.freshness_policy import (
    GrapheneAssetFreshnessInfo,
    GrapheneFreshnessPolicy,
)
from dagster_graphql.schema.inputs import GraphenePipelineSelector
from dagster_graphql.schema.instigators import GrapheneInstigator
from dagster_graphql.schema.logs.events import (
    GrapheneMaterializationEvent,
    GrapheneObservationEvent,
)
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.partition_mappings import GraphenePartitionMapping
from dagster_graphql.schema.partition_sets import (
    GrapheneDimensionPartitionKeys,
    GraphenePartitionDefinition,
    GraphenePartitionDefinitionType,
)
from dagster_graphql.schema.pipelines.pipeline import (
    GrapheneAssetPartitionStatuses,
    GrapheneDefaultPartitionStatuses,
    GrapheneMultiPartitionStatuses,
    GraphenePartitionStats,
    GraphenePipeline,
    GrapheneRun,
    GrapheneTimePartitionStatuses,
)
from dagster_graphql.schema.schedules import GrapheneSchedule
from dagster_graphql.schema.sensors import GrapheneSensor
from dagster_graphql.schema.solids import (
    GrapheneCompositeSolidDefinition,
    GrapheneResourceRequirement,
    GrapheneSolidDefinition,
)
from dagster_graphql.schema.tags import GrapheneDefinitionTag
from dagster_graphql.schema.util import ResolveInfo, non_null_list

if TYPE_CHECKING:
    from dagster_graphql.schema.external import GrapheneRepository

GrapheneAssetStaleStatus = graphene.Enum.from_enum(StaleStatus, name="StaleStatus")
GrapheneAssetStaleCauseCategory = graphene.Enum.from_enum(
    StaleCauseCategory, name="StaleCauseCategory"
)

GrapheneAssetChangedReason = graphene.Enum.from_enum(AssetDefinitionChangeType, name="ChangeReason")


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
    partitionMapping = graphene.Field(GraphenePartitionMapping)

    def __init__(
        self,
        *,
        asset_key: AssetKey,
        partition_mapping: Optional[PartitionMapping] = None,
    ):
        self._asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        self._partition_mapping = check.opt_inst_param(
            partition_mapping, "partition_mapping", PartitionMapping
        )
        super().__init__()

    def resolve_asset(self, graphene_info: ResolveInfo):
        remote_node = graphene_info.context.asset_graph.get(self._asset_key)
        return GrapheneAssetNode(
            remote_node=remote_node,
        )

    def resolve_partitionMapping(
        self, graphene_info: ResolveInfo
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
    automationCondition = graphene.Field(GrapheneAutomationCondition)
    graphName = graphene.String()
    groupName = graphene.NonNull(graphene.String)
    owners = non_null_list(GrapheneAssetOwner)
    id = graphene.NonNull(graphene.ID)
    isExecutable = graphene.NonNull(graphene.Boolean)
    isObservable = graphene.NonNull(graphene.Boolean)
    isMaterializable = graphene.NonNull(graphene.Boolean)
    isPartitioned = graphene.NonNull(graphene.Boolean)
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
    kinds = non_null_list(graphene.String)
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
    pools = non_null_list(graphene.String)
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
        graphene.List(non_null_list(GrapheneAssetStaleCause)),
        partitions=graphene.List(graphene.NonNull(graphene.String)),
    )
    type = graphene.Field(GrapheneDagsterType)
    hasMaterializePermission = graphene.NonNull(graphene.Boolean)
    hasReportRunlessAssetEventPermission = graphene.NonNull(graphene.Boolean)

    # the acutal checks are listed in the assetChecksOrError resolver. We use this boolean
    # to show/hide the checks tab. We plan to remove this field once we always show the checks tab.
    hasAssetChecks = graphene.NonNull(graphene.Boolean)
    assetChecksOrError = graphene.Field(
        graphene.NonNull(GrapheneAssetChecksOrError),
        limit=graphene.Argument(graphene.Int),
        pipeline=graphene.Argument(GraphenePipelineSelector),
    )
    currentAutoMaterializeEvaluationId = graphene.ID()
    targetingInstigators = non_null_list(GrapheneInstigator)

    class Meta:
        name = "AssetNode"

    def __init__(
        self,
        *,
        remote_node: RemoteAssetNode,
        stale_status_loader: Optional[StaleStatusLoader] = None,
        dynamic_partitions_loader: Optional[CachingDynamicPartitionsLoader] = None,
    ):
        from dagster_graphql.implementation.fetch_assets import get_unique_asset_id

        self._remote_node = check.inst_param(remote_node, "remote_node", RemoteAssetNode)

        repo_scoped_node = remote_node.resolve_to_singular_repo_scoped_node()
        self._asset_node_snap = repo_scoped_node.asset_node_snap
        self._repository_handle = repo_scoped_node.repository_handle
        self._repository_selector = self._repository_handle.to_selector()

        self._stale_status_loader = check.opt_inst_param(
            stale_status_loader,
            "stale_status_loader",
            StaleStatusLoader,
        )
        self._dynamic_partitions_loader = check.opt_inst_param(
            dynamic_partitions_loader, "dynamic_partitions_loader", CachingDynamicPartitionsLoader
        )
        self._remote_job = None  # lazily loaded
        self._node_definition_snap = None  # lazily loaded
        self._asset_graph_differ = None  # lazily loaded

        super().__init__(
            id=get_unique_asset_id(
                self._asset_node_snap.asset_key,
                self._repository_handle.location_name,
                self._repository_handle.repository_name,
            ),
            assetKey=self._asset_node_snap.asset_key,
            description=self._asset_node_snap.description,
            opName=self._asset_node_snap.op_name,
            opVersion=self._asset_node_snap.code_version,
            groupName=self._asset_node_snap.group_name,
            owners=[
                self._graphene_asset_owner_from_owner_str(owner)
                for owner in (self._asset_node_snap.owners or [])
            ],
        )

    def _graphene_asset_owner_from_owner_str(
        self, owner_str: str
    ) -> Union[GrapheneUserAssetOwner, GrapheneTeamAssetOwner]:
        if is_valid_email(owner_str):
            return GrapheneUserAssetOwner(email=owner_str)
        else:
            check.invariant(owner_str.startswith("team:"))
            return GrapheneTeamAssetOwner(team=owner_str[5:])

    @property
    def asset_node_snap(self) -> AssetNodeSnap:
        return self._asset_node_snap

    @property
    def stale_status_loader(self) -> StaleStatusLoader:
        loader = check.not_none(
            self._stale_status_loader,
            "stale_status_loader must exist in order to access data versioning information",
        )
        return loader

    def _get_asset_graph_differ(self, graphene_info: ResolveInfo) -> Optional[AssetGraphDiffer]:
        if self._asset_graph_differ is not None:
            return self._asset_graph_differ

        base_deployment_asset_graph = graphene_info.context.get_base_deployment_asset_graph()

        if base_deployment_asset_graph is None:
            return None

        self._asset_graph_differ = AssetGraphDiffer(
            branch_asset_graph=graphene_info.context.asset_graph,
            base_asset_graph=base_deployment_asset_graph,
        )
        return self._asset_graph_differ

    def _job_selector(self) -> Optional[JobSelector]:
        if len(self._asset_node_snap.job_names) < 1:
            return None

        return JobSelector(
            location_name=self._repository_selector.location_name,
            repository_name=self._repository_selector.repository_name,
            job_name=self._asset_node_snap.job_names[0],
        )

    def get_remote_job(self, graphene_info: ResolveInfo) -> RemoteJob:
        selector = self._job_selector()
        if self._remote_job is None:
            if selector is None:
                check.failed("Asset must be part of a job")
            self._remote_job = graphene_info.context.get_full_job(selector)
        return self._remote_job

    def get_node_definition_snap(
        self,
        graphene_info: ResolveInfo,
    ) -> Optional[Union[GraphDefSnap, OpDefSnap]]:
        selector = self._job_selector()
        if selector is None:
            return None

        if self._node_definition_snap is None:
            node_key = check.not_none(
                self._asset_node_snap.node_definition_name
                # nodes serialized using an older Dagster version may not have node_definition_name
                or self._asset_node_snap.graph_name
                or self._asset_node_snap.op_name
            )
            self._node_definition_snap = graphene_info.context.get_node_def(selector, node_key)

        return self._node_definition_snap

    def get_partition_keys(
        self,
        partitions_snap: Optional[PartitionsSnap] = None,
        start_idx: Optional[int] = None,
        end_idx: Optional[int] = None,
    ) -> Sequence[str]:
        # TODO: Add functionality for dynamic partitions definition
        # Accepts an optional start_idx and end_idx to fetch a subset of time window partition keys

        check.opt_inst_param(partitions_snap, "partitions_snap", PartitionsSnap)
        check.opt_int_param(start_idx, "start_idx")
        check.opt_int_param(end_idx, "end_idx")

        if not self._dynamic_partitions_loader:
            check.failed("dynamic_partitions_loader must be provided to get partition keys")

        partitions_snap = (
            self._asset_node_snap.partitions if not partitions_snap else partitions_snap
        )
        if partitions_snap:
            if isinstance(
                partitions_snap,
                (
                    StaticPartitionsSnap,
                    TimeWindowPartitionsSnap,
                    MultiPartitionsSnap,
                ),
            ):
                if start_idx and end_idx and isinstance(partitions_snap, TimeWindowPartitionsSnap):
                    return partitions_snap.get_partitions_definition().get_partition_keys_between_indexes(
                        start_idx, end_idx
                    )
                else:
                    return partitions_snap.get_partitions_definition().get_partition_keys(
                        dynamic_partitions_store=self._dynamic_partitions_loader
                    )
            elif isinstance(partitions_snap, DynamicPartitionsSnap):
                return self._dynamic_partitions_loader.get_dynamic_partitions(
                    partitions_def_name=partitions_snap.name
                )
            else:
                raise DagsterInvariantViolationError(
                    f"Unsupported partition definition type {partitions_snap}"
                )
        return []

    def is_multipartitioned(self) -> bool:
        partitions_snap = self._asset_node_snap.partitions

        return partitions_snap is not None and isinstance(partitions_snap, MultiPartitionsSnap)

    def get_required_resource_keys(
        self,
        graphene_info: ResolveInfo,
        node_def_snap: Union[GraphDefSnap, OpDefSnap],
    ) -> Sequence[str]:
        all_keys = self.get_required_resource_keys_rec(graphene_info, node_def_snap)
        return list(set(all_keys))

    def get_required_resource_keys_rec(
        self,
        graphene_info: ResolveInfo,
        node_def_snap: Union[GraphDefSnap, OpDefSnap],
    ) -> Sequence[str]:
        if isinstance(node_def_snap, GraphDefSnap):
            constituent_node_names = [
                inv.node_def_name
                for inv in node_def_snap.dep_structure_snapshot.node_invocation_snaps
            ]
            job = self.get_remote_job(graphene_info)
            constituent_resource_key_sets = [
                self.get_required_resource_keys_rec(graphene_info, job.get_node_def_snap(name))
                for name in constituent_node_names
            ]
            return [key for res_key_set in constituent_resource_key_sets for key in res_key_set]
        else:
            return node_def_snap.required_resource_keys

    def is_graph_backed_asset(self) -> bool:
        return self.graphName is not None

    @property
    def is_executable(self) -> bool:
        return self._asset_node_snap.is_executable

    def resolve_hasMaterializePermission(
        self,
        graphene_info: ResolveInfo,
    ) -> bool:
        return graphene_info.context.has_permission_for_location(
            Permissions.LAUNCH_PIPELINE_EXECUTION, self._repository_selector.location_name
        )

    def resolve_hasReportRunlessAssetEventPermission(
        self,
        graphene_info: ResolveInfo,
    ) -> bool:
        return graphene_info.context.has_permission_for_location(
            Permissions.REPORT_RUNLESS_ASSET_EVENTS, self._repository_selector.location_name
        )

    def resolve_assetMaterializationUsedData(
        self,
        graphene_info: ResolveInfo,
        timestampMillis: str,
    ) -> Sequence[GrapheneMaterializationUpstreamDataVersion]:
        if not timestampMillis:
            return []

        instance = graphene_info.context.instance
        asset_graph = graphene_info.context.asset_graph
        asset_key = self._asset_node_snap.asset_key
        event_records = instance.fetch_materializations(
            AssetRecordsFilter(
                asset_key=asset_key,
                before_timestamp=int(timestampMillis) / 1000.0 + 1,
                after_timestamp=int(timestampMillis) / 1000.0 - 1,
            ),
            limit=1,
        ).records

        if not event_records:
            return []

        if not asset_graph.has_materializable_parents(asset_key):
            return []

        used_data_times = graphene_info.context.data_time_resolver.get_data_time_by_key_for_record(
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

        if limit == 1 and not partitions and not before_timestamp:
            record = AssetRecord.blocking_get(
                graphene_info.context, self._asset_node_snap.asset_key
            )
            latest_materialization_event = (
                record.asset_entry.last_materialization if record else None
            )

            if not latest_materialization_event:
                return []

            return [GrapheneMaterializationEvent(event=latest_materialization_event)]

        return [
            GrapheneMaterializationEvent(event=event)
            for event in get_asset_materializations(
                graphene_info,
                self._asset_node_snap.asset_key,
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

        if (
            graphene_info.context.instance.event_log_storage.asset_records_have_last_observation
            and limit == 1
            and not partitions
            and not before_timestamp
        ):
            record = AssetRecord.blocking_get(
                graphene_info.context, self._asset_node_snap.asset_key
            )
            latest_observation_event = record.asset_entry.last_observation if record else None

            if not latest_observation_event:
                return []

            return [GrapheneObservationEvent(event=latest_observation_event)]

        return [
            GrapheneObservationEvent(event=event)
            for event in get_asset_observations(
                graphene_info,
                self._asset_node_snap.asset_key,
                partitions,
                before_timestamp=before_timestamp,
                limit=limit,
            )
        ]

    def resolve_configField(self, graphene_info: ResolveInfo) -> Optional[GrapheneConfigTypeField]:
        selector = self._job_selector()
        if selector is None:
            return None
        node_def_snap = self.get_node_definition_snap(graphene_info)
        if node_def_snap is None or node_def_snap.config_field_snap is None:
            return None

        def _get_config_type(key: str):
            return graphene_info.context.get_config_type(selector, key)

        return GrapheneConfigTypeField(
            get_config_type=_get_config_type,
            field_snap=node_def_snap.config_field_snap,
        )

    def resolve_computeKind(self, _graphene_info: ResolveInfo) -> Optional[str]:
        return self._asset_node_snap.compute_kind

    def resolve_changedReasons(
        self, graphene_info: ResolveInfo
    ) -> Sequence[Any]:  # Sequence[GrapheneAssetChangedReason]
        asset_graph_differ = self._get_asset_graph_differ(graphene_info)
        if asset_graph_differ is None:
            # asset_graph_differ is None when not in a branch deployment
            return []
        return asset_graph_differ.get_changes_for_asset(self._asset_node_snap.asset_key)

    def resolve_staleStatus(
        self, graphene_info: ResolveInfo, partition: Optional[str] = None
    ) -> Any:  # (GrapheneAssetStaleStatus)
        if partition:
            self._validate_partitions_existence()
        return self.stale_status_loader.get_status(self._asset_node_snap.asset_key, partition)

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
            self.stale_status_loader.get_status(self._asset_node_snap.asset_key, partition)
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
            self._asset_node_snap.asset_key, partition
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
            self._asset_node_snap.asset_key, partition
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
                self._asset_node_snap.asset_key, partition
            )
            for partition in partitions
        ]
        return [
            None if version == NULL_DATA_VERSION else version.value for version in data_versions
        ]

    def resolve_dependedBy(self, graphene_info: ResolveInfo) -> list[GrapheneAssetDependency]:
        if not self._remote_node.child_keys:
            return []

        return [
            GrapheneAssetDependency(
                asset_key=asset_key,
            )
            for asset_key in self._remote_node.child_keys
        ]

    def resolve_dependedByKeys(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneAssetKey]:
        return [GrapheneAssetKey(path=key.path) for key in self._remote_node.child_keys]

    def resolve_dependencyKeys(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneAssetKey]:
        return [
            GrapheneAssetKey(path=dep.parent_asset_key.path)
            for dep in self._asset_node_snap.parent_edges
        ]

    def resolve_dependencies(self, graphene_info: ResolveInfo) -> Sequence[GrapheneAssetDependency]:
        if not self._remote_node.parent_keys:
            return []

        return [
            GrapheneAssetDependency(
                asset_key=key,
                partition_mapping=self._remote_node.partition_mappings.get(key),
            )
            for key in self._remote_node.parent_keys
        ]

    def resolve_freshnessInfo(
        self, graphene_info: ResolveInfo
    ) -> Optional[GrapheneAssetFreshnessInfo]:
        if self._asset_node_snap.freshness_policy:
            return get_freshness_info(
                asset_key=self._asset_node_snap.asset_key,
                data_time_resolver=graphene_info.context.data_time_resolver,
            )
        return None

    def resolve_freshnessPolicy(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GrapheneFreshnessPolicy]:
        if self._asset_node_snap.freshness_policy:
            return GrapheneFreshnessPolicy(self._asset_node_snap.freshness_policy)
        return None

    def resolve_autoMaterializePolicy(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GrapheneAutoMaterializePolicy]:
        if self._asset_node_snap.auto_materialize_policy:
            return GrapheneAutoMaterializePolicy(self._asset_node_snap.auto_materialize_policy)
        return None

    def resolve_automationCondition(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GrapheneAutomationCondition]:
        automation_condition = (
            self._asset_node_snap.automation_condition_snapshot
            or self._asset_node_snap.automation_condition
        )
        if automation_condition:
            return GrapheneAutomationCondition(
                # we only store one of automation_condition or automation_condition_snapshot
                automation_condition
                if isinstance(automation_condition, AutomationConditionSnapshot)
                else automation_condition.get_snapshot()
            )
        return None

    def resolve_targetingInstigators(self, graphene_info: ResolveInfo) -> Sequence[GrapheneSensor]:
        if isinstance(self._remote_node, RemoteWorkspaceAssetNode):
            # global nodes have saved references to their targeting instigators
            schedules = [
                schedule
                for schedule_handle in self._remote_node.get_targeting_schedule_handles()
                if (schedule := graphene_info.context.get_schedule(schedule_handle)) is not None
            ]
            sensors = [
                sensor
                for sensor_handle in self._remote_node.get_targeting_sensor_handles()
                if (sensor := graphene_info.context.get_sensor(sensor_handle)) is not None
            ]

        else:
            # fallback to using the repository
            repo = graphene_info.context.get_repository(self._repository_selector)
            schedules = repo.get_schedules_targeting(self._asset_node_snap.asset_key)
            sensors = repo.get_sensors_targeting(self._asset_node_snap.asset_key)

        results = []
        for sensor in sensors:
            sensor_state = graphene_info.context.instance.get_instigator_state(
                sensor.get_remote_origin_id(),
                sensor.selector_id,
            )
            results.append(
                GrapheneSensor(
                    sensor,
                    sensor_state,
                )
            )

        for schedule in schedules:
            schedule_state = graphene_info.context.instance.get_instigator_state(
                schedule.get_remote_origin_id(),
                schedule.selector_id,
            )
            results.append(
                GrapheneSchedule(
                    schedule,
                    schedule_state,
                )
            )

        return results

    def _get_auto_materialize_remote_sensor(
        self, graphene_info: ResolveInfo
    ) -> Optional[RemoteSensor]:
        repo = graphene_info.context.get_repository(self._repository_selector)
        asset_graph = repo.asset_graph

        asset_key = self._asset_node_snap.asset_key
        matching_sensors = [
            sensor
            for sensor in repo.get_sensors()
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

    def resolve_currentAutoMaterializeEvaluationId(self, graphene_info: ResolveInfo):
        from dagster._daemon.asset_daemon import get_current_evaluation_id

        instance = graphene_info.context.instance
        if instance.auto_materialize_use_sensors:
            sensor = self._get_auto_materialize_remote_sensor(graphene_info)
            if not sensor:
                return None

            return get_current_evaluation_id(
                graphene_info.context.instance, sensor.get_remote_origin()
            )
        else:
            return get_current_evaluation_id(graphene_info.context.instance, None)

    def resolve_backfillPolicy(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GrapheneBackfillPolicy]:
        if self._asset_node_snap.backfill_policy:
            return GrapheneBackfillPolicy(self._asset_node_snap.backfill_policy)
        return None

    def resolve_jobNames(self, _graphene_info: ResolveInfo) -> Sequence[str]:
        return self._asset_node_snap.job_names

    def resolve_jobs(self, graphene_info: ResolveInfo) -> Sequence[GraphenePipeline]:
        job_names = self._asset_node_snap.job_names or []
        repo = graphene_info.context.get_repository(self._repository_selector)
        return [
            GraphenePipeline(repo.get_full_job(job_name))
            for job_name in job_names
            if repo.has_job(job_name)
        ]

    def resolve_isPartitioned(self, _graphene_info: ResolveInfo) -> bool:
        return self._asset_node_snap.partitions is not None

    def resolve_isMaterializable(self, _graphene_info: ResolveInfo) -> bool:
        return self._asset_node_snap.is_materializable

    def resolve_isObservable(self, _graphene_info: ResolveInfo) -> bool:
        return self._asset_node_snap.is_observable

    def resolve_isExecutable(self, _graphene_info: ResolveInfo) -> bool:
        return self._asset_node_snap.is_executable

    def resolve_latestMaterializationByPartition(
        self,
        graphene_info: ResolveInfo,
        partitions: Optional[Sequence[str]] = None,
    ) -> Sequence[Optional[GrapheneMaterializationEvent]]:
        latest_storage_ids = sorted(
            (
                graphene_info.context.instance.event_log_storage.get_latest_storage_id_by_partition(
                    self._asset_node_snap.asset_key,
                    DagsterEventType.ASSET_MATERIALIZATION,
                    set(partitions) if partitions else None,
                )
            ).values()
        )
        events_for_partitions = get_asset_materializations(
            graphene_info,
            asset_key=self._asset_node_snap.asset_key,
            storage_ids=latest_storage_ids,
        )
        latest_materialization_by_partition = {
            event.dagster_event.step_materialization_data.materialization.partition: event
            for event in events_for_partitions
            if event.dagster_event
        }

        # return materializations in the same order as the provided partitions, None if
        # materialization does not exist
        partitions = self.get_partition_keys() if partitions is None else partitions
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
        planned_info = graphene_info.context.instance.get_latest_planned_materialization_info(
            asset_key=self._asset_node_snap.asset_key, partition=partition
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
        asset_key = self._asset_node_snap.asset_key

        if not self._dynamic_partitions_loader:
            check.failed("dynamic_partitions_loader must be provided to get partition keys")

        partitions_def = (
            self._asset_node_snap.partitions.get_partitions_definition()
            if self._asset_node_snap.partitions
            else None
        )

        (
            materialized_partition_subset,
            failed_partition_subset,
            in_progress_subset,
        ) = get_partition_subsets(
            graphene_info.context.instance,
            graphene_info.context,
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
        partitions_snap = self._asset_node_snap.partitions
        if partitions_snap:
            asset_key = self._asset_node_snap.asset_key

            if not self._dynamic_partitions_loader:
                check.failed("dynamic_partitions_loader must be provided to get partition keys")

            (
                materialized_partition_subset,
                failed_partition_subset,
                in_progress_subset,
            ) = get_partition_subsets(
                graphene_info.context.instance,
                graphene_info.context,
                asset_key,
                self._dynamic_partitions_loader,
                (
                    self._asset_node_snap.partitions.get_partitions_definition()
                    if self._asset_node_snap.partitions
                    else None
                ),
            )

            if (
                materialized_partition_subset is None
                or failed_partition_subset is None
                or in_progress_subset is None
            ):
                check.failed("Expected partitions subset for a partitioned asset")

            failed_or_in_progress_subset = failed_partition_subset | in_progress_subset
            failed_and_not_in_progress_subset = failed_partition_subset - in_progress_subset

            materialized_and_not_failed_or_in_progress_subset = (
                materialized_partition_subset - failed_or_in_progress_subset
            )

            return GraphenePartitionStats(
                numMaterialized=len(materialized_and_not_failed_or_in_progress_subset),
                numPartitions=partitions_snap.get_partitions_definition().get_num_partitions(
                    dynamic_partitions_store=self._dynamic_partitions_loader
                ),
                numFailed=len(failed_and_not_in_progress_subset),
                numMaterializing=len(in_progress_subset),
            )
        else:
            return None

    def resolve_metadata_entries(
        self, _graphene_info: ResolveInfo
    ) -> Sequence[GrapheneMetadataEntry]:
        return list(iterate_metadata_entries(self._asset_node_snap.metadata))

    def resolve_tags(self, _graphene_info: ResolveInfo) -> Sequence[GrapheneDefinitionTag]:
        return [
            GrapheneDefinitionTag(key, value)
            for key, value in (self._asset_node_snap.tags or {}).items()
        ]

    def resolve_kinds(self, _graphene_info: ResolveInfo) -> Sequence[str]:
        if self._asset_node_snap.compute_kind:
            return [self._asset_node_snap.compute_kind]

        return [
            key[len(KIND_PREFIX) :]
            for key in (self._asset_node_snap.tags or {}).keys()
            if key.startswith(KIND_PREFIX)
        ]

    def resolve_op(
        self, graphene_info: ResolveInfo
    ) -> Optional[Union[GrapheneSolidDefinition, GrapheneCompositeSolidDefinition]]:
        if not self.is_executable:
            return None
        job = self.get_remote_job(graphene_info)
        node_def_snap = self.get_node_definition_snap(graphene_info)
        if node_def_snap is None:
            return None

        if isinstance(node_def_snap, OpDefSnap):
            return GrapheneSolidDefinition(job, node_def_snap.name)

        if isinstance(node_def_snap, GraphDefSnap):
            return GrapheneCompositeSolidDefinition(job, node_def_snap.name)

        check.failed(f"Unknown solid definition type {type(node_def_snap)}")

    def resolve_opNames(self, _graphene_info: ResolveInfo) -> Sequence[str]:
        return self._asset_node_snap.op_names or []

    def resolve_graphName(self, _graphene_info: ResolveInfo) -> Optional[str]:
        return self._asset_node_snap.graph_name

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
        if not self._asset_node_snap.partitions:
            return []

        if self.is_multipartitioned():
            return [
                GrapheneDimensionPartitionKeys(
                    name=dimension.name,
                    partition_keys=self.get_partition_keys(
                        dimension.partitions,
                        startIdx,
                        endIdx,
                    ),
                    type=GraphenePartitionDefinitionType.from_partition_def_data(
                        dimension.partitions
                    ),
                )
                for dimension in cast(
                    MultiPartitionsSnap,
                    self._asset_node_snap.partitions,
                ).partition_dimensions
            ]

        return [
            GrapheneDimensionPartitionKeys(
                name="default",
                type=GraphenePartitionDefinitionType.from_partition_def_data(
                    self._asset_node_snap.partitions
                ),
                partition_keys=self.get_partition_keys(start_idx=startIdx, end_idx=endIdx),
            )
        ]

    def resolve_partitionKeys(self, _graphene_info: ResolveInfo) -> Sequence[str]:
        return self.get_partition_keys()

    def resolve_partitionDefinition(
        self, _graphene_info: ResolveInfo
    ) -> Optional[GraphenePartitionDefinition]:
        partitions_snap = self._asset_node_snap.partitions
        if partitions_snap:
            return GraphenePartitionDefinition(partitions_snap)
        return None

    def resolve_pools(self, _graphene_info: ResolveInfo) -> Sequence[str]:
        return sorted([pool for pool in self._asset_node_snap.pools or set()])

    def resolve_repository(self, graphene_info: ResolveInfo) -> "GrapheneRepository":
        return external.GrapheneRepository(self._repository_handle)

    def resolve_required_resources(
        self, graphene_info: ResolveInfo
    ) -> Sequence[GrapheneResourceRequirement]:
        if not self.is_executable:
            return []
        node_def_snap = self.get_node_definition_snap(graphene_info)
        if node_def_snap is None:
            return []
        all_unique_keys = self.get_required_resource_keys(graphene_info, node_def_snap)
        return [GrapheneResourceRequirement(key) for key in all_unique_keys]

    def resolve_type(
        self, graphene_info: ResolveInfo
    ) -> Optional[
        Union[
            "GrapheneListDagsterType", "GrapheneNullableDagsterType", "GrapheneRegularDagsterType"
        ]
    ]:
        selector = self._job_selector()
        node_def_snap = self.get_node_definition_snap(graphene_info)

        if selector is None or node_def_snap is None:
            return None

        def _get_dagster_type(key: str):
            return graphene_info.context.get_dagster_type(selector, key)

        def _get_config_type(key: str):
            return graphene_info.context.get_config_type(selector, key)

        output_name = self._asset_node_snap.output_name
        if output_name:
            for output_def in node_def_snap.output_def_snaps:
                if output_def.name == output_name:
                    return to_dagster_type(
                        get_dagster_type=_get_dagster_type,
                        get_config_type=_get_config_type,
                        dagster_type_key=output_def.dagster_type_key,
                    )
        return None

    def _get_partitions_def(self) -> PartitionsDefinition:
        if not self._asset_node_snap.partitions:
            check.failed("Asset node has no partitions definition")
        return self._asset_node_snap.partitions.get_partitions_definition()

    def _validate_partitions_existence(self) -> None:
        if not self._asset_node_snap.partitions:
            check.failed("Asset node has no partitions definition")

    def resolve_hasAssetChecks(self, graphene_info: ResolveInfo) -> bool:
        return has_asset_checks(graphene_info, self._asset_node_snap.asset_key)

    def resolve_assetChecksOrError(
        self,
        graphene_info: ResolveInfo,
        limit=None,
        pipeline: Optional[GraphenePipelineSelector] = None,
    ) -> AssetChecksOrErrorUnion:
        remote_check_nodes = graphene_info.context.asset_graph.get_checks_for_asset(
            self._asset_node_snap.asset_key
        )
        if not remote_check_nodes:
            return GrapheneAssetChecks(checks=[])

        asset_check_support = graphene_info.context.instance.get_asset_check_support()
        if asset_check_support == AssetCheckInstanceSupport.NEEDS_MIGRATION:
            return GrapheneAssetCheckNeedsMigrationError(
                message="Asset checks require an instance migration. Run `dagster instance migrate`."
            )
        elif asset_check_support == AssetCheckInstanceSupport.NEEDS_AGENT_UPGRADE:
            return GrapheneAssetCheckNeedsAgentUpgradeError(
                "Asset checks require an agent upgrade to 1.5.0 or greater."
            )
        else:
            check.invariant(
                asset_check_support == AssetCheckInstanceSupport.SUPPORTED,
                f"Unexpected asset check support status {asset_check_support}",
            )

        library_versions = graphene_info.context.get_dagster_library_versions(
            self._repository_handle.location_name
        )
        code_location_version = (library_versions or {}).get("dagster")
        if code_location_version and version.parse(code_location_version) < version.parse("1.5"):
            return GrapheneAssetCheckNeedsUserCodeUpgrade(
                message=(
                    "Asset checks require dagster>=1.5. Upgrade your dagster"
                    " version for this code location."
                )
            )
        if pipeline:
            remote_check_nodes = [
                node
                for node in remote_check_nodes
                if node.handle.location_name == pipeline.repositoryLocationName
                and node.handle.repository_name == pipeline.repositoryName
                and pipeline.pipelineName in node.asset_check.job_names
            ]

        if limit:
            remote_check_nodes = remote_check_nodes[:limit]

        return GrapheneAssetChecks(
            checks=[
                GrapheneAssetCheck(remote_check_node) for remote_check_node in remote_check_nodes
            ]
        )


class GrapheneAssetGroup(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    groupName = graphene.NonNull(graphene.String)
    assetKeys = non_null_list(GrapheneAssetKey)

    class Meta:
        name = "AssetGroup"


class GrapheneCodeLocation(graphene.ObjectType):
    class Meta:
        name = "CodeLocation"

    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)


class GrapheneDefinitionGroup(graphene.ObjectType):
    class Meta:
        name = "DefinitionGroup"

    groupName = graphene.NonNull(graphene.String)
    repositoryName = graphene.NonNull(graphene.String)
    repositoryLocationName = graphene.NonNull(graphene.String)


class GrapheneAssetNodeOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetNode, GrapheneAssetNotFoundError)
        name = "AssetNodeOrError"
